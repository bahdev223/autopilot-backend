from django.test import TestCase
from django.db import IntegrityError
from django_formation.models.etablissement import Etablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_formation.models.historique import HistoriqueStatutInscription


class EtablissementTest(TestCase):
    def test_creation_etablissement(self):
        etab = Etablissement.objects.create(nom="Sahel Formation", code="sahel-001")
        self.assertEqual(etab.nom, "Sahel Formation")
        self.assertEqual(etab.code, "sahel-001")

    def test_code_normalise(self):
        etab = Etablissement.objects.create(nom="Test", code="TEST-CODE")
        self.assertEqual(etab.code, "test-code")

    def test_desactivation(self):
        etab = Etablissement.objects.create(nom="Test", code="test")
        self.assertTrue(etab.actif)
        etab.actif = False
        etab.save()
        etab.refresh_from_db()
        self.assertFalse(etab.actif)


class ApprenantTest(TestCase):
    def setUp(self):
        self.etab = Etablissement.objects.create(nom="Test", code="test")

    def test_creation_apprenant(self):
        a = Apprenant.objects.create(etablissement=self.etab, matricule="APP-2026-0001", nom="Diarra", prenom="Mamadou")
        self.assertEqual(a.nom_complet, "Mamadou Diarra")

    def test_matricule_unique_dans_etablissement(self):
        Apprenant.objects.create(etablissement=self.etab, matricule="APP-2026-0001", nom="A", prenom="B")
        with self.assertRaises(IntegrityError):
            Apprenant.objects.create(etablissement=self.etab, matricule="APP-2026-0001", nom="C", prenom="D")

    def test_meme_matricule_possible_dans_deux_etablissements(self):
        etab2 = Etablissement.objects.create(nom="Test2", code="test2")
        Apprenant.objects.create(etablissement=self.etab, matricule="APP-2026-0001", nom="A", prenom="B")
        Apprenant.objects.create(etablissement=etab2, matricule="APP-2026-0001", nom="C", prenom="D")

    def test_apprenant_sans_utilisateur(self):
        a = Apprenant.objects.create(etablissement=self.etab, matricule="APP-001", nom="X", prenom="Y")
        self.assertIsNone(a.utilisateur)


class FormationTest(TestCase):
    def setUp(self):
        self.etab = Etablissement.objects.create(nom="Test", code="test")

    def test_creation_formation(self):
        f = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Développement Web")
        self.assertEqual(f.statut, Formation.Statut.BROUILLON)

    def test_code_unique_par_etablissement(self):
        Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="A")
        with self.assertRaises(IntegrityError):
            Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="B")


class SessionTest(TestCase):
    def setUp(self):
        self.etab = Etablissement.objects.create(nom="Test", code="test")
        self.formation = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Dev Web", statut=Formation.Statut.PUBLIEE)

    def test_creation_session(self):
        from datetime import date
        s = SessionFormation.objects.create(
            etablissement=self.etab, formation=self.formation,
            code="DEVWEB-2026-S01", nom="Promo Sept 2026",
            date_debut=date(2026, 9, 1), capacite=25,
        )
        self.assertEqual(s.statut, SessionFormation.Statut.BROUILLON)
        self.assertEqual(s.nombre_places_restantes, 25)

    def test_calcul_places_restantes(self):
        from datetime import date
        s = SessionFormation.objects.create(
            etablissement=self.etab, formation=self.formation,
            code="S01", nom="Session 1", date_debut=date(2026, 1, 1), capacite=10,
        )
        self.assertFalse(s.est_complete)
        self.assertEqual(s.nombre_places_restantes, 10)

    def test_places_restantes_sans_capacite(self):
        from datetime import date
        s = SessionFormation.objects.create(
            etablissement=self.etab, formation=self.formation,
            code="S02", nom="Sans limite", date_debut=date(2026, 1, 1),
        )
        self.assertEqual(s.nombre_places_restantes, -1)
        self.assertFalse(s.est_complete)


class InscriptionTest(TestCase):
    def setUp(self):
        from datetime import date
        self.etab = Etablissement.objects.create(nom="Test", code="test")
        self.formation = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Dev", statut=Formation.Statut.PUBLIEE)
        self.apprenant = Apprenant.objects.create(etablissement=self.etab, matricule="APP-001", nom="A", prenom="B")
        self.session = SessionFormation.objects.create(
            etablissement=self.etab, formation=self.formation,
            code="S01", nom="Session 1", date_debut=date(2026, 1, 1), capacite=5,
            statut=SessionFormation.Statut.INSCRIPTIONS_OUVERTES,
        )

    def test_creation_inscription(self):
        from datetime import date
        ins = Inscription.objects.create(
            etablissement=self.etab, apprenant=self.apprenant, session=self.session,
            numero="INS-2026-0001", date_inscription=date.today(),
            statut=Inscription.Statut.PREINSCRITE,
        )
        self.assertEqual(ins.statut, Inscription.Statut.PREINSCRITE)

    def test_double_inscription_refusee(self):
        from datetime import date
        Inscription.objects.create(
            etablissement=self.etab, apprenant=self.apprenant, session=self.session,
            numero="INS-2026-0001", date_inscription=date.today(),
        )
        with self.assertRaises(IntegrityError):
            Inscription.objects.create(
                etablissement=self.etab, apprenant=self.apprenant, session=self.session,
                numero="INS-2026-0002", date_inscription=date.today(),
            )

    def test_numero_unique_par_etablissement(self):
        from datetime import date
        Inscription.objects.create(
            etablissement=self.etab, apprenant=self.apprenant, session=self.session,
            numero="INS-2026-0001", date_inscription=date.today(),
        )
        with self.assertRaises(IntegrityError):
            Inscription.objects.create(
                etablissement=self.etab, apprenant=self.apprenant, session=self.session,
                numero="INS-2026-0001", date_inscription=date.today(),
            )

    def test_historique_statut(self):
        from datetime import date
        ins = Inscription.objects.create(
            etablissement=self.etab, apprenant=self.apprenant, session=self.session,
            numero="INS-2026-0001", date_inscription=date.today(),
        )
        hist = HistoriqueStatutInscription.objects.create(
            inscription=ins, ancien_statut="", nouveau_statut="PREINSCRITE",
        )
        self.assertEqual(hist.nouveau_statut, "PREINSCRITE")
