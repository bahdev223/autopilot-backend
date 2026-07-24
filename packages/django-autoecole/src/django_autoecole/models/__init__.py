from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import UUIDModel, TimeStampedModel
from ..constants import (
    StatutMoniteur, StatutVehicule, StatutDossier, DOSSIER_TRANSITIONS,
    StatutLecon, StatutExamen, ResultatExamen, StatutIndisponibilite,
    TypeBoite, TypeCarburant, TypeLecon, NiveauEvaluation, TypeExamen,
)
from ..exceptions import InvalidStatusTransitionError


class CategoriePermis(UUIDModel, TimeStampedModel):
    etablissement = models.ForeignKey(
        "django_formation.Etablissement", on_delete=models.PROTECT,
        related_name="categories_permis",
    )
    code = models.CharField(max_length=20)
    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    age_minimum = models.PositiveSmallIntegerField(null=True, blank=True)
    heures_theorie_minimum = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    heures_conduite_minimum = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    nombre_evaluations_minimum = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = "autoecole_categories_permis"
        verbose_name = _("Catégorie de permis")
        verbose_name_plural = _("Catégories de permis")
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["etablissement", "code"],
                name="autoecole_unique_categorie_permis_etablissement",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.nom}"


class Moniteur(UUIDModel, TimeStampedModel):
    etablissement = models.ForeignKey(
        "django_formation.Etablissement", on_delete=models.PROTECT,
        related_name="moniteurs_autoecole",
    )
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="profil_moniteur_autoecole",
    )
    matricule = models.CharField(max_length=50)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    numero_agrement = models.CharField(max_length=100, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    categories_permis = models.ManyToManyField(
        CategoriePermis, related_name="moniteurs", blank=True,
    )
    statut = models.CharField(
        max_length=25, choices=StatutMoniteur.choices,
        default=StatutMoniteur.ACTIF,
    )

    class Meta:
        db_table = "autoecole_moniteurs"
        verbose_name = _("Moniteur")
        verbose_name_plural = _("Moniteurs")
        ordering = ["nom", "prenom"]
        constraints = [
            models.UniqueConstraint(
                fields=["etablissement", "matricule"],
                name="autoecole_unique_moniteur_matricule_etablissement",
            ),
        ]

    def __str__(self):
        return f"{self.matricule} - {self.nom_complet}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip()

    @property
    def est_disponible(self):
        return self.statut == StatutMoniteur.ACTIF


class Vehicule(UUIDModel, TimeStampedModel):
    etablissement = models.ForeignKey(
        "django_formation.Etablissement", on_delete=models.PROTECT,
        related_name="vehicules_autoecole",
    )
    categorie_permis = models.ForeignKey(
        CategoriePermis, on_delete=models.PROTECT,
        related_name="vehicules",
    )
    immatriculation = models.CharField(max_length=50)
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100)
    annee = models.PositiveSmallIntegerField(null=True, blank=True)
    couleur = models.CharField(max_length=50, blank=True)
    type_boite = models.CharField(max_length=20, choices=TypeBoite.choices)
    type_carburant = models.CharField(max_length=30, choices=TypeCarburant.choices, blank=True)
    kilometrage_actuel = models.PositiveBigIntegerField(default=0)
    date_mise_en_service = models.DateField(null=True, blank=True)
    date_expiration_assurance = models.DateField(null=True, blank=True)
    date_expiration_visite_technique = models.DateField(null=True, blank=True)
    statut = models.CharField(
        max_length=25, choices=StatutVehicule.choices,
        default=StatutVehicule.DISPONIBLE,
    )
    observation = models.TextField(blank=True)

    class Meta:
        db_table = "autoecole_vehicules"
        verbose_name = _("Véhicule")
        verbose_name_plural = _("Véhicules")
        ordering = ["immatriculation"]
        constraints = [
            models.UniqueConstraint(
                fields=["etablissement", "immatriculation"],
                name="autoecole_unique_vehicule_immatriculation",
            ),
        ]

    def __str__(self):
        return f"{self.immatriculation} - {self.marque} {self.modele}"

    @property
    def est_disponible(self):
        return self.statut == StatutVehicule.DISPONIBLE

    @property
    def documents_en_ordre(self):
        from datetime import date
        if self.date_expiration_assurance and self.date_expiration_assurance < date.today():
            return False
        if self.date_expiration_visite_technique and self.date_expiration_visite_technique < date.today():
            return False
        return True


