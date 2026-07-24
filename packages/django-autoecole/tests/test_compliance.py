from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.utils import timezone

from django_autoecole.api.permissions import IsAuthenticatedFormationMember
from django_autoecole.constants import StatutVehicule
from django_autoecole.exceptions import (
    AutoEcoleDomainError,
    CrossEstablishmentOperationError,
    InvalidMileageError,
)
from django_autoecole.models import (
    IndisponibiliteMoniteur,
    IndisponibiliteVehicule,
)
from django_autoecole.selectors import (
    lister_lecons_dossier,
    lister_lecons_moniteur,
    lister_lecons_vehicule,
    verifier_disponibilites,
)
from django_autoecole.services import moniteurs, vehicules
from factories import (
    CategoriePermisFactory,
    DossierAutoEcoleFactory,
    EtablissementFactory,
    LeconConduiteFactory,
    MoniteurFactory,
    VehiculeFactory,
)


pytestmark = pytest.mark.django_db


def test_cycle_services_moniteur():
    moniteur = MoniteurFactory()
    moniteurs.modifier_moniteur(moniteur, telephone="71000000")
    assert moniteur.telephone == "71000000"
    moniteurs.rendre_moniteur_indisponible(moniteur)
    moniteurs.activer_moniteur(moniteur)
    moniteurs.suspendre_moniteur(moniteur)
    moniteurs.reactiver_moniteur(moniteur)

    categorie = CategoriePermisFactory(etablissement=moniteur.etablissement)
    moniteurs.ajouter_habilitation_permis(moniteur, categorie)
    assert categorie in moniteur.categories_permis.all()
    moniteurs.retirer_habilitation_permis(moniteur, categorie)
    moniteurs.archiver_moniteur(moniteur)
    assert moniteur.statut == "ARCHIVE"

    autre = CategoriePermisFactory()
    with pytest.raises(CrossEstablishmentOperationError):
        moniteurs.ajouter_habilitation_permis(moniteur, autre)


def test_creation_moniteur_service():
    etablissement = EtablissementFactory()
    moniteur = moniteurs.creer_moniteur(
        etablissement=etablissement,
        matricule="MON-001",
        nom="Traore",
        prenom="Moussa",
    )
    assert moniteur.etablissement == etablissement


def test_cycle_services_vehicule():
    vehicule = VehiculeFactory(kilometrage_actuel=1000)
    vehicules.modifier_vehicule(vehicule, couleur="Bleu")
    vehicules.reserver_vehicule(vehicule)
    with pytest.raises(AutoEcoleDomainError):
        vehicules.reserver_vehicule(vehicule)
    vehicules.liberer_vehicule(vehicule)
    vehicules.mettre_vehicule_en_entretien(vehicule)
    vehicules.remettre_vehicule_disponible(vehicule)
    vehicules.declarer_vehicule_en_panne(vehicule)
    vehicules.remettre_vehicule_disponible(vehicule)
    vehicules.mettre_vehicule_hors_service(vehicule)
    vehicules.archiver_vehicule(vehicule)
    assert vehicule.statut == StatutVehicule.ARCHIVE

    with pytest.raises(InvalidMileageError):
        vehicules.mettre_a_jour_kilometrage(vehicule, -1)
    vehicules.mettre_a_jour_kilometrage(vehicule, 1100)
    assert vehicule.kilometrage_actuel == 1100


def test_creation_vehicule_et_validation_etablissement():
    etablissement = EtablissementFactory()
    categorie = CategoriePermisFactory(etablissement=etablissement)
    vehicule = vehicules.creer_vehicule(
        etablissement=etablissement,
        categorie_permis_id=categorie.pk,
        immatriculation="AA-001",
        marque="Toyota",
        modele="Yaris",
    )
    assert vehicule.etablissement == etablissement
    with pytest.raises(CrossEstablishmentOperationError):
        vehicules.creer_vehicule(
            etablissement=EtablissementFactory(),
            categorie_permis_id=categorie.pk,
            immatriculation="AA-002",
            marque="Toyota",
            modele="Yaris",
        )


def test_selecteurs_planning_et_indisponibilites():
    dossier = DossierAutoEcoleFactory(statut="EN_FORMATION")
    moniteur = MoniteurFactory(etablissement=dossier.etablissement)
    vehicule = VehiculeFactory(etablissement=dossier.etablissement)
    debut = timezone.now() + timedelta(days=1)
    fin = debut + timedelta(hours=1)
    lecon = LeconConduiteFactory(
        dossier=dossier,
        etablissement=dossier.etablissement,
        moniteur=moniteur,
        vehicule=vehicule,
        date_debut=debut,
        date_fin=fin,
    )
    assert lecon in lister_lecons_dossier(dossier.pk)
    assert lecon in lister_lecons_moniteur(
        moniteur.pk,
        debut - timedelta(minutes=1),
        fin + timedelta(minutes=1),
    )
    assert lecon in lister_lecons_vehicule(
        vehicule.pk,
        debut - timedelta(minutes=1),
        fin + timedelta(minutes=1),
    )

    IndisponibiliteMoniteur.objects.create(
        moniteur=moniteur,
        date_debut=debut,
        date_fin=fin,
        motif="Congé",
    )
    IndisponibiliteVehicule.objects.create(
        vehicule=vehicule,
        date_debut=debut,
        date_fin=fin,
        motif="Entretien",
    )
    result = verifier_disponibilites(
        moniteur_id=moniteur.pk,
        vehicule_id=vehicule.pk,
        date_debut=debut,
        date_fin=fin,
    )
    assert result == {"moniteur": True, "vehicule": True}
    assert verifier_disponibilites(
        moniteur_id=MoniteurFactory().pk,
        date_debut=debut,
        date_fin=fin,
    ) == {"moniteur": False}


def test_permission_objet_et_anonyme():
    permission = IsAuthenticatedFormationMember()
    assert permission.has_permission(SimpleNamespace(user=AnonymousUser()), None) is False
    user = User.objects.create_user("sans-adhesion")
    assert permission.has_permission(SimpleNamespace(user=user), None) is False
