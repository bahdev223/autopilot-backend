from django.db import models
from django.utils.translation import gettext_lazy as _


class StatutMoniteur(models.TextChoices):
    ACTIF = "ACTIF", _("Actif")
    INDISPONIBLE = "INDISPONIBLE", _("Indisponible")
    SUSPENDU = "SUSPENDU", _("Suspendu")
    INACTIF = "INACTIF", _("Inactif")
    ARCHIVE = "ARCHIVE", _("Archivé")


class StatutVehicule(models.TextChoices):
    DISPONIBLE = "DISPONIBLE", _("Disponible")
    RESERVE = "RESERVE", _("Réservé")
    EN_LECON = "EN_LECON", _("En leçon")
    ENTRETIEN = "ENTRETIEN", _("En entretien")
    PANNE = "PANNE", _("En panne")
    HORS_SERVICE = "HORS_SERVICE", _("Hors service")
    ARCHIVE = "ARCHIVE", _("Archivé")


class StatutDossier(models.TextChoices):
    BROUILLON = "BROUILLON", _("Brouillon")
    OUVERT = "OUVERT", _("Ouvert")
    EN_FORMATION = "EN_FORMATION", _("En formation")
    PRET_EXAMEN = "PRET_EXAMEN", _("Prêt pour l'examen")
    PRESENTE_EXAMEN = "PRESENTE_EXAMEN", _("Présenté à l'examen")
    REUSSI = "REUSSI", _("Réussi")
    ECHOUE = "ECHOUE", _("Échoué")
    SUSPENDU = "SUSPENDU", _("Suspendu")
    ANNULE = "ANNULE", _("Annulé")
    CLOTURE = "CLOTURE", _("Clôturé")


DOSSIER_TRANSITIONS = {
    StatutDossier.BROUILLON: [StatutDossier.OUVERT, StatutDossier.ANNULE],
    StatutDossier.OUVERT: [StatutDossier.EN_FORMATION, StatutDossier.SUSPENDU, StatutDossier.ANNULE],
    StatutDossier.EN_FORMATION: [StatutDossier.PRET_EXAMEN, StatutDossier.SUSPENDU, StatutDossier.ANNULE],
    StatutDossier.PRET_EXAMEN: [StatutDossier.PRESENTE_EXAMEN, StatutDossier.EN_FORMATION, StatutDossier.SUSPENDU, StatutDossier.ANNULE],
    StatutDossier.PRESENTE_EXAMEN: [StatutDossier.REUSSI, StatutDossier.ECHOUE],
    StatutDossier.REUSSI: [StatutDossier.CLOTURE],
    StatutDossier.ECHOUE: [StatutDossier.EN_FORMATION, StatutDossier.PRET_EXAMEN, StatutDossier.CLOTURE],
    StatutDossier.SUSPENDU: [StatutDossier.OUVERT, StatutDossier.EN_FORMATION, StatutDossier.ANNULE, StatutDossier.CLOTURE],
    StatutDossier.ANNULE: [StatutDossier.CLOTURE],
    StatutDossier.CLOTURE: [],
}


class StatutLecon(models.TextChoices):
    PLANIFIEE = "PLANIFIEE", _("Planifiée")
    CONFIRMEE = "CONFIRMEE", _("Confirmée")
    EN_COURS = "EN_COURS", _("En cours")
    REALISEE = "REALISEE", _("Réalisée")
    ANNULEE = "ANNULEE", _("Annulée")
    ABSENT_CANDIDAT = "ABSENT_CANDIDAT", _("Candidat absent")
    ABSENT_MONITEUR = "ABSENT_MONITEUR", _("Moniteur absent")
    REPORTEE = "REPORTEE", _("Reportée")


LECON_TRANSITIONS = {
    StatutLecon.PLANIFIEE: [StatutLecon.CONFIRMEE, StatutLecon.ANNULEE, StatutLecon.REPORTEE],
    StatutLecon.CONFIRMEE: [StatutLecon.EN_COURS, StatutLecon.ANNULEE, StatutLecon.ABSENT_CANDIDAT, StatutLecon.ABSENT_MONITEUR, StatutLecon.REPORTEE],
    StatutLecon.EN_COURS: [StatutLecon.REALISEE, StatutLecon.ANNULEE],
    StatutLecon.REALISEE: [],
    StatutLecon.ANNULEE: [],
    StatutLecon.ABSENT_CANDIDAT: [],
    StatutLecon.ABSENT_MONITEUR: [],
    StatutLecon.REPORTEE: [StatutLecon.PLANIFIEE, StatutLecon.ANNULEE],
}


