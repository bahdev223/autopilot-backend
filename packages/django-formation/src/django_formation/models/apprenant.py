from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_formation.models.base import UUIDModel, TimeStampedModel


class Apprenant(UUIDModel, TimeStampedModel):
    class Sexe(models.TextChoices):
        MASCULIN = "M", _("Masculin")
        FEMININ = "F", _("Féminin")

    class Statut(models.TextChoices):
        ACTIF = "ACTIF", _("Actif")
        INACTIF = "INACTIF", _("Inactif")
        ARCHIVE = "ARCHIVE", _("Archivé")

    etablissement = models.ForeignKey(
        "Etablissement", on_delete=models.PROTECT, related_name="apprenants",
        verbose_name=_("Établissement"),
    )
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="profil_apprenant_formation", verbose_name=_("Utilisateur"),
    )
    matricule = models.CharField(max_length=50, verbose_name=_("Matricule"))
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    prenom = models.CharField(max_length=100, verbose_name=_("Prénom"))
    sexe = models.CharField(max_length=20, blank=True, choices=Sexe.choices, verbose_name=_("Sexe"))
    date_naissance = models.DateField(null=True, blank=True, verbose_name=_("Date de naissance"))
    lieu_naissance = models.CharField(max_length=150, blank=True, verbose_name=_("Lieu de naissance"))
    telephone = models.CharField(max_length=30, blank=True, verbose_name=_("Téléphone"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    adresse = models.TextField(blank=True, verbose_name=_("Adresse"))
    contact_urgence_nom = models.CharField(max_length=200, blank=True, verbose_name=_("Contact urgence - Nom"))
    contact_urgence_telephone = models.CharField(max_length=30, blank=True, verbose_name=_("Contact urgence - Téléphone"))
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.ACTIF, verbose_name=_("Statut"),
    )

    class Meta:
        verbose_name = _("Apprenant")
        verbose_name_plural = _("Apprenants")
        constraints = [
            models.UniqueConstraint(
                fields=["etablissement", "matricule"],
                name="formation_unique_matricule_etablissement",
            ),
        ]

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.matricule})"

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}".strip()