class DossierAutoEcole(UUIDModel, TimeStampedModel):
    etablissement = models.ForeignKey(
        "django_formation.Etablissement", on_delete=models.PROTECT,
        related_name="dossiers_autoecole",
    )
    inscription = models.OneToOneField(
        "django_formation.Inscription", on_delete=models.PROTECT,
        related_name="dossier_autoecole",
    )
    categorie_permis = models.ForeignKey(
        CategoriePermis, on_delete=models.PROTECT,
        related_name="dossiers",
    )
    moniteur_referent = models.ForeignKey(
        Moniteur, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="dossiers_referents",
    )
    numero_dossier = models.CharField(max_length=50)
    date_ouverture = models.DateField()
    date_expiration = models.DateField(null=True, blank=True)
    statut = models.CharField(
        max_length=30, choices=StatutDossier.choices,
        default=StatutDossier.BROUILLON,
    )
    heures_theorie_validees = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    heures_conduite_validees = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    pret_examen_le = models.DateTimeField(null=True, blank=True)
    cloture_le = models.DateTimeField(null=True, blank=True)
    observation = models.TextField(blank=True)

    class Meta:
        db_table = "autoecole_dossiers"
        verbose_name = _("Dossier auto-école")
        verbose_name_plural = _("Dossiers auto-école")
        ordering = ["-date_ouverture"]
        constraints = [
            models.UniqueConstraint(
                fields=["etablissement", "numero_dossier"],
                name="autoecole_unique_numero_dossier",
            ),
        ]

    def __str__(self):
        return f"{self.numero_dossier} - {self.inscription.apprenant}"

    @property
    def apprenant(self):
        return self.inscription.apprenant

    @property
    def heures_conduite_requises(self):
        return self.categorie_permis.heures_conduite_minimum

    @property
    def progression_conduite(self):
        if self.heures_conduite_requises > 0:
            return float(self.heures_conduite_validees / self.heures_conduite_requises * 100)
        return 0

    @property
    def peut_etre_presente_examen(self):
        if self.statut not in (StatutDossier.EN_FORMATION, StatutDossier.PRET_EXAMEN):
            return False
        heures_ok = self.heures_conduite_validees >= self.heures_conduite_requises
        theorie_ok = self.heures_theorie_validees >= self.categorie_permis.heures_theorie_minimum
        nb_eval = self.lecons.filter(evaluation__isnull=False, statut=StatutLecon.REALISEE).count()
        evals_ok = nb_eval >= self.categorie_permis.nombre_evaluations_minimum
        return heures_ok and theorie_ok and evals_ok

    def changer_statut(self, nouveau_statut):
        transitions = DOSSIER_TRANSITIONS.get(self.statut, [])
        if nouveau_statut not in transitions:
            raise InvalidStatusTransitionError(
                f"Transition {self.statut} → {nouveau_statut} non autorisée"
            )
        self.statut = nouveau_statut
        self.save(update_fields=["statut", "updated_at"])


class LeconConduite(UUIDModel, TimeStampedModel):
    etablissement = models.ForeignKey(
        "django_formation.Etablissement", on_delete=models.PROTECT,
        related_name="lecons_autoecole",
    )
    dossier = models.ForeignKey(
        DossierAutoEcole, on_delete=models.PROTECT, related_name="lecons",
    )
    moniteur = models.ForeignKey(
        Moniteur, on_delete=models.PROTECT, related_name="lecons",
    )
    vehicule = models.ForeignKey(
        Vehicule, null=True, blank=True,
        on_delete=models.PROTECT, related_name="lecons",
    )
    type_lecon = models.CharField(max_length=30, choices=TypeLecon.choices)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    duree_minutes = models.PositiveIntegerField()
    lieu_depart = models.CharField(max_length=255, blank=True)
    lieu_arrivee = models.CharField(max_length=255, blank=True)
    kilometrage_depart = models.PositiveBigIntegerField(null=True, blank=True)
    kilometrage_fin = models.PositiveBigIntegerField(null=True, blank=True)
    statut = models.CharField(
        max_length=30, choices=StatutLecon.choices, default=StatutLecon.PLANIFIEE,
    )
    motif_annulation = models.TextField(blank=True)
    observation = models.TextField(blank=True)
    realisee_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "autoecole_lecons"
        verbose_name = _("Leçon de conduite")
        verbose_name_plural = _("Leçons de conduite")
        ordering = ["-date_debut"]

    def __str__(self):
        return f"{self.get_type_lecon_display()} - {self.date_debut}"

    def changer_statut(self, nouveau_statut):
        from ..constants import LECON_TRANSITIONS
        transitions = LECON_TRANSITIONS.get(self.statut, [])
        if nouveau_statut not in transitions:
            raise InvalidStatusTransitionError(
                f"Leçon {self.statut} → {nouveau_statut} non autorisée"
            )
        self.statut = nouveau_statut
        self.save(update_fields=["statut", "updated_at"])


