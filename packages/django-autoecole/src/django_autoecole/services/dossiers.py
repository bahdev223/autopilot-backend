from django.db import transaction
from django.utils import timezone
from django_autoecole.exceptions import (
    InactivePermitCategoryError, InvalidEnrollmentStatusError,
    CrossEstablishmentOperationError, DuplicateDrivingSchoolFileError,
    InsufficientTrainingHoursError,
)
from django_autoecole.models import DossierAutoEcole, CategoriePermis, HistoriqueStatutDossier
from django_autoecole.constants import StatutDossier, get_config
from django_autoecole import signals


@transaction.atomic
def creer_dossier_autoecole(*, inscription, categorie_permis_id, numero_dossier=None,
                             moniteur_referent=None, date_ouverture=None, cree_par=None):
    etablissement = inscription.session.etablissement
    categorie = CategoriePermis.objects.get(id=categorie_permis_id)

    if not categorie.actif:
        raise InactivePermitCategoryError("La catégorie de permis est inactive")

    if categorie.etablissement_id != etablissement.id:
        raise CrossEstablishmentOperationError(
            "La catégorie de permis n'appartient pas au même établissement"
        )

    if inscription.statut not in ("CONFIRMEE", "EN_COURS"):
        raise InvalidEnrollmentStatusError(
            "L'inscription doit être confirmée ou en cours"
        )

    if hasattr(inscription, "dossier_autoecole"):
        raise DuplicateDrivingSchoolFileError(
            "Cette inscription possède déjà un dossier auto-école"
        )

    if moniteur_referent:
        _valider_moniteur_etablissement(moniteur_referent, etablissement, categorie)

    config = get_config()
    if not numero_dossier:
        count = DossierAutoEcole.objects.filter(etablissement=etablissement).count()
        prefix = config["DOSSIER_NUMBER_PREFIX"]
        year = timezone.now().year
        numero_dossier = f"{prefix}-{year}-{count + 1:06d}"

    dossier = DossierAutoEcole.objects.create(
        etablissement=etablissement,
        inscription=inscription,
        categorie_permis=categorie,
        moniteur_referent=moniteur_referent,
        numero_dossier=numero_dossier,
        date_ouverture=date_ouverture or timezone.localdate(),
        statut=StatutDossier.BROUILLON,
    )
    signals.emit_on_commit(
        signals.dossier_autoecole_cree,
        creer_dossier_autoecole,
        dossier=dossier,
        cree_par=cree_par,
    )
    return dossier


def _lock_dossier(dossier):
    DossierAutoEcole.objects.filter(pk=dossier.pk).select_for_update()
    dossier.refresh_from_db()


@transaction.atomic
def ouvrir_dossier(dossier, modifie_par=None):
    _lock_dossier(dossier)
    dossier.changer_statut(StatutDossier.OUVERT)
    _historiser(dossier, StatutDossier.BROUILLON, StatutDossier.OUVERT, modifie_par)
    return dossier


@transaction.atomic
def demarrer_formation_dossier(dossier, modifie_par=None):
    _lock_dossier(dossier)
    dossier.changer_statut(StatutDossier.EN_FORMATION)
    _historiser(dossier, StatutDossier.OUVERT, StatutDossier.EN_FORMATION, modifie_par)
    return dossier


@transaction.atomic
def suspendre_dossier(dossier, modifie_par=None, commentaire=""):
    _lock_dossier(dossier)
    ancien = dossier.statut
    dossier.changer_statut(StatutDossier.SUSPENDU)
    _historiser(dossier, ancien, StatutDossier.SUSPENDU, modifie_par, commentaire)
    return dossier


@transaction.atomic
def reprendre_dossier(dossier, modifie_par=None):
    _lock_dossier(dossier)
    ancien = dossier.statut
    dossier.changer_statut(StatutDossier.OUVERT)
    _historiser(dossier, ancien, StatutDossier.OUVERT, modifie_par)
    return dossier


