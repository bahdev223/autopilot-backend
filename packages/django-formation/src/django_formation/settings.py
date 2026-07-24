from django.conf import settings
from django.utils.module_loading import import_string

DJANGO_FORMATION = getattr(settings, "DJANGO_FORMATION", {})

DEFAULT_COUNTRY = DJANGO_FORMATION.get("DEFAULT_COUNTRY", "Mali")
DEFAULT_CURRENCY = DJANGO_FORMATION.get("DEFAULT_CURRENCY", "XOF")
LEARNER_NUMBER_PREFIX = DJANGO_FORMATION.get("LEARNER_NUMBER_PREFIX", "APP")
ENROLLMENT_NUMBER_PREFIX = DJANGO_FORMATION.get("ENROLLMENT_NUMBER_PREFIX", "INS")
ALLOW_LEARNER_USER_LINK = DJANGO_FORMATION.get("ALLOW_LEARNER_USER_LINK", True)
ENABLE_API = DJANGO_FORMATION.get("ENABLE_API", True)


def get_number_generator(setting_name):
    path = DJANGO_FORMATION.get(setting_name, "django_formation.numbering.sequential_number")
    return import_string(path)
