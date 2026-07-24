from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.core.views import health

urlpatterns = [
    # AutoPilot — pages HTML
    path("", include("apps.core.urls_html")),
    path("health/", health, name="health"),
    # Administration
    path("admin/", admin.site.urls),
    # API — moteurs métier
    path("api/v1/formation/", include("django_formation.api.urls")),
    path("api/v1/autoecole/", include("django_autoecole.api.urls")),
    # API — Dépenses, Comptabilité, Comptes
    path("api/v1/", include("django_expenses.api.urls")),
    path("api/v1/", include("comptabilite_ohada.api.urls")),
    path("api/v1/", include("comptes.urls_api")),
    # HTML — Dépenses, Comptabilité, Comptes (pour l'interface AutoPilot)
    path("expenses/", include("django_expenses.urls")),
    path("comptabilite/", include("comptabilite_ohada.urls")),
    path("comptes/", include("comptes.urls")),
    # RH
    path("api/v1/rh/", include("django_rh.urls")),
    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