@transaction.atomic
def declarer_dossier_pret_examen(dossier, modifie_par=None):
    _lock_dossier(dossier)
    if dossier.heures_conduite_validees < dossier.categorie_permis.heures_conduite_minimum:
        raise InsufficientTrainingHoursError(
            f"Minimum {dossier.categorie_permis.heures_conduite_minimum}h requis, "
            f"actuellement {dossier.heures_conduite_validees}h"
        )
    if dossier.heures_theorie_validees < dossier.categorie_permis.heures_theorie_minimum:
        raise InsufficientTrainingHoursError(
            f"Minimum {dossier.categorie_permis.heures_theorie_minimum}h de théorie requis"
        )
    nb_evals = dossier.lecons.filter(evaluation__isnull=False, statut="REALISEE").count()
    if nb_evals < dossier.categorie_permis.nombre_evaluations_minimum:
        raise InsufficientTrainingHoursError(
            f"Minimum {dossier.categorie_permis.nombre_evaluations_minimum} évaluations requises"
        )
    dossier.changer_statut(StatutDossier.PRET_EXAMEN)
    dossier.pret_examen_le = timezone.now()
    dossier.save(update_fields=["statut", "pret_examen_le", "updated_at"])
    _historiser(dossier, StatutDossier.EN_FORMATION, StatutDossier.PRET_EXAMEN, modifie_par)
    return dossier


@transaction.atomic
def presenter_dossier_examen(dossier, modifie_par=None):
    _lock_dossier(dossier)
    dossier.changer_statut(StatutDossier.PRESENTE_EXAMEN)
    dossier.save(update_fields=["statut", "updated_at"])
    _historiser(dossier, StatutDossier.PRET_EXAMEN, StatutDossier.PRESENTE_EXAMEN, modifie_par)
    return dossier


@transaction.atomic
def annuler_dossier(dossier, modifie_par=None, commentaire=""):
    _lock_dossier(dossier)
    ancien = dossier.statut
    dossier.changer_statut(StatutDossier.ANNULE)
    _historiser(dossier, ancien, StatutDossier.ANNULE, modifie_par, commentaire)
    return dossier


@transaction.atomic
def cloturer_dossier(dossier, modifie_par=None):
    _lock_dossier(dossier)
    ancien = dossier.statut
    dossier.changer_statut(StatutDossier.CLOTURE)
    dossier.cloture_le = timezone.now()
    dossier.save(update_fields=["statut", "cloture_le", "updated_at"])
    _historiser(dossier, ancien, StatutDossier.CLOTURE, modifie_par)
    return dossier


@transaction.atomic
def marquer_dossier_reussi(dossier, modifie_par=None):
    _lock_dossier(dossier)
    dossier.changer_statut(StatutDossier.REUSSI)
    _historiser(dossier, StatutDossier.PRESENTE_EXAMEN, StatutDossier.REUSSI, modifie_par)
    return dossier


@transaction.atomic
def marquer_dossier_echoue(dossier, modifie_par=None):
    _lock_dossier(dossier)
    dossier.changer_statut(StatutDossier.ECHOUE)
    _historiser(dossier, StatutDossier.PRESENTE_EXAMEN, StatutDossier.ECHOUE, modifie_par)
    return dossier


@transaction.atomic
def affecter_moniteur_referent(dossier, moniteur, modifie_par=None):
    _lock_dossier(dossier)
    _valider_moniteur_etablissement(moniteur, dossier.etablissement, dossier.categorie_permis)
    dossier.moniteur_referent = moniteur
    dossier.save(update_fields=["moniteur_referent", "updated_at"])
    signals.emit_on_commit(signals.moniteur_referent_affecte, affecter_moniteur_referent, dossier=dossier, moniteur=moniteur, modifie_par=modifie_par)
    return dossier


def _valider_moniteur_etablissement(moniteur, etablissement, categorie):
    if moniteur.etablissement_id != etablissement.id:
        raise CrossEstablishmentOperationError("Le moniteur n'appartient pas à cet établissement")
    if categorie not in moniteur.categories_permis.all():
        from django_autoecole.exceptions import InstructorNotAuthorizedError
        raise InstructorNotAuthorizedError(
            f"Le moniteur n'est pas habilité pour la catégorie {categorie.code}"
        )


def _historiser(dossier, ancien, nouveau, user=None, commentaire=""):
    HistoriqueStatutDossier.objects.create(
        dossier=dossier,
        ancien_statut=ancien,
        nouveau_statut=nouveau,
        commentaire=commentaire,
        modifie_par=user,
    )
    event_by_status = {
        StatutDossier.OUVERT: signals.dossier_ouvert,
        StatutDossier.EN_FORMATION: signals.dossier_en_formation,
        StatutDossier.PRET_EXAMEN: signals.dossier_pret_examen,
        StatutDossier.SUSPENDU: signals.dossier_suspendu,
        StatutDossier.ANNULE: signals.dossier_annule,
        StatutDossier.REUSSI: signals.dossier_reussi,
        StatutDossier.ECHOUE: signals.dossier_echoue,
        StatutDossier.CLOTURE: signals.dossier_cloture,
    }
    event = event_by_status.get(nouveau)
    if event:
        signals.emit_on_commit(event, _historiser, dossier=dossier, modifie_par=user)
