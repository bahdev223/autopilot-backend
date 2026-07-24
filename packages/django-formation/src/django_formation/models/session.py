from django.db import models
from django.utils.translation import gettext_lazy as _

from django_formation.models.base import UUIDModel, TimeStampedModel


class SessionFormation(UUIDModel, TimeStampedModel):
    class Statut(models.TextChoices):
        BROUILLON = "BROUILLON", _("Brouillon")
        INSCRIPTIONS_OUVERTES = "INSCRIPTIONS_OUVERTES", _("Inscriptions ouvertes")
        INSCRIPTIONS_FERMEES = "INSCRIPTIONS_FERMEES", _("Inscriptions fermées")
        EN_COURS = "EN_COURS", _("En cours")
        TERMINEE = "TERMINEE", _("Terminée")
        ANNULEE = "ANNULEE", _("Annulée")

    etablissement = models.ForeignKey(
        "Etablissement", on_delete=models.PROTECT, related_name="sessions_formation",
        verbose_name=_("Établissement"),
    )
    formation = models.ForeignKey(
        "Formation", on_delete=models.PROTECT, related_name="sessions",
        verbose_name=_("Formation"),
    )
    code = models.CharField(max_length=50, verbose_name=_("Code"))
    nom = models.CharField(max_length=255, verbose_name=_("Nom"))
    date_debut = models.DateField(verbose_name=_("Date de début"))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_("Date de fin"))
    date_ouverture_inscriptions = models.DateField(null=True, blank=True, verbose_name=_("Date d'ouverture des inscriptions"))
    date_fermeture_inscriptions = models.DateField(null=True, blank=True, verbose_name=_("Date de fermeture des inscriptions"))
    capacite = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Capacité"))
    tarif = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        verbose_name=_("Tarif"),
    )
    devise = models.CharField(max_length=3, default="XOF", verbose_name=_("Devise"))
    statut = models.CharField(
        max_length=25, choices=Statut.choices, default=Statut.BROUILLON, verbose_name=_("Statut"),
    )

    class Meta:
        verbose_name = _("Session de formation")
        verbose_name_plural = _("Sessions de formation")
        constraints = [
            models.UniqueConstraint(
                fields=["etablissement", "code"],
                name="formation_unique_code_session_etablissement",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.nom}"

    @property
    def nombre_inscrits_actifs(self) -> int:
        from django_formation.models.inscription import Inscription
        return self.inscriptions.filter(
            statut__in=[
                Inscription.Statut.PREINSCRITE,
                Inscription.Statut.EN_ATTENTE,
                Inscription.Statut.CONFIRMEE,
                Inscription.Statut.EN_COURS,
            ],
        ).count()

    @property
    def nombre_places_restantes(self) -> int:
        if self.capacite is None:
            return -1
        return self.capacite - self.nombre_inscrits_actifs

    @property
    def est_complete(self) -> bool:
        if self.capacite is None:
            return False
        return self.nombre_inscrits_actifs >= self.capacite

    @property
    def accepte_inscriptions(self) -> bool:
        return self.statut == self.Statut.INSCRIPTIONS_OUVERTES
