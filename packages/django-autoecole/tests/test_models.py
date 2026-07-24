import pytest
from datetime import date, timedelta
from django.db import IntegrityError, transaction
from django_autoecole.exceptions import InvalidStatusTransitionError
from factories import (
    CategoriePermisFactory,
    DossierAutoEcoleFactory,
    MoniteurFactory,
    VehiculeFactory,
    LeconConduiteFactory,
    ExamenAutoEcoleFactory,
    EtablissementFactory,
)


class TestCategoriePermis:
    def test_creation(self, db):
        cat = CategoriePermisFactory(code="B", nom="Permis B")
        assert cat.code == "B"
        assert cat.actif is True

    def test_code_unique_par_etablissement(self, db):
        etab = EtablissementFactory()
        CategoriePermisFactory(etablissement=etab, code="B")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                CategoriePermisFactory(etablissement=etab, code="B")

    def test_str(self, db):
        cat = CategoriePermisFactory(code="B")
        assert str(cat) == "B - Permis B"


class TestDossierAutoEcole:
    def test_creation(self, db):
        dossier = DossierAutoEcoleFactory()
        assert dossier.statut == "BROUILLON"
        assert dossier.numero_dossier.startswith("AE-")

    def test_progression_conduite(self, db):
        dossier = DossierAutoEcoleFactory(
            heures_conduite_validees=10,
            categorie_permis__heures_conduite_minimum=20,
        )
        assert dossier.progression_conduite == 50.0

    def test_transition_invalide(self, db):
        dossier = DossierAutoEcoleFactory(statut="BROUILLON")
        with pytest.raises(InvalidStatusTransitionError):
            dossier.changer_statut("REUSSI")

    def test_transition_valide(self, db):
        dossier = DossierAutoEcoleFactory(statut="BROUILLON")
        dossier.changer_statut("OUVERT")
        assert dossier.statut == "OUVERT"


class TestMoniteur:
    def test_creation(self, db):
        moniteur = MoniteurFactory()
        assert moniteur.statut == "ACTIF"
        assert moniteur.nom_complet == "Moussa TRAORE"

    def test_est_disponible(self, db):
        moniteur = MoniteurFactory()
        assert moniteur.est_disponible is True

    def test_indisponible(self, db):
        from django_autoecole.constants import StatutMoniteur
        moniteur = MoniteurFactory(statut=StatutMoniteur.SUSPENDU)
        assert moniteur.est_disponible is False


class TestVehicule:
    def test_creation(self, db):
        v = VehiculeFactory()
        assert v.est_disponible is True
        assert v.documents_en_ordre is True

    def test_documents_expires(self, db):
        v = VehiculeFactory(
            date_expiration_assurance=date.today() - timedelta(days=1),
        )
        assert v.documents_en_ordre is False


class TestLeconConduite:
    def test_creation(self, db):
        dossier = DossierAutoEcoleFactory()
        lecon = LeconConduiteFactory(dossier=dossier)
        assert lecon.statut == "PLANIFIEE"
        assert lecon.duree_minutes == 60

    def test_transitions(self, db):
        lecon = LeconConduiteFactory()
        lecon.changer_statut("CONFIRMEE")
        assert lecon.statut == "CONFIRMEE"
        lecon.changer_statut("EN_COURS")
        assert lecon.statut == "EN_COURS"
        lecon.changer_statut("REALISEE")
        assert lecon.statut == "REALISEE"


class TestExamenAutoEcole:
    def test_creation(self, db):
        examen = ExamenAutoEcoleFactory()
        assert examen.statut == "BROUILLON"
        assert examen.resultat == "EN_ATTENTE"
