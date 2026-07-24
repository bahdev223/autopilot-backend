from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from django_formation.domain.exceptions.formation_exceptions import (
    SessionCapacityReachedError,
)
from django_formation.models.apprenant import Apprenant
from django_formation.models.etablissement import Etablissement
from django_formation.models.formation import Formation
from django_formation.models.inscription import Inscription
from django_formation.models.session import SessionFormation
from django_formation.services.inscriptions import InscriptionService


@skipUnless(connection.vendor == "postgresql", "Ce test exige PostgreSQL")
class EnrollmentConcurrencyTest(TransactionTestCase):
    reset_sequences = True

    def test_une_seule_inscription_sur_la_derniere_place(self):
        etablissement = Etablissement.objects.create(nom="Centre", code="centre")
        formation = Formation.objects.create(
            etablissement=etablissement,
            code="DEV",
            nom="Développement",
            statut=Formation.Statut.PUBLIEE,
        )
        session = SessionFormation.objects.create(
            etablissement=etablissement,
            formation=formation,
            code="DEV-S01",
            nom="Promotion",
            date_debut=date(2026, 9, 1),
            capacite=1,
            statut=SessionFormation.Statut.INSCRIPTIONS_OUVERTES,
        )
        learners = [
            Apprenant.objects.create(
                etablissement=etablissement,
                matricule=f"APP-{index}",
                nom="Test",
                prenom=str(index),
            )
            for index in (1, 2)
        ]
        barrier = Barrier(2)

        def enroll(learner_id):
            close_old_connections()
            barrier.wait()
            try:
                learner = Apprenant.objects.get(pk=learner_id)
                locked_session = SessionFormation.objects.get(pk=session.pk)
                InscriptionService().creer_preinscription(
                    apprenant=learner,
                    session=locked_session,
                )
                return "created"
            except SessionCapacityReachedError:
                return "capacity"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(enroll, [learner.pk for learner in learners]))

        self.assertCountEqual(results, ["created", "capacity"])
        self.assertEqual(Inscription.objects.filter(session=session).count(), 1)
