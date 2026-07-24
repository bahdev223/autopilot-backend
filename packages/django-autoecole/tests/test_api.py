import pytest
from django.contrib.auth.models import User
from django_formation.models import Etablissement, MembreEtablissement
from rest_framework.test import APIClient

from django_autoecole.models import CategoriePermis
from factories import MoniteurFactory, VehiculeFactory


pytestmark = pytest.mark.django_db


def test_api_exige_authentification():
    response = APIClient().get("/api/v1/autoecole/categories-permis/")
    assert response.status_code in (401, 403)


def test_api_pagine_et_isole_les_etablissements():
    user = User.objects.create_user("owner")
    own = Etablissement.objects.create(nom="Centre A", code="centre-a")
    other = Etablissement.objects.create(nom="Centre B", code="centre-b")
    MembreEtablissement.objects.create(
        etablissement=own,
        utilisateur=user,
        role="PROPRIETAIRE",
    )
    CategoriePermis.objects.create(etablissement=own, code="B", nom="Permis B")
    CategoriePermis.objects.create(etablissement=other, code="C", nom="Permis C")
    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/v1/autoecole/categories-permis/")
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["code"] == "B"

    response = client.post(
        "/api/v1/autoecole/categories-permis/",
        {"etablissement": str(other.pk), "code": "D", "nom": "Permis D"},
        format="json",
    )
    assert response.status_code == 403


def test_schema_openapi_est_genere():
    response = APIClient().get("/api/schema/")
    assert response.status_code == 200
    assert b"openapi" in response.content


def test_actions_moniteur_vehicule_et_categorie():
    user = User.objects.create_user("manager")
    etablissement = Etablissement.objects.create(nom="Centre", code="centre")
    MembreEtablissement.objects.create(
        etablissement=etablissement,
        utilisateur=user,
        role="PROPRIETAIRE",
    )
    categorie = CategoriePermis.objects.create(
        etablissement=etablissement,
        code="B",
        nom="Permis B",
    )
    moniteur = MoniteurFactory(etablissement=etablissement)
    vehicule = VehiculeFactory(
        etablissement=etablissement,
        categorie_permis=categorie,
    )
    client = APIClient()
    client.force_authenticate(user)

    for action in ("desactiver", "activer"):
        response = client.post(
            f"/api/v1/autoecole/categories-permis/{categorie.pk}/{action}/"
        )
        assert response.status_code == 200

    for action in ("indisponible", "activer", "suspendre", "reactiver", "archiver"):
        response = client.post(
            f"/api/v1/autoecole/moniteurs/{moniteur.pk}/{action}/"
        )
        assert response.status_code == 200

    for action in (
        "mettre_en_entretien",
        "rendre_disponible",
        "declarer_en_panne",
        "rendre_disponible",
        "mettre_hors_service",
        "archiver",
    ):
        response = client.post(
            f"/api/v1/autoecole/vehicules/{vehicule.pk}/{action}/"
        )
        assert response.status_code == 200
