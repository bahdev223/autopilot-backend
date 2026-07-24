from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless

import pytest
from django.db import close_old_connections, connection
from django.utils import timezone

from django_autoecole.exceptions import LessonTimeConflictError
from django_autoecole.models import DossierAutoEcole, Moniteur, Vehicule
from django_autoecole.services.lecons import planifier_lecon
from factories import DossierAutoEcoleFactory, MoniteurFactory, VehiculeFactory


pytestmark = pytest.mark.django_db(transaction=True)


@skipUnless(connection.vendor == "postgresql", "Ce test exige PostgreSQL")
def test_reservation_concurrente_moniteur_et_vehicule():
    dossier = DossierAutoEcoleFactory(statut="EN_FORMATION")
    moniteur = MoniteurFactory(etablissement=dossier.etablissement)
    moniteur.categories_permis.add(dossier.categorie_permis)
    vehicule = VehiculeFactory(
        etablissement=dossier.etablissement,
        categorie_permis=dossier.categorie_permis,
    )
    debut = timezone.now() + timedelta(days=1)
    fin = debut + timedelta(hours=1)
    barrier = Barrier(2)

    def reserve(_):
        close_old_connections()
        barrier.wait()
        try:
            planifier_lecon(
                dossier_id=DossierAutoEcole.objects.get(pk=dossier.pk).pk,
                moniteur_id=Moniteur.objects.get(pk=moniteur.pk).pk,
                vehicule_id=Vehicule.objects.get(pk=vehicule.pk).pk,
                type_lecon="CONDUITE",
                date_debut=debut,
                date_fin=fin,
            )
            return "created"
        except LessonTimeConflictError:
            return "conflict"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(reserve, range(2)))
    assert sorted(results) == ["conflict", "created"]
