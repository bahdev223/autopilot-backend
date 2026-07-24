from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoAutoecoleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_autoecole"
    verbose_name = _("Auto-école")
    label = "django_autoecole"

    def ready(self):
        import django_autoecole.signals  # noqa
