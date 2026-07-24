from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FormationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_formation"
    verbose_name = _("Formation")

    def ready(self):
        pass
