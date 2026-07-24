from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase

from django_formation.api.permissions import (
    CanManageEnrollments,
    CanManageLearners,
    CanManageSessions,
    CanManageTrainings,
    IsAuthenticatedMember,
    IsProprietaireOrAdmin,
)
from django_formation.domain.value_objects.role_etablissement import RoleEtablissement
from django_formation.domain.validators.formation_validator import FormationValidator
from django_formation.models.apprenant import Apprenant
from django_formation.models.etablissement import Etablissement
from django_formation.models.formation import Formation
from django_formation.models.historique import HistoriqueStatutInscription
from django_formation.models.inscription import Inscription
from django_formation.models.membre import MembreEtablissement
from django_formation.models.session import SessionFormation
from django_formation.selectors.apprenants import ApprenantSelector
from django_formation.selectors.formations import FormationSelector
from django_formation.selectors.inscriptions import InscriptionSelector
from django_formation.selectors.sessions import SessionSelector


class SelectorsAndPermissionsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("owner")
        self.etablissement = Etablissement.objects.create(nom="Centre", code="centre")
        MembreEtablissement.objects.create(
            etablissement=self.etablissement,
            utilisateur=self.user,
            role=MembreEtablissement.Role.PROPRIETAIRE,
        )
        self.apprenant = Apprenant.objects.create(
            etablissement=self.etablissement,
            matricule="APP-001",
            nom="Diarra",
            prenom="Mamadou",
            email="mamadou@example.com",
        )
        self.formation = Formation.objects.create(
            etablissement=self.etablissement,
            code="DEV",
            nom="Développement",
            statut=Formation.Statut.PUBLIEE,
        )
        self.session = SessionFormation.objects.create(
            etablissement=self.etablissement,
            formation=self.formation,
            code="DEV-S01",
            nom="Promotion",
            date_debut=date(2026, 9, 1),
            capacite=2,
            statut=SessionFormation.Statut.INSCRIPTIONS_OUVERTES,
        )
        self.inscription = Inscription.objects.create(
            etablissement=self.etablissement,
            apprenant=self.apprenant,
            session=self.session,
            numero="INS-001",
            date_inscription=date(2026, 7, 23),
        )
        HistoriqueStatutInscription.objects.create(
            inscription=self.inscription,
            ancien_statut="",
            nouveau_statut=Inscription.Statut.PREINSCRITE,
        )

    def test_selectors(self):
        learners = ApprenantSelector()
        self.assertEqual(learners.apprenants_accessibles_par_utilisateur(self.user).count(), 1)
        self.assertEqual(learners.apprenants_par_etablissement(self.etablissement.pk).count(), 1)
        self.assertEqual(learners.rechercher_apprenants(self.etablissement.pk, "Diarra", "ACTIF").count(), 1)
        self.assertEqual(learners.detail_apprenant(self.apprenant.pk), self.apprenant)
        self.assertEqual(learners.inscriptions_apprenant(self.apprenant).count(), 1)

        trainings = FormationSelector()
        self.assertEqual(trainings.formations_accessibles_par_utilisateur(self.user).count(), 1)
        self.assertEqual(trainings.formations_publiees().count(), 1)
        self.assertEqual(trainings.formations_publiees(self.etablissement.pk).count(), 1)
        self.assertEqual(trainings.formations_par_etablissement(self.etablissement.pk).count(), 1)
        self.assertEqual(trainings.detail_formation(self.formation.pk), self.formation)
        self.assertEqual(trainings.sessions_formation(self.formation.pk).count(), 1)

        sessions = SessionSelector()
        self.assertEqual(sessions.sessions_accessibles_par_utilisateur(self.user).count(), 1)
        self.assertEqual(sessions.sessions_ouvertes().count(), 1)
        self.assertEqual(sessions.sessions_ouvertes(self.etablissement.pk).count(), 1)
        self.session.statut = SessionFormation.Statut.EN_COURS
        self.session.save(update_fields=["statut"])
        self.assertEqual(sessions.sessions_en_cours().count(), 1)
        self.assertEqual(sessions.sessions_en_cours(self.etablissement.pk).count(), 1)
        self.assertEqual(sessions.sessions_par_formation(self.formation.pk).count(), 1)
        self.assertEqual(sessions.detail_session(self.session.pk), self.session)
        self.assertEqual(sessions.inscrits_session(self.session.pk).count(), 1)
        self.assertEqual(sessions.places_restantes_session(self.session.pk), 1)

        enrollments = InscriptionSelector()
        self.assertEqual(enrollments.inscriptions_accessibles_par_utilisateur(self.user).count(), 1)
        self.assertEqual(enrollments.inscriptions_par_session(self.session.pk).count(), 1)
        self.assertEqual(enrollments.inscriptions_par_apprenant(self.apprenant.pk).count(), 1)
        self.assertEqual(
            enrollments.inscriptions_par_statut(self.etablissement.pk, "PREINSCRITE").count(),
            1,
        )
        self.assertEqual(enrollments.detail_inscription(self.inscription.pk), self.inscription)
        self.assertEqual(enrollments.historique_inscription(self.inscription.pk).count(), 1)

    def test_permissions_and_role_labels(self):
        request = SimpleNamespace(user=self.user)
        anonymous_request = SimpleNamespace(user=AnonymousUser())
        self.assertTrue(IsAuthenticatedMember().has_permission(request, None))
        self.assertFalse(IsAuthenticatedMember().has_permission(anonymous_request, None))

        permissions = [
            IsProprietaireOrAdmin(),
            CanManageLearners(),
            CanManageEnrollments(),
            CanManageTrainings(),
            CanManageSessions(),
        ]
        for permission in permissions:
            self.assertTrue(permission.has_permission(request, None))
            self.assertFalse(permission.has_permission(anonymous_request, None))
            self.assertTrue(permission.has_object_permission(request, None, self.apprenant))
            self.assertFalse(
                permission.has_object_permission(anonymous_request, None, self.apprenant)
            )

        self.assertEqual(RoleEtablissement.PROPRIETAIRE.label, "Propriétaire")

    def test_validateurs_metier(self):
        FormationValidator.valider_tarif(Decimal("0"))
        FormationValidator.valider_duree(0)
        FormationValidator.valider_capacite(1)
        FormationValidator.valider_dates(date(2026, 1, 1), date(2026, 1, 1))
        FormationValidator.valider_periodes_inscription(
            date(2025, 12, 1),
            date(2025, 12, 31),
        )

        invalid_calls = [
            lambda: FormationValidator.valider_tarif(-1),
            lambda: FormationValidator.valider_duree(-1),
            lambda: FormationValidator.valider_capacite(0),
            lambda: FormationValidator.valider_dates(
                date(2026, 2, 1),
                date(2026, 1, 1),
            ),
            lambda: FormationValidator.valider_periodes_inscription(
                date(2026, 2, 1),
                date(2026, 1, 1),
            ),
        ]
        for call in invalid_calls:
            with self.assertRaises(ValueError):
                call()
