from django.urls import path, include

urlpatterns = [
    path("api/v1/formation/", include("django_formation.api.urls")),
]
