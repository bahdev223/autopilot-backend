from django.db.models.signals import post_migrate
from django.dispatch import Signal, receiver
from django.db import transaction
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


categorie_permis_creee = Signal()
categorie_permis_activee = Signal()
categorie_permis_desactivee = Signal()
moniteur_cree = Signal()
moniteur_modifie = Signal()
moniteur_active = Signal()
moniteur_indisponible = Signal()
moniteur_suspendu = Signal()
moniteur_reactive = Signal()
moniteur_archive = Signal()
habilitation_permis_ajoutee = Signal()
habilitation_permis_retiree = Signal()
vehicule_cree = Signal()
vehicule_modifie = Signal()
vehicule_reserve = Signal()
vehicule_liberer = Signal()
vehicule_en_panne = Signal()
vehicule_en_entretien = Signal()
vehicule_disponible = Signal()
vehicule_hors_service = Signal()
vehicule_archive = Signal()
vehicule_kilometrage_mis_a_jour = Signal()
dossier_autoecole_cree = Signal()
dossier_ouvert = Signal()
dossier_en_formation = Signal()
dossier_pret_examen = Signal()
dossier_suspendu = Signal()
dossier_annule = Signal()
dossier_reussi = Signal()
dossier_echoue = Signal()
dossier_cloture = Signal()
moniteur_referent_affecte = Signal()
lecon_planifiee = Signal()
lecon_confirmee = Signal()
lecon_demarre = Signal()
lecon_realisee = Signal()
lecon_annulee = Signal()
lecon_reportee = Signal()
candidat_absent = Signal()
moniteur_absent = Signal()
evaluation_lecon_creee = Signal()
examen_planifie = Signal()
examen_confirme = Signal()
examen_presente = Signal()
examen_annule = Signal()
candidat_absent_examen = Signal()
resultat_examen_enregistre = Signal()
indisponibilite_moniteur_annulee = Signal()
indisponibilite_vehicule_annulee = Signal()


def emit_on_commit(signal, sender, **kwargs):
    transaction.on_commit(lambda: signal.send(sender=sender, **kwargs))


PERMISSIONS = {
    # Dossiers
    "open_dossier": "Peut ouvrir un dossier",
    "suspend_dossier": "Peut suspendre un dossier",
    "resume_dossier": "Peut reprendre un dossier",
    "mark_dossier_exam_ready": "Peut déclarer un dossier prêt pour l'examen",
    "cancel_dossier": "Peut annuler un dossier",
    "close_dossier": "Peut clôturer un dossier",
    # Leçons
    "confirm_lecon": "Peut confirmer une leçon",
    "start_lecon": "Peut démarrer une leçon",
    "complete_lecon": "Peut terminer une leçon",
    "cancel_lecon": "Peut annuler une leçon",
    "postpone_lecon": "Peut reporter une leçon",
    "mark_candidate_absent": "Peut marquer l'absence du candidat",
    "mark_instructor_absent": "Peut marquer l'absence du moniteur",
    # Véhicules
    "reserve_vehicule": "Peut réserver un véhicule",
    "mark_vehicle_maintenance": "Peut mettre en entretien",
    "mark_vehicle_broken": "Peut déclarer en panne",
    "restore_vehicle": "Peut rendre disponible",
    # Examens
    "confirm_examen": "Peut confirmer un examen",
    "mark_exam_attended": "Peut marquer présenté",
    "mark_exam_absent": "Peut marquer absent",
    "record_exam_result": "Peut enregistrer un résultat",
}


@receiver(post_migrate)
def creer_permissions_autoecole(sender, **kwargs):
    app_config = kwargs.get("app_config")
    if app_config and app_config.label != "django_autoecole":
        return
    ct, _ = ContentType.objects.get_or_create(
        app_label="django_autoecole",
        model="dossierautoecole",
    )
    for codename, name in PERMISSIONS.items():
        Permission.objects.get_or_create(
            codename=f"autoecole_{codename}",
            content_type=ct,
            defaults={"name": name},
        )
