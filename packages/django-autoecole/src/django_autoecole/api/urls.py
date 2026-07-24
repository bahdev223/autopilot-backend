from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import (
    CategoriePermisViewSet, MoniteurViewSet, VehiculeViewSet,
    DossierAutoEcoleViewSet, LeconConduiteViewSet, ExamenAutoEcoleViewSet,
    IndisponibiliteMoniteurViewSet, IndisponibiliteVehiculeViewSet,
)

router = DefaultRouter()
router.register("categories-permis", CategoriePermisViewSet)
router.register("moniteurs", MoniteurViewSet)
router.register("vehicules", VehiculeViewSet)
router.register("dossiers", DossierAutoEcoleViewSet)
router.register("lecons", LeconConduiteViewSet)
router.register("examens", ExamenAutoEcoleViewSet)
router.register("indisponibilites-moniteurs", IndisponibiliteMoniteurViewSet)
router.register("indisponibilites-vehicules", IndisponibiliteVehiculeViewSet)

app_name = "django_autoecole"

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="django_autoecole:schema"), name="swagger-ui"),
] + router.urls
