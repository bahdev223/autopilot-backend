from django.db import models
from django.utils.translation import gettext_lazy as _

from django_formation.models.base import UUIDModel, TimeStampedModel


class Formation(UUIDModel, TimeStampedModel):
    class Statut(models.TextChoices):
        BROUILLON = "BROUILLON", _("Brouillon")
        PUBLIEE = "PUBLIEE", _("Publiée")
        SUSPENDUE = "SUSPENDUE", _("Suspendue")
        ARCHIVEE = "ARCHIVEE", _("Archivée")

    etablissement = models.ForeignKey(
        "Etablissement", on_delete=models.PROTECT, related_name="formations",
        verbose_name=_("Établissement"),
    )
    code = models.CharField(max_length=50, verbose_name=_("Code"))
    nom = models.CharField(max_length=255, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    objectifs = models.TextField(blank=True, verbose_name=_("Objectifs"))
    duree_heures = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Durée (heures)"))
    duree_jours = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Durée (jours)"))
    tarif_indicatif = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        verbose_name=_("Tarif indicatif"),
    )
    devise = models.CharField(max_length=3, default="XOF", verbose_name=_("Devise"))
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.BROUILLON, verbose_name=_("Statut"),
    )

    class Meta:
        verbose_name = _("Formation")
        verbose_name_plural = _("Formations")
        constraints = [
            models.UniqueConstraint(
                fields=["etablissement", "code"],
                name="formation_unique_code_formation_etablissement",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.nom}"
