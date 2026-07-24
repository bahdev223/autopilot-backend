import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ConfigurationAutoPilot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.OneToOneField(
        "django_formation.Etablissement", on_delete=models.CASCADE,
        related_name="configuration_autopilot",
    )
    devise = models.CharField(max_length=10, default="XOF")
    fuseau_horaire = models.CharField(max_length=50, default="Africa/Bamako")
    duree_lecon_defaut_minutes = models.PositiveIntegerField(default=60)
    verifier_expiration_documents = models.BooleanField(default=True)
    permettre_examen_sans_heures_minimum = models.BooleanField(default=False)
    prefixe_numero_dossier = models.CharField(max_length=10, default="AE")
    prefixe_matricule_moniteur = models.CharField(max_length=10, default="MON")
    score_maximum_evaluation = models.DecimalField(max_digits=4, decimal_places=2, default=20.00)
    delai_annulation_lecon_heures = models.PositiveIntegerField(default=24)
    apercu_disponibilite_jours = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "autopilot_configuration"
        verbose_name = _("Configuration AutoPilot")
        verbose_name_plural = _("Configurations AutoPilot")

    def __str__(self):
        return f"Configuration - {self.etablissement}"


class JournalAuditAutoPilot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(
        "django_formation.Etablissement", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="audits_autopilot",
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="audits_autopilot",
    )
    action = models.CharField(max_length=255)
    categorie = models.CharField(max_length=50, default="GENERAL")
    entite_type = models.CharField(max_length=100, blank=True)
    entite_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "autopilot_journal_audit"
        verbose_name = _("Journal d'audit AutoPilot")
        verbose_name_plural = _("Journaux d'audit AutoPilot")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["etablissement", "-created_at"]),
            models.Index(fields=["action"]),
            models.Index(fields=["categorie"]),
            models.Index(fields=["entite_type", "entite_id"]),
        ]

    def __str__(self):
        return f"[{self.created_at}] {self.action} par {self.utilisateur or 'inconnu'}"
