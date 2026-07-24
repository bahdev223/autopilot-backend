"""
AutoPilot — Configuration de base (commune à tous les environnements).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key-change-in-production")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # "drf_spectacular_sidecar",
    # AutoPilot apps
    "apps.core",
    # Moteurs métier
    "django_formation",
    "django_autoecole",
    # Intégrations — Dépenses, Comptabilité, Comptes financiers
    "django_expenses",
    "comptabilite_ohada",
    "comptes",
    # RH
    "django_rh",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.EtablissementActifMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.autopilot_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database — support DATABASE_URL ou variables DB_*
_database_url = os.getenv("DATABASE_URL")
if _database_url:
    import re
    match = re.match(r"postgres://(.+):(.+)@(.+):(\d+)/(.+)", _database_url)
    if match:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": match.group(5),
                "USER": match.group(1),
                "PASSWORD": match.group(2),
                "HOST": match.group(3),
                "PORT": match.group(4),
            }
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "autopilot"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "fr")
TIME_ZONE = os.getenv("TIME_ZONE", "Africa/Bamako")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.api.exceptions.autopilot_exception_handler",
}

# Spectacular / OpenAPI
SPECTACULAR_SETTINGS = {
    "TITLE": "AutoPilot API",
    "DESCRIPTION": "Plateforme complète de gestion des auto-écoles",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": None,
    "SWAGGER_UI_FAVICON_HREF": None,
    "REDOC_DIST": None,
}

# CORS
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
CORS_ALLOW_CREDENTIALS = True

# Auth
LOGIN_URL = "/connexion/"
LOGIN_REDIRECT_URL = "/"

# Email (console pour dev)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# AutoPilot settings
AUTOPILOT_CONFIG = {
    "ETABLISSEMENT_PAR_DEFAUT": os.getenv("AUTOPILOT_ETABLISSEMENT", ""),
}
