from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_formation.models.base import UUIDModel, TimeStampedModel


class HistoriqueStatutInscription(UUIDModel, TimeStampedModel):
    inscription = models.ForeignKey(
        "Inscription", on_delete=models.CASCADE, related_name="historique_statuts",
        verbose_name=_("Inscription"),
    )
    ancien_statut = models.CharField(max_length=25, blank=True, verbose_name=_("Ancien statut"))
    nouveau_statut = models.CharField(max_length=25, verbose_name=_("Nouveau statut"))
    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", verbose_name=_("Modifié par"),
    )

    class Meta:
        verbose_name = _("Historique de statut d'inscription")
        verbose_name_plural = _("Historiques de statut d'inscription")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.inscription.numero}: {self.ancien_statut} → {self.nouveau_statut}"
