from django.db import models
from django.utils.translation import gettext_lazy as _

from django_formation.models.base import UUIDModel, TimeStampedModel


class Inscription(UUIDModel, TimeStampedModel):
    class Statut(models.TextChoices):
        PREINSCRITE = "PREINSCRITE", _("Préinscrite")
        EN_ATTENTE = "EN_ATTENTE", _("En attente")
        CONFIRMEE = "CONFIRMEE", _("Confirmée")
        REFUSEE = "REFUSEE", _("Refusée")
        ANNULEE = "ANNULEE", _("Annulée")
        EN_COURS = "EN_COURS", _("En cours")
        ABANDONNEE = "ABANDONNEE", _("Abandonnée")
        TERMINEE = "TERMINEE", _("Terminée")

    etablissement = models.ForeignKey(
        "Etablissement", on_delete=models.PROTECT, related_name="inscriptions",
        verbose_name=_("Établissement"),
    )
    apprenant = models.ForeignKey(
        "Apprenant", on_delete=models.PROTECT, related_name="inscriptions",
        verbose_name=_("Apprenant"),
    )
    session = models.ForeignKey(
        "SessionFormation", on_delete=models.PROTECT, related_name="inscriptions",
        verbose_name=_("Session"),
    )
    numero = models.CharField(max_length=50, verbose_name=_("Numéro"))
    date_inscription = models.DateField(verbose_name=_("Date d'inscription"))
    statut = models.CharField(
        max_length=25, choices=Statut.choices, default=Statut.PREINSCRITE, verbose_name=_("Statut"),
    )
    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))
    motif_refus = models.TextField(blank=True, verbose_name=_("Motif de refus"))
    motif_annulation = models.TextField(blank=True, verbose_name=_("Motif d'annulation"))
    date_confirmation = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de confirmation"))
    date_fin = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de fin"))

    class Meta:
        verbose_name = _("Inscription")
        verbose_name_plural = _("Inscriptions")
        constraints = [
            models.UniqueConstraint(
                fields=["apprenant", "session"],
                name="formation_unique_apprenant_session",
            ),
            models.UniqueConstraint(
                fields=["etablissement", "numero"],
                name="formation_unique_numero_inscription_etablissement",
            ),
        ]

    def __str__(self):
        return f"{self.numero} - {self.apprenant.nom_complet} ({self.session.nom})"
