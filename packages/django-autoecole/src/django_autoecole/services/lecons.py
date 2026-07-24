from django.db import transaction
from django.utils import timezone
from django_autoecole.models import LeconConduite, Moniteur, Vehicule, DossierAutoEcole, EvaluationLecon
from django_autoecole.constants import (
    StatutLecon, StatutDossier, StatutMoniteur, StatutVehicule, TypeLecon,
)
from django_autoecole.exceptions import (
    InstructorNotAuthorizedError, InstructorUnavailableError,
    VehicleUnavailableError, VehicleCategoryMismatchError,
    LessonTimeConflictError,
    InvalidMileageError, MissingCancellationReasonError,
    InvalidStatusTransitionError, AutoEcoleDomainError,
    InvalidLessonDurationError,
)
from django_autoecole.selectors import verifier_disponibilites
from django_autoecole.constants import get_config
from django_autoecole import signals
from django_autoecole.exceptions import VehicleDocumentsExpiredError


@transaction.atomic
def planifier_lecon(*, dossier_id, moniteur_id, vehicule_id=None,
                     type_lecon, date_debut, date_fin,
                     lieu_depart="", lieu_arrivee="", cree_par=None):
    dossier = DossierAutoEcole.objects.select_for_update().select_related(
        "etablissement", "categorie_permis"
    ).get(id=dossier_id)

    if dossier.statut not in (StatutDossier.OUVERT, StatutDossier.EN_FORMATION, StatutDossier.PRET_EXAMEN):
        raise AutoEcoleDomainError("Le dossier n'est pas en état de recevoir une leçon")

    moniteur = Moniteur.objects.select_for_update().select_related("etablissement").get(id=moniteur_id)
    if moniteur.statut != StatutMoniteur.ACTIF:
        raise InstructorUnavailableError("Le moniteur n'est pas actif")
    if moniteur.etablissement_id != dossier.etablissement_id:
        raise AutoEcoleDomainError("Le moniteur n'appartient pas au même établissement")
    if dossier.categorie_permis not in moniteur.categories_permis.all():
        raise InstructorNotAuthorizedError(
            "Le moniteur n'est pas habilité pour cette catégorie de permis"
        )

    if date_fin <= date_debut:
        raise InvalidLessonDurationError("La date de fin doit être postérieure à la date de début")

    duree = int((date_fin - date_debut).total_seconds() / 60)
    if duree <= 0:
        raise InvalidLessonDurationError("La durée de la leçon doit être positive")

    lecon_pratique = type_lecon in (TypeLecon.CONDUITE, TypeLecon.MANOEUVRE, TypeLecon.CIRCULATION)

    if lecon_pratique and not vehicule_id:
        raise AutoEcoleDomainError("Un véhicule est obligatoire pour une leçon pratique")

    vehicule = None
    if vehicule_id:
        vehicule = Vehicule.objects.select_for_update().select_related("categorie_permis").get(id=vehicule_id)
        if vehicule.etablissement_id != dossier.etablissement_id:
            raise AutoEcoleDomainError("Le véhicule n'appartient pas au même établissement")
        if vehicule.statut not in (StatutVehicule.DISPONIBLE, StatutVehicule.RESERVE):
            raise VehicleUnavailableError("Le véhicule n'est pas disponible")
        if vehicule.categorie_permis != dossier.categorie_permis:
            raise VehicleCategoryMismatchError(
                f"Le véhicule est pour {vehicule.categorie_permis.code}, "
                f"le dossier est pour {dossier.categorie_permis.code}"
            )
        if get_config()["CHECK_VEHICLE_DOCUMENT_EXPIRY"] and not vehicule.documents_en_ordre:
            raise VehicleDocumentsExpiredError("Les documents du véhicule sont expirés")

    _verifier_conflits(moniteur, vehicule, date_debut, date_fin)

    lecon = LeconConduite.objects.create(
        etablissement=dossier.etablissement,
        dossier=dossier,
        moniteur=moniteur,
        vehicule=vehicule,
        type_lecon=type_lecon,
        date_debut=date_debut,
        date_fin=date_fin,
        duree_minutes=duree,
        lieu_depart=lieu_depart,
        lieu_arrivee=lieu_arrivee,
        statut=StatutLecon.PLANIFIEE,
    )
    signals.emit_on_commit(signals.lecon_planifiee, planifier_lecon, lecon=lecon, cree_par=cree_par)
    return lecon


@transaction.atomic
def confirmer_lecon(lecon):
    lecon.changer_statut(StatutLecon.CONFIRMEE)
    signals.emit_on_commit(signals.lecon_confirmee, confirmer_lecon, lecon=lecon)
    return lecon


@transaction.atomic
def demarrer_lecon(lecon, kilometrage_depart=None):
    lecon.changer_statut(StatutLecon.EN_COURS)
    if kilometrage_depart is not None:
        lecon.kilometrage_depart = kilometrage_depart
        lecon.save(update_fields=["kilometrage_depart", "updated_at"])
    signals.emit_on_commit(signals.lecon_demarre, demarrer_lecon, lecon=lecon)
    return lecon


