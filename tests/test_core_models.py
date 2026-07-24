import pytest
from django.db import IntegrityError
from django.contrib.auth.models import User
from django_formation.models.etablissement import Etablissement
from apps.core.models import ConfigurationAutoPilot, JournalAuditAutoPilot
from tests.factories import EtablissementFactory, UserFactory, ConfigurationAutoPilotFactory

pytestmark = pytest.mark.django_db


class TestConfigurationAutoPilot:
    def test_creer_configuration(self):
        etab = EtablissementFactory()
        config = ConfigurationAutoPilot.objects.create(
            etablissement=etab, devise="XOF",
        )
        assert config.devise == "XOF"
        assert config.fuseau_horaire == "Africa/Bamako"
        assert config.pk is not None

    def test_uniqueness_one_per_etablissement(self):
        etab = EtablissementFactory()
        ConfigurationAutoPilot.objects.create(etablissement=etab)
        with pytest.raises(IntegrityError):
            ConfigurationAutoPilot.objects.create(etablissement=etab)

    def test_default_values(self):
        config = ConfigurationAutoPilotFactory()
        assert config.duree_lecon_defaut_minutes == 60
        assert config.devise == "XOF"
        assert config.fuseau_horaire == "Africa/Bamako"
        assert config.verifier_expiration_documents is True
        assert config.permettre_examen_sans_heures_minimum is False
        assert config.delai_annulation_lecon_heures == 24
        assert config.apercu_disponibilite_jours == 30

    def test_str_representation(self):
        etab = EtablissementFactory(nom="Auto Ecole Test")
        config = ConfigurationAutoPilot.objects.create(etablissement=etab)
        assert str(config) == f"Configuration - {etab}"

    def test_timestamps_auto(self):
        config = ConfigurationAutoPilotFactory()
        assert config.created_at is not None
        assert config.updated_at is not None

    def test_update_config(self):
        config = ConfigurationAutoPilotFactory(devise="XOF")
        config.devise = "EUR"
        config.save()
        config.refresh_from_db()
        assert config.devise == "EUR"


class TestJournalAuditAutoPilot:
    def test_creer_entree(self):
        entry = JournalAuditAutoPilot.objects.create(
            action="TEST_ACTION", categorie="TEST",
        )
        assert entry.pk is not None
        assert entry.action == "TEST_ACTION"
        assert entry.categorie == "TEST"

    def test_creer_avec_etablissement_et_utilisateur(self):
        etab = EtablissementFactory()
        user = UserFactory()
        entry = JournalAuditAutoPilot.objects.create(
            etablissement=etab, utilisateur=user,
            action="UTILISATEUR_CONNECTE", categorie="AUTH",
            entite_type="User", entite_id=str(user.pk),
            details={"ip": "127.0.0.1"},
        )
        assert entry.etablissement == etab
        assert entry.utilisateur == user
        assert entry.details == {"ip": "127.0.0.1"}

    def test_ordering_by_created_at_desc(self):
        e1 = JournalAuditAutoPilot.objects.create(action="FIRST")
        e2 = JournalAuditAutoPilot.objects.create(action="SECOND")
        entries = JournalAuditAutoPilot.objects.all()
        assert entries[0] == e2
        assert entries[1] == e1

    def test_str_representation(self):
        user = UserFactory()
        entry = JournalAuditAutoPilot.objects.create(
            action="TEST", utilisateur=user,
        )
        assert str(user.username) in str(entry)
        assert "TEST" in str(entry)

    def test_etablissement_nullable_on_delete(self):
        etab = EtablissementFactory()
        entry = JournalAuditAutoPilot.objects.create(
            etablissement=etab, action="BEFORE_DELETE",
        )
        etab.delete()
        entry.refresh_from_db()
        assert entry.etablissement is None

    def test_indexes_created(self):
        indexes = JournalAuditAutoPilot._meta.indexes
        assert len(indexes) >= 4
