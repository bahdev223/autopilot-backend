from datetime import date
from django.test import TestCase
from django_formation.models.etablissement import Etablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_formation.models.historique import HistoriqueStatutInscription
from django_formation.services.apprenants import ApprenantService
from django_formation.services.formations import FormationService
from django_formation.services.sessions import SessionService
from django_formation.services.inscriptions import InscriptionService
from django_formation.domain.exceptions.formation_exceptions import (
    InactiveEstablishmentError, InvalidStatusTransitionError,
    ArchivedTrainingError, SessionNotOpenError, DuplicateEnrollmentError,
    SessionCapacityReachedError, MissingRejectionReasonError, MissingCancellationReasonError,
    ArchivedLearnerError, TrainingNotPublishedError, NoConfirmedEnrollmentsError,
    CrossEstablishmentOperationError,
)


class ApprenantServiceTest(TestCase):
    def setUp(self):
        self.svc = ApprenantService()
        self.etab = Etablissement.objects.create(nom="Test", code="test")

    def test_creer_apprenant_dans_etablissement_actif(self):
        a = self.svc.creer_apprenant(etablissement=self.etab, nom="Diarra", prenom="Mamadou")
        self.assertEqual(a.nom, "DIARRA")
        self.assertEqual(a.statut, Apprenant.Statut.ACTIF)
        self.assertTrue(a.matricule.startswith("APP-"))

    def test_creer_apprenant_dans_etablissement_inactif_refuse(self):
        self.etab.actif = False
        self.etab.save()
        with self.assertRaises(InactiveEstablishmentError):
            self.svc.creer_apprenant(etablissement=self.etab, nom="X", prenom="Y")

    def test_generation_automatique_matricule(self):
        a1 = self.svc.creer_apprenant(etablissement=self.etab, nom="A", prenom="B")
        a2 = self.svc.creer_apprenant(etablissement=self.etab, nom="C", prenom="D")
        self.assertNotEqual(a1.matricule, a2.matricule)

    def test_archiver_apprenant(self):
        a = self.svc.creer_apprenant(etablissement=self.etab, nom="X", prenom="Y")
        self.svc.archiver_apprenant(a)
        a.refresh_from_db()
        self.assertEqual(a.statut, Apprenant.Statut.ARCHIVE)

    def test_activdepuis_inactif(self):
        a = self.svc.creer_apprenant(etablissement=self.etab, nom="X", prenom="Y")
        self.svc.desactiver_apprenant(a)
        a.refresh_from_db()
        self.assertEqual(a.statut, Apprenant.Statut.INACTIF)

    def test_archiver_apprenant_inactif(self):
        a = self.svc.creer_apprenant(etablissement=self.etab, nom="X", prenom="Y")
        self.svc.desactiver_apprenant(a)
        self.svc.archiver_apprenant(a)
        a.refresh_from_db()
        self.assertEqual(a.statut, Apprenant.Statut.ARCHIVE)


class FormationServiceTest(TestCase):
    def setUp(self):
        self.svc = FormationService()
        self.etab = Etablissement.objects.create(nom="Test", code="test")

    def test_publier_formation_brouillon(self):
        f = self.svc.creer_formation(etablissement=self.etab, code="DEVWEB", nom="Dev Web")
        self.svc.publier_formation(f)
        f.refresh_from_db()
        self.assertEqual(f.statut, Formation.Statut.PUBLIEE)

    def test_archiver_formation(self):
        f = self.svc.creer_formation(etablissement=self.etab, code="DEVWEB", nom="Dev")
        self.svc.archiver_formation(f)
        f.refresh_from_db()
        self.assertEqual(f.statut, Formation.Statut.ARCHIVEE)

    def test_publier_et_archiver_depuis_publiee(self):
        f = self.svc.creer_formation(etablissement=self.etab, code="DEVWEB", nom="Dev")
        self.svc.publier_formation(f)
        self.svc.archiver_formation(f)
        f.refresh_from_db()
        self.assertEqual(f.statut, Formation.Statut.ARCHIVEE)

    def test_publier_formation_dans_etablissement_inactif(self):
        self.etab.actif = False
        self.etab.save()
        f = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Dev")
        with self.assertRaises(InactiveEstablishmentError):
            self.svc.publier_formation(f)