class StatutExamen(models.TextChoices):
    BROUILLON = "BROUILLON", _("Brouillon")
    PLANIFIE = "PLANIFIE", _("Planifié")
    CONFIRME = "CONFIRME", _("Confirmé")
    PRESENTE = "PRESENTE", _("Présenté")
    ABSENT = "ABSENT", _("Absent")
    ANNULE = "ANNULE", _("Annulé")
    RESULTAT_DISPONIBLE = "RESULTAT_DISPONIBLE", _("Résultat disponible")


class ResultatExamen(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", _("En attente")
    ADMIS = "ADMIS", _("Admis")
    AJOURNE = "AJOURNE", _("Ajourné")
    ECHOUE = "ECHOUE", _("Échoué")


class StatutIndisponibilite(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    ANNULEE = "ANNULEE", _("Annulée")


class TypeBoite(models.TextChoices):
    MANUELLE = "MANUELLE", _("Manuelle")
    AUTOMATIQUE = "AUTOMATIQUE", _("Automatique")


class TypeCarburant(models.TextChoices):
    ESSENCE = "ESSENCE", _("Essence")
    DIESEL = "DIESEL", _("Diesel")
    ELECTRIQUE = "ELECTRIQUE", _("Électrique")
    HYBRIDE = "HYBRIDE", _("Hybride")
    AUTRE = "AUTRE", _("Autre")


class TypeLecon(models.TextChoices):
    THEORIE = "THEORIE", _("Théorie")
    SIMULATEUR = "SIMULATEUR", _("Simulateur")
    CONDUITE = "CONDUITE", _("Conduite")
    MANOEUVRE = "MANOEUVRE", _("Manœuvre")
    CIRCULATION = "CIRCULATION", _("Circulation")
    REVISION = "REVISION", _("Révision")


class NiveauEvaluation(models.TextChoices):
    INSUFFISANT = "INSUFFISANT", _("Insuffisant")
    DEBUTANT = "DEBUTANT", _("Débutant")
    EN_PROGRESSION = "EN_PROGRESSION", _("En progression")
    ACQUIS = "ACQUIS", _("Acquis")
    MAITRISE = "MAITRISE", _("Maîtrisé")


class TypeExamen(models.TextChoices):
    CODE_INTERNE = "CODE_INTERNE", _("Code interne")
    CODE_OFFICIEL = "CODE_OFFICIEL", _("Code officiel")
    CONDUITE_INTERNE = "CONDUITE_INTERNE", _("Conduite interne")
    CONDUITE_OFFICIELLE = "CONDUITE_OFFICIELLE", _("Conduite officielle")


class RoleAutoEcole(models.TextChoices):
    DIRECTEUR = "DIRECTEUR_AUTOECOLE", _("Directeur d'auto-école")
    RESPONSABLE_PEDAGOGIQUE = "RESPONSABLE_PEDAGOGIQUE", _("Responsable pédagogique")
    AGENT_PLANNING = "AGENT_PLANNING", _("Agent planning")
    MONITEUR = "MONITEUR", _("Moniteur")
    AGENT_EXAMEN = "AGENT_EXAMEN", _("Agent examen")
    GESTIONNAIRE_VEHICULES = "GESTIONNAIRE_VEHICULES", _("Gestionnaire des véhicules")
    LECTEUR = "LECTEUR", _("Lecteur")


# Configuration par defaut
DEFAULT_CONFIG = {
    "DEFAULT_TIMEZONE": "Africa/Bamako",
    "DEFAULT_CURRENCY": "XOF",
    "DEFAULT_LESSON_DURATION_MINUTES": 60,
    "MAX_EVALUATION_SCORE": 20,
    "CHECK_VEHICLE_DOCUMENT_EXPIRY": True,
    "ALLOW_EXAM_WITHOUT_MINIMUM_HOURS": False,
    "DOSSIER_NUMBER_PREFIX": "AE",
    "INSTRUCTOR_NUMBER_PREFIX": "MON",
}


def get_config():
    from django.conf import settings
    user_config = getattr(settings, "DJANGO_AUTOECOLE", {})
    merged = DEFAULT_CONFIG.copy()
    merged.update(user_config)
    return merged