@transaction.atomic
def terminer_lecon(lecon, kilometrage_fin=None, observation=""):
    if lecon.statut not in (StatutLecon.CONFIRMEE, StatutLecon.EN_COURS):
        raise InvalidStatusTransitionError(
            f"Impossible de terminer une leçon au statut {lecon.statut}"
        )
    if kilometrage_fin is not None and lecon.kilometrage_depart is not None:
        if kilometrage_fin < lecon.kilometrage_depart:
            raise InvalidMileageError("Le kilométrage final ne peut pas être inférieur au kilométrage de départ")
    now = timezone.now()
    lecon.statut = StatutLecon.REALISEE
    if kilometrage_fin is not None:
        lecon.kilometrage_fin = kilometrage_fin
    if observation:
        lecon.observation = observation
    lecon.realisee_le = now
    lecon.save(update_fields=["statut", "kilometrage_fin", "observation", "realisee_le", "updated_at"])

    _recalculer_heures_dossier(lecon.dossier)
    signals.emit_on_commit(signals.lecon_realisee, terminer_lecon, lecon=lecon)
    return lecon


@transaction.atomic
def annuler_lecon(lecon, motif="", observation=""):
    if not motif:
        raise MissingCancellationReasonError("Le motif d'annulation est obligatoire")
    lecon.changer_statut(StatutLecon.ANNULEE)
    lecon.motif_annulation = motif
    if observation:
        lecon.observation = observation
    lecon.save(update_fields=["motif_annulation", "observation", "updated_at"])
    signals.emit_on_commit(signals.lecon_annulee, annuler_lecon, lecon=lecon)
    return lecon


@transaction.atomic
def reporter_lecon(lecon, nouvelle_date_debut, nouvelle_date_fin):
    lecon.changer_statut(StatutLecon.REPORTEE)
    nouvelle = LeconConduite.objects.create(
        etablissement=lecon.etablissement,
        dossier=lecon.dossier,
        moniteur=lecon.moniteur,
        vehicule=lecon.vehicule,
        type_lecon=lecon.type_lecon,
        date_debut=nouvelle_date_debut,
        date_fin=nouvelle_date_fin,
        duree_minutes=int((nouvelle_date_fin - nouvelle_date_debut).total_seconds() / 60),
        lieu_depart=lecon.lieu_depart,
        lieu_arrivee=lecon.lieu_arrivee,
        statut=StatutLecon.PLANIFIEE,
        observation=f"Report de la leçon #{lecon.id}",
    )
    signals.emit_on_commit(
        signals.lecon_reportee,
        reporter_lecon,
        lecon=lecon,
        nouvelle_lecon=nouvelle,
    )
    return nouvelle


@transaction.atomic
def marquer_absence_candidat(lecon, observation=""):
    lecon.changer_statut(StatutLecon.ABSENT_CANDIDAT)
    if observation:
        lecon.observation = observation
    lecon.save(update_fields=["observation", "updated_at"])
    signals.emit_on_commit(signals.candidat_absent, marquer_absence_candidat, lecon=lecon)
    return lecon


@transaction.atomic
def marquer_absence_moniteur(lecon, observation=""):
    lecon.changer_statut(StatutLecon.ABSENT_MONITEUR)
    if observation:
        lecon.observation = observation
    lecon.save(update_fields=["observation", "updated_at"])
    signals.emit_on_commit(signals.moniteur_absent, marquer_absence_moniteur, lecon=lecon)
    return lecon


def _verifier_conflits(moniteur, vehicule, date_debut, date_fin):
    periode_bloquante = [StatutLecon.PLANIFIEE, StatutLecon.CONFIRMEE, StatutLecon.EN_COURS]
    conflits = verifier_disponibilites(
        moniteur_id=moniteur.id,
        vehicule_id=vehicule.id if vehicule else None,
        date_debut=date_debut,
        date_fin=date_fin,
        statuts_bloquants=periode_bloquante,
    )
    if conflits["moniteur"]:
        raise LessonTimeConflictError("Le moniteur a déjà une leçon ou une indisponibilité sur ce créneau")
    if conflits.get("vehicule"):
        raise LessonTimeConflictError("Le véhicule est déjà réservé sur ce créneau")


@transaction.atomic
def evaluer_lecon(*, lecon, moniteur, note_globale=None, niveau="",
                   competences_acquises=None, points_forts="",
                   points_a_ameliorer="", commentaire="",
                   recommande_examen=False):
    LeconConduite.objects.filter(pk=lecon.pk).select_for_update()
    lecon.refresh_from_db()
    evaluation = EvaluationLecon.objects.create(
        lecon=lecon,
        moniteur=moniteur,
        note_globale=note_globale,
        niveau=niveau,
        competences_acquises=competences_acquises or [],
        points_forts=points_forts,
        points_a_ameliorer=points_a_ameliorer,
        commentaire=commentaire,
        recommande_examen=recommande_examen,
    )
    signals.emit_on_commit(signals.evaluation_lecon_creee, evaluer_lecon, evaluation=evaluation, lecon=lecon)
    return evaluation


def _recalculer_heures_dossier(dossier):
    from django.db.models import Sum
    lecons = dossier.lecons.filter(statut=StatutLecon.REALISEE)

    types_theorie = [TypeLecon.THEORIE, TypeLecon.SIMULATEUR]
    types_conduite = [TypeLecon.CONDUITE, TypeLecon.MANOEUVRE, TypeLecon.CIRCULATION, TypeLecon.REVISION]

    theorie = lecons.filter(type_lecon__in=types_theorie).aggregate(
        total=Sum("duree_minutes")
    )["total"] or 0
    pratique = lecons.filter(type_lecon__in=types_conduite).aggregate(
        total=Sum("duree_minutes")
    )["total"] or 0

    dossier.heures_theorie_validees = theorie / 60
    dossier.heures_conduite_validees = pratique / 60
    dossier.save(update_fields=["heures_theorie_validees", "heures_conduite_validees", "updated_at"])