class SessionServiceTest(TestCase):
    def setUp(self):
        self.svc = SessionService()
        self.etab = Etablissement.objects.create(nom="Test", code="test")
        self.formation = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Dev", statut=Formation.Statut.PUBLIEE)

    def test_ouvrir_inscriptions(self):
        s = self.svc.creer_session(etablissement=self.etab, formation=self.formation, code="S01", nom="Session 1", date_debut=date(2026, 9, 1))
        self.svc.ouvrir_inscriptions(s)
        s.refresh_from_db()
        self.assertEqual(s.statut, SessionFormation.Statut.INSCRIPTIONS_OUVERTES)

    def test_ouvrir_session_formation_non_publiee_refuse(self):
        f2 = Formation.objects.create(etablissement=self.etab, code="AUTRE", nom="Autre")
        s = self.svc.creer_session(etablissement=self.etab, formation=f2, code="S02", nom="Session 2", date_debut=date(2026, 9, 1))
        with self.assertRaises(TrainingNotPublishedError):
            self.svc.ouvrir_inscriptions(s)

    def test_annuler_session(self):
        s = self.svc.creer_session(etablissement=self.etab, formation=self.formation, code="S01", nom="S1", date_debut=date(2026, 9, 1))
        self.svc.annuler_session(s)
        s.refresh_from_db()
        self.assertEqual(s.statut, SessionFormation.Statut.ANNULEE)

    def test_demarrer_session_sans_inscriptions(self):
        s = self.svc.creer_session(etablissement=self.etab, formation=self.formation, code="S01", nom="S1", date_debut=date(2026, 9, 1))
        self.svc.ouvrir_inscriptions(s)
        with self.assertRaises(NoConfirmedEnrollmentsError):
            self.svc.demarrer_session(s)

    def test_fermeture_puis_reouverture(self):
        s = self.svc.creer_session(etablissement=self.etab, formation=self.formation, code="S01", nom="S1", date_debut=date(2026, 9, 1))
        self.svc.ouvrir_inscriptions(s)
        self.svc.fermer_inscriptions(s)
        s.refresh_from_db()
        self.assertEqual(s.statut, SessionFormation.Statut.INSCRIPTIONS_FERMEES)

    def test_creer_session_formation_archived(self):
        f2 = Formation.objects.create(etablissement=self.etab, code="ARCH", nom="Archived", statut=Formation.Statut.ARCHIVEE)
        with self.assertRaises(ArchivedTrainingError):
            self.svc.creer_session(etablissement=self.etab, formation=f2, code="S01", nom="S1", date_debut=date(2026, 9, 1))

    def test_creer_session_etablissement_different(self):
        etab2 = Etablissement.objects.create(nom="Autre", code="autre")
        with self.assertRaises(CrossEstablishmentOperationError):
            self.svc.creer_session(etablissement=etab2, formation=self.formation, code="S01", nom="S1", date_debut=date(2026, 9, 1))


