from django.db import models
from django.utils.translation import gettext_lazy as _

from django_formation.models.base import UUIDModel, TimeStampedModel


class Etablissement(UUIDModel, TimeStampedModel):
    nom = models.CharField(max_length=255, verbose_name=_("Nom"))
    code = models.SlugField(max_length=50, unique=True, verbose_name=_("Code"))
    raison_sociale = models.CharField(max_length=255, blank=True, verbose_name=_("Raison sociale"))
    telephone = models.CharField(max_length=30, blank=True, verbose_name=_("Téléphone"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    adresse = models.TextField(blank=True, verbose_name=_("Adresse"))
    ville = models.CharField(max_length=100, blank=True, verbose_name=_("Ville"))
    pays = models.CharField(max_length=100, default="Mali", verbose_name=_("Pays"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))

    class Meta:
        verbose_name = _("Établissement")
        verbose_name_plural = _("Établissements")
        ordering = ["nom"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["actif"]),
            models.Index(fields=["nom"]),
        ]

    def __str__(self):
        return f"{self.nom} ({self.code})"

    def save(self, *args, **kwargs):
        self.code = self.code.lower()
        super().save(*args, **kwargs)
