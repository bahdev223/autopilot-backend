from .base import *  # noqa

DEBUG = False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "autopilot.app").split(",")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

STATIC_ROOT = "/var/www/autopilot/static"
MEDIA_ROOT = "/var/www/autopilot/media"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "/var/log/autopilot/error.log",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}
