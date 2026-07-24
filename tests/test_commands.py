import pytest
from io import StringIO
from django.core.management import call_command
from django.contrib.auth.models import User, Group
from django_formation.models.etablissement import Etablissement
from django_formation.models.membre import MembreEtablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_autoecole.models import Moniteur, Vehicule, DossierAutoEcole, LeconConduite, ExamenAutoEcole, CategoriePermis
from apps.core.models import ConfigurationAutoPilot

pytestmark = pytest.mark.django_db


class TestSetupAutopilot:
    def test_creates_groups(self):
        out = StringIO()
        call_command("setup_autopilot", stdout=out)
        assert Group.objects.filter(name="DIRECTION").exists()
        assert Group.objects.filter(name="RESPONSABLE_PEDAGOGIQUE").exists()
        assert Group.objects.filter(name="AGENT_PLANNING").exists()
        assert Group.objects.filter(name="LECTEUR").exists()

    def test_direction_has_permissions(self):
        call_command("setup_autopilot")
        groupe = Group.objects.get(name="DIRECTION")
        assert groupe.permissions.count() > 10

    def test_idempotent(self):
        call_command("setup_autopilot")
        call_command("setup_autopilot")
        assert Group.objects.count() == 4


class TestSetupDemoAutoEcole:
    def test_creates_all_entities(self):
        out = StringIO()
        call_command("setup_demo_autoecole", stdout=out)
        assert User.objects.filter(username="admin").exists()
        assert Etablissement.objects.filter(code="autopilot-demo").exists()
        assert Apprenant.objects.count() == 5
        assert Formation.objects.count() == 3
        assert SessionFormation.objects.count() == 5
        assert Inscription.objects.count() == 5
        assert CategoriePermis.objects.count() == 3
        assert Moniteur.objects.count() == 3
        assert Vehicule.objects.count() == 5
        assert DossierAutoEcole.objects.count() == 5
        assert LeconConduite.objects.count() >= 100
        assert ExamenAutoEcole.objects.count() == 3
        assert ConfigurationAutoPilot.objects.count() == 1

    def test_admin_user_is_staff(self):
        call_command("setup_demo_autoecole")
        admin = User.objects.get(username="admin")
        assert admin.is_staff
        assert admin.is_superuser

    def test_etablissement_membership(self):
        call_command("setup_demo_autoecole")
        etab = Etablissement.objects.get(code="autopilot-demo")
        assert MembreEtablissement.objects.filter(
            etablissement=etab, utilisateur__username="admin"
        ).exists()

    def test_idempotent(self):
        call_command("setup_demo_autoecole")
        call_command("setup_demo_autoecole")
        assert Apprenant.objects.count() == 5
        assert DossierAutoEcole.objects.count() == 5