class InscriptionServiceTest(TestCase):
    def setUp(self):
        self.svc = InscriptionService()
        self.etab = Etablissement.objects.create(nom="Test", code="test")
        self.formation = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Dev", statut=Formation.Statut.PUBLIEE)
        self.apprenant = Apprenant.objects.create(etablissement=self.etab, matricule="APP-001", nom="A", prenom="B")
        self.session = SessionFormation.objects.create(
            etablissement=self.etab, formation=self.formation,
            code="S01", nom="Session 1", date_debut=date(2026, 9, 1), capacite=5,
            statut=SessionFormation.Statut.INSCRIPTIONS_OUVERTES,
        )

    def test_creer_preinscription(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.assertEqual(ins.statut, Inscription.Statut.PREINSCRITE)
        self.assertTrue(ins.numero.startswith("INS-"))
        self.assertTrue(HistoriqueStatutInscription.objects.filter(inscription=ins).exists())

    def test_inscription_session_fermee_refusee(self):
        self.session.statut = SessionFormation.Statut.BROUILLON
        self.session.save()
        with self.assertRaises(SessionNotOpenError):
            self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)

    def test_inscription_apprenant_archive_refusee(self):
        self.apprenant.statut = Apprenant.Statut.ARCHIVE
        self.apprenant.save()
        with self.assertRaises(ArchivedLearnerError):
            self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)

    def test_double_inscription_refusee(self):
        self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        with self.assertRaises(DuplicateEnrollmentError):
            self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)

    def test_capacite_maximale_respectee(self):
        self.session.capacite = 1
        self.session.save()
        self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        a2 = Apprenant.objects.create(etablissement=self.etab, matricule="APP-002", nom="C", prenom="D")
        with self.assertRaises(SessionCapacityReachedError):
            self.svc.creer_preinscription(apprenant=a2, session=self.session)

    def test_capacite_infinie(self):
        self.session.capacite = None
        self.session.save()
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.assertIsNotNone(ins)

    def test_confirmation_inscription(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.svc.confirmer_inscription(ins)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, Inscription.Statut.CONFIRMEE)
        self.assertIsNotNone(ins.date_confirmation)

    def test_refus_avec_motif(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.svc.refuser_inscription(ins, motif="Dossier incomplet")
        ins.refresh_from_db()
        self.assertEqual(ins.statut, Inscription.Statut.REFUSEE)

    def test_refus_sans_motif_refuse(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        with self.assertRaises(MissingRejectionReasonError):
            self.svc.refuser_inscription(ins, motif="")

    def test_annulation_avec_motif(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.svc.annuler_inscription(ins, motif="Retrait volontaire")
        ins.refresh_from_db()
        self.assertEqual(ins.statut, Inscription.Statut.ANNULEE)

    def test_terminer_inscription(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.svc.confirmer_inscription(ins)
        self.svc.demarrer_inscription(ins)
        self.svc.terminer_inscription(ins)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, Inscription.Statut.TERMINEE)

    def test_abandon_inscription(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.svc.confirmer_inscription(ins)
        self.svc.demarrer_inscription(ins)
        self.svc.marquer_abandon(ins)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, Inscription.Statut.ABANDONNEE)

    def test_mise_en_attente(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.svc.mettre_en_attente(ins)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, Inscription.Statut.EN_ATTENTE)

    def test_transition_invalide(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        with self.assertRaises(InvalidStatusTransitionError):
            self.svc.demarrer_inscription(ins)

    def test_historique_cree_apres_transition(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.svc.confirmer_inscription(ins)
        hist_count = HistoriqueStatutInscription.objects.filter(inscription=ins).count()
        self.assertEqual(hist_count, 2)

    def test_annulation_sans_motif(self):
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        with self.assertRaises(MissingCancellationReasonError):
            self.svc.annuler_inscription(ins, motif="")

    def test_cross_etablissement_refuse(self):
        etab2 = Etablissement.objects.create(nom="Autre", code="autre")
        apprenant2 = Apprenant.objects.create(etablissement=etab2, matricule="APP-999", nom="X", prenom="Y")
        with self.assertRaises(CrossEstablishmentOperationError):
            self.svc.creer_preinscription(apprenant=apprenant2, session=self.session)

    def test_demarrer_session_cree_historique_pour_inscriptions(self):
        session_svc = SessionService()
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.svc.confirmer_inscription(ins)
        session_svc.demarrer_session(self.session, modifie_par=None)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, Inscription.Statut.EN_COURS)
        hist_count = HistoriqueStatutInscription.objects.filter(inscription=ins, nouveau_statut="EN_COURS").count()
        self.assertEqual(hist_count, 1)

    def test_annuler_session_cree_historique_pour_inscriptions(self):
        session_svc = SessionService()
        ins = self.svc.creer_preinscription(apprenant=self.apprenant, session=self.session)
        self.svc.confirmer_inscription(ins)
        session_svc.annuler_session(self.session, modifie_par=None)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, Inscription.Statut.ANNULEE)
        self.assertEqual(ins.motif_annulation, "Session annulée")
        hist_count = HistoriqueStatutInscription.objects.filter(inscription=ins, nouveau_statut="ANNULEE").count()
        self.assertEqual(hist_count, 1)
