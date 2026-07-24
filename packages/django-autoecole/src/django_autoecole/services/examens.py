from django.db import transaction
from django.utils import timezone
from django_autoecole.models import ExamenAutoEcole, DossierAutoEcole
from django_autoecole.constants import StatutExamen, ResultatExamen, StatutDossier
from django_autoecole.exceptions import (
    DossierNotExamReadyError, DuplicateActiveExamError, AutoEcoleDomainError,
)
from django_autoecole.services.dossiers import presenter_dossier_examen, marquer_dossier_reussi, marquer_dossier_echoue
from django_autoecole import signals


@transaction.atomic
def planifier_examen(*, dossier_id, type_examen, date_examen, centre_examen="",
                      numero_convocation="", observation="", cree_par=None):
    dossier = DossierAutoEcole.objects.select_for_update().select_related("etablissement", "categorie_permis").get(id=dossier_id)

    if dossier.statut not in (StatutDossier.EN_FORMATION, StatutDossier.PRET_EXAMEN):
        raise DossierNotExamReadyError("Le dossier doit être en formation ou prêt pour l'examen")

    if not dossier.peut_etre_presente_examen:
        raise DossierNotExamReadyError("Le dossier ne remplit pas les conditions pour l'examen")

    actif = dossier.examens.filter(
        statut__in=[StatutExamen.PLANIFIE, StatutExamen.CONFIRME],
        type_examen=type_examen,
    ).exists()
    if actif:
        raise DuplicateActiveExamError("Un examen actif de ce type existe déjà pour ce dossier")

    if date_examen <= timezone.now():
        raise AutoEcoleDomainError("La date d'examen doit être dans le futur")

    examen = ExamenAutoEcole.objects.create(
        etablissement=dossier.etablissement,
        dossier=dossier,
        type_examen=type_examen,
        date_examen=date_examen,
        centre_examen=centre_examen,
        numero_convocation=numero_convocation,
        statut=StatutExamen.PLANIFIE,
        observation=observation,
    )
    signals.emit_on_commit(signals.examen_planifie, planifier_examen, examen=examen, cree_par=cree_par)
    return examen


def _lock_examen(examen):
    ExamenAutoEcole.objects.filter(pk=examen.pk).select_for_update()
    examen.refresh_from_db()


@transaction.atomic
def confirmer_examen(examen):
    _lock_examen(examen)
    if examen.statut != StatutExamen.PLANIFIE:
        raise AutoEcoleDomainError("Seul un examen planifié peut être confirmé")
    examen.statut = StatutExamen.CONFIRME
    examen.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.examen_confirme, confirmer_examen, examen=examen)
    return examen


@transaction.atomic
def marquer_candidat_presente(examen):
    _lock_examen(examen)
    if examen.statut not in (StatutExamen.PLANIFIE, StatutExamen.CONFIRME):
        raise AutoEcoleDomainError("L'examen doit être planifié ou confirmé")
    examen.statut = StatutExamen.PRESENTE
    examen.save(update_fields=["statut", "updated_at"])
    if examen.dossier.statut == StatutDossier.PRET_EXAMEN:
        presenter_dossier_examen(examen.dossier)
    signals.emit_on_commit(signals.examen_presente, marquer_candidat_presente, examen=examen)
    return examen


@transaction.atomic
def marquer_candidat_absent(examen):
    _lock_examen(examen)
    if examen.statut not in (StatutExamen.PLANIFIE, StatutExamen.CONFIRME):
        raise AutoEcoleDomainError("L'examen doit être planifié ou confirmé")
    examen.statut = StatutExamen.ABSENT
    examen.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.candidat_absent_examen, marquer_candidat_absent, examen=examen)
    return examen


@transaction.atomic
def annuler_examen(examen):
    _lock_examen(examen)
    if examen.statut in (StatutExamen.RESULTAT_DISPONIBLE, StatutExamen.PRESENTE):
        raise AutoEcoleDomainError("Impossible d'annuler un examen déjà présenté ou avec résultat")
    examen.statut = StatutExamen.ANNULE
    examen.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.examen_annule, annuler_examen, examen=examen)
    return examen


@transaction.atomic
def enregistrer_resultat_examen(examen, resultat, score=None, observation=""):
    _lock_examen(examen)
    if examen.statut not in (StatutExamen.PRESENTE, StatutExamen.CONFIRME):
        raise AutoEcoleDomainError(
            "L'examen doit être présenté ou confirmé pour enregistrer un résultat"
        )

    examen.resultat = resultat
    examen.statut = StatutExamen.RESULTAT_DISPONIBLE
    if score is not None:
        examen.score = score
    if observation:
        examen.observation = observation
    examen.resultat_enregistre_le = timezone.now()
    examen.save(update_fields=["resultat", "statut", "score", "observation", "resultat_enregistre_le", "updated_at"])

    dossier = examen.dossier
    if resultat == ResultatExamen.ADMIS:
        marquer_dossier_reussi(dossier)
    elif resultat in (ResultatExamen.ECHOUE, ResultatExamen.AJOURNE):
        marquer_dossier_echoue(dossier)

    signals.emit_on_commit(
        signals.resultat_examen_enregistre,
        enregistrer_resultat_examen,
        examen=examen,
    )
    return examen