class EvaluationLecon(UUIDModel, TimeStampedModel):
    lecon = models.OneToOneField(
        LeconConduite, on_delete=models.CASCADE, related_name="evaluation",
    )
    moniteur = models.ForeignKey(
        Moniteur, on_delete=models.PROTECT, related_name="evaluations",
    )
    note_globale = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    niveau = models.CharField(max_length=25, choices=NiveauEvaluation.choices)
    competences_acquises = models.JSONField(default=list, blank=True)
    points_forts = models.TextField(blank=True)
    points_a_ameliorer = models.TextField(blank=True)
    commentaire = models.TextField(blank=True)
    recommande_examen = models.BooleanField(default=False)

    class Meta:
        db_table = "autoecole_evaluations"
        verbose_name = _("Évaluation de leçon")
        verbose_name_plural = _("Évaluations de leçon")

    def __str__(self):
        return f"Évaluation {self.lecon}"


class ExamenAutoEcole(UUIDModel, TimeStampedModel):
    etablissement = models.ForeignKey(
        "django_formation.Etablissement", on_delete=models.PROTECT,
        related_name="examens_autoecole",
    )
    dossier = models.ForeignKey(
        DossierAutoEcole, on_delete=models.PROTECT, related_name="examens",
    )
    type_examen = models.CharField(max_length=30, choices=TypeExamen.choices)
    date_examen = models.DateTimeField()
    centre_examen = models.CharField(max_length=255, blank=True)
    numero_convocation = models.CharField(max_length=100, blank=True)
    statut = models.CharField(
        max_length=30, choices=StatutExamen.choices, default=StatutExamen.BROUILLON,
    )
    resultat = models.CharField(
        max_length=25, choices=ResultatExamen.choices, default=ResultatExamen.EN_ATTENTE,
    )
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    observation = models.TextField(blank=True)
    resultat_enregistre_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "autoecole_examens"
        verbose_name = _("Examen auto-école")
        verbose_name_plural = _("Examens auto-école")
        ordering = ["-date_examen"]

    def __str__(self):
        return f"{self.get_type_examen_display()} - {self.dossier}"


class IndisponibiliteMoniteur(UUIDModel, TimeStampedModel):
    moniteur = models.ForeignKey(
        Moniteur, on_delete=models.CASCADE, related_name="indisponibilites",
    )
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    motif = models.CharField(max_length=255)
    commentaire = models.TextField(blank=True)
    statut = models.CharField(
        max_length=20, choices=StatutIndisponibilite.choices,
        default=StatutIndisponibilite.ACTIVE,
    )

    class Meta:
        db_table = "autoecole_indisponibilites_moniteurs"
        verbose_name = _("Indisponibilité moniteur")
        verbose_name_plural = _("Indisponibilités moniteurs")

    def __str__(self):
        return f"{self.moniteur} - {self.date_debut}"


class IndisponibiliteVehicule(UUIDModel, TimeStampedModel):
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name="indisponibilites",
    )
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    motif = models.CharField(max_length=255)
    commentaire = models.TextField(blank=True)
    statut = models.CharField(
        max_length=20, choices=StatutIndisponibilite.choices,
        default=StatutIndisponibilite.ACTIVE,
    )

    class Meta:
        db_table = "autoecole_indisponibilites_vehicules"
        verbose_name = _("Indisponibilité véhicule")
        verbose_name_plural = _("Indisponibilités véhicules")

    def __str__(self):
        return f"{self.vehicule} - {self.date_debut}"


class HistoriqueStatutDossier(UUIDModel, TimeStampedModel):
    dossier = models.ForeignKey(
        DossierAutoEcole, on_delete=models.CASCADE,
        related_name="historique_statuts",
    )
    ancien_statut = models.CharField(max_length=30, blank=True)
    nouveau_statut = models.CharField(max_length=30)
    commentaire = models.TextField(blank=True)
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )

    class Meta:
        db_table = "autoecole_historique_statuts_dossiers"
        verbose_name = _("Historique statut dossier")
        verbose_name_plural = _("Historiques statuts dossiers")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.dossier} : {self.ancien_statut} → {self.nouveau_statut}"
