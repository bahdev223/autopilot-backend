from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_formation.models.base import UUIDModel, TimeStampedModel


class MembreEtablissement(UUIDModel, TimeStampedModel):
    class Role(models.TextChoices):
        PROPRIETAIRE = "PROPRIETAIRE", _("Propriétaire")
        ADMINISTRATEUR = "ADMINISTRATEUR", _("Administrateur")
        RESPONSABLE = "RESPONSABLE", _("Responsable de formation")
        AGENT_INSCRIPTION = "AGENT_INSCRIPTION", _("Agent d'inscription")
        LECTEUR = "LECTEUR", _("Lecteur")

    etablissement = models.ForeignKey(
        "Etablissement", on_delete=models.CASCADE, related_name="membres",
        verbose_name=_("Établissement"),
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="adhesions_formation", verbose_name=_("Utilisateur"),
    )
    role = models.CharField(max_length=30, choices=Role.choices, verbose_name=_("Rôle"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))

    class Meta:
        verbose_name = _("Membre d'établissement")
        verbose_name_plural = _("Membres d'établissement")
        constraints = [
            models.UniqueConstraint(
                fields=["etablissement", "utilisateur"],
                name="formation_unique_membre_etablissement",
            ),
        ]

    def __str__(self):
        return f"{self.utilisateur} - {self.etablissement.nom} ({self.get_role_display()})"
