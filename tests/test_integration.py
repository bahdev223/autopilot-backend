import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User

from django_formation.models.etablissement import Etablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_formation.services.apprenants import ApprenantService
from django_formation.services.formations import FormationService
from django_formation.services.sessions import SessionService
from django_formation.services.inscriptions import InscriptionService
from django_formation.domain.exceptions.formation_exceptions import FormationDomainError

from django_autoecole.models import (
    CategoriePermis, Moniteur, Vehicule, DossierAutoEcole,
    LeconConduite, ExamenAutoEcole, EvaluationLecon,
)
from django_autoecole.services.dossiers import (
    creer_dossier_autoecole, ouvrir_dossier, demarrer_formation_dossier,
    declarer_dossier_pret_examen, cloturer_dossier, suspendre_dossier,
    annuler_dossier,
)
from django_autoecole.services.lecons import (
    planifier_lecon, confirmer_lecon, demarrer_lecon,
    terminer_lecon, annuler_lecon,
)
from django_autoecole.services.examens import (
    planifier_examen, confirmer_examen, marquer_candidat_presente,
    enregistrer_resultat_examen,
)
from django_autoecole.services.moniteurs import creer_moniteur
from django_autoecole.services.vehicules import creer_vehicule
from django_autoecole.constants import (
    StatutDossier, StatutLecon, StatutExamen, ResultatExamen,
    TypeLecon, TypeExamen, TypeBoite, TypeCarburant, NiveauEvaluation,
    StatutMoniteur, StatutVehicule,
)
from django_autoecole.exceptions import (
    CrossEstablishmentOperationError, InvalidEnrollmentStatusError,
    DuplicateDrivingSchoolFileError, InsufficientTrainingHoursError,
    InstructorNotAuthorizedError, VehicleCategoryMismatchError,
    InvalidMileageError, MissingCancellationReasonError,
    LessonTimeConflictError, DossierNotExamReadyError,
    AutoEcoleDomainError,
)
from apps.core.models import ConfigurationAutoPilot, JournalAuditAutoPilot

from tests.factories import (
    EtablissementFactory, UserFactory, ApprenantFactory,
    FormationFactory, SessionFormationFactory, InscriptionFactory,
    CategoriePermisFactory, MoniteurFactory, VehiculeFactory,
    DossierAutoEcoleFactory,
)

pytestmark = pytest.mark.django_db


class TestFullWorkflow:
    def test_complete_scenario_inscription_to_cloture(self):
        admin = UserFactory(is_staff=True)
        etab = EtablissementFactory()
        cat = CategoriePermisFactory(
            etablissement=etab, code="B", heures_conduite_minimum=2,
            heures_theorie_minimum=1, nombre_evaluations_minimum=1,
        )
        moniteur = MoniteurFactory(etablissement=etab)
        moniteur.categories_permis.add(cat)
        vehicule = VehiculeFactory(
            etablissement=etab, categorie_permis=cat,
            type_boite=TypeBoite.MANUELLE,
        )
        apprenant = ApprenantFactory(etablissement=etab)
        formation = Formation.objects.create(
            etablissement=etab, code="B-CODE", nom="Permis B",
            duree_heures=240, duree_jours=30, tarif_indicatif=150000,
        )
        FormationService().publier_formation(formation)
        session = SessionFormation.objects.create(
            etablissement=etab, formation=formation,
            code="B-2026", nom="Session Test",
            date_debut=date.today() + timedelta(days=30), capacite=20,
        )
        SessionService().ouvrir_inscriptions(session)
        ins = InscriptionService().creer_preinscription(
            apprenant=apprenant, session=session,
            commentaire="Test", cree_par=admin,
        )
        ins = InscriptionService().confirmer_inscription(ins, modifie_par=admin)

        dossier = creer_dossier_autoecole(
            inscription=ins, categorie_permis_id=cat.pk,
            moniteur_referent=moniteur, cree_par=admin,
        )
        assert dossier.statut == StatutDossier.BROUILLON
        dossier = ouvrir_dossier(dossier, modifie_par=admin)
        assert dossier.statut == StatutDossier.OUVERT
        dossier = demarrer_formation_dossier(dossier, modifie_par=admin)
        assert dossier.statut == StatutDossier.EN_FORMATION

        for j in range(3):
            debut = timezone.now() + timedelta(days=j, hours=9)
            lecon = planifier_lecon(
                dossier_id=dossier.pk, moniteur_id=moniteur.pk,
                vehicule_id=vehicule.pk, type_lecon=TypeLecon.CONDUITE,
                date_debut=debut, date_fin=debut + timedelta(hours=1),
                cree_par=admin,
            )
            confirmer_lecon(lecon)
            demarrer_lecon(lecon, kilometrage_depart=1000 + j * 10)
            terminer_lecon(lecon, kilometrage_fin=1000 + (j + 1) * 10)
        for j in range(2):
            debut = timezone.now() + timedelta(days=j, hours=14)
            lecon = planifier_lecon(
                dossier_id=dossier.pk, moniteur_id=moniteur.pk,
                type_lecon=TypeLecon.THEORIE,
                date_debut=debut, date_fin=debut + timedelta(hours=1),
                cree_par=admin,
            )
            confirmer_lecon(lecon)
            demarrer_lecon(lecon)
            terminer_lecon(lecon)

        dossier.refresh_from_db()
        assert dossier.heures_conduite_validees >= 2
        assert dossier.heures_theorie_validees >= 1

        lecons = dossier.lecons.filter(
            statut=StatutLecon.REALISEE, type_lecon=TypeLecon.CONDUITE
        )[:2]
        for lecon in lecons:
            EvaluationLecon.objects.create(
                lecon=lecon, moniteur=moniteur,
                niveau=NiveauEvaluation.ACQUIS,
                recommande_examen=True,
            )

        dossier = declarer_dossier_pret_examen(dossier, modifie_par=admin)
        assert dossier.statut == StatutDossier.PRET_EXAMEN

        examen = planifier_examen(
            dossier_id=dossier.pk, type_examen=TypeExamen.CONDUITE_OFFICIELLE,
            date_examen=timezone.now() + timedelta(days=30),
            cree_par=admin,
        )
        assert examen.statut == StatutExamen.PLANIFIE
        confirmer_examen(examen)
        marquer_candidat_presente(examen)
        enregistrer_resultat_examen(
            examen, resultat=ResultatExamen.ADMIS, score=Decimal("18.00"),
        )
        dossier.refresh_from_db()
        assert dossier.statut == StatutDossier.REUSSI

        dossier = cloturer_dossier(dossier, modifie_par=admin)
        assert dossier.statut == StatutDossier.CLOTURE


class TestMultiEstablishmentIsolation:
    def test_cross_etablissement_dossier_creation(self):
        admin = UserFactory()
        etab1 = EtablissementFactory()
        etab2 = EtablissementFactory()
        cat = CategoriePermisFactory(etablissement=etab2)
        ins = InscriptionFactory(session__etablissement=etab1)
        with pytest.raises(CrossEstablishmentOperationError):
            creer_dossier_autoecole(
                inscription=ins, categorie_permis_id=cat.pk,
                moniteur_referent=None, cree_par=admin,
            )

    def test_cross_etablissement_moniteur_habilitation(self):
        etab1 = EtablissementFactory()
        etab2 = EtablissementFactory()
        moniteur = MoniteurFactory(etablissement=etab1)
        cat_autre = CategoriePermisFactory(etablissement=etab2)
        with pytest.raises(CrossEstablishmentOperationError):
            from django_autoecole.services.moniteurs import ajouter_habilitation_permis
            ajouter_habilitation_permis(moniteur, cat_autre)

    def test_cross_etablissement_vehicule_creation(self):
        etab1 = EtablissementFactory()
        etab2 = EtablissementFactory()
        cat = CategoriePermisFactory(etablissement=etab1)
        with pytest.raises(CrossEstablishmentOperationError):
            creer_vehicule(
                etablissement=etab2, categorie_permis_id=cat.pk,
                immatriculation="XX-001", marque="Test", modele="Test",
            )


class TestDossierTransitions:
    def test_transition_brouillon_to_annule(self):
        dossier = DossierAutoEcoleFactory(statut=StatutDossier.BROUILLON)
        annuler_dossier(dossier)
        assert dossier.statut == StatutDossier.ANNULE

    def test_transition_ouvert_to_formation(self):
        dossier = DossierAutoEcoleFactory(statut=StatutDossier.OUVERT)
        demarrer_formation_dossier(dossier)
        assert dossier.statut == StatutDossier.EN_FORMATION

    def test_transition_suspendu_to_ouvert(self):
        dossier = DossierAutoEcoleFactory(statut=StatutDossier.SUSPENDU)
        from django_autoecole.services.dossiers import reprendre_dossier
        reprendre_dossier(dossier)
        assert dossier.statut == StatutDossier.OUVERT

    def test_transition_formation_to_pret_examen_fails_sans_heures(self):
        dossier = DossierAutoEcoleFactory(statut=StatutDossier.EN_FORMATION)
        with pytest.raises(InsufficientTrainingHoursError):
            declarer_dossier_pret_examen(dossier)

    def test_transition_invalide(self):
        dossier = DossierAutoEcoleFactory(statut=StatutDossier.BROUILLON)
        from django_autoecole.exceptions import InvalidStatusTransitionError
        with pytest.raises(InvalidStatusTransitionError):
            dossier.changer_statut(StatutDossier.REUSSI)


class TestLeconTransitions:
    def test_cycle_complet_lecon(self):
        dossier = DossierAutoEcoleFactory(statut=StatutDossier.EN_FORMATION)
        moniteur = MoniteurFactory(etablissement=dossier.etablissement)
        moniteur.categories_permis.add(dossier.categorie_permis)
        vehicule = VehiculeFactory(
            etablissement=dossier.etablissement,
            categorie_permis=dossier.categorie_permis,
        )
        debut = timezone.now() + timedelta(hours=1)
        lecon = planifier_lecon(
            dossier_id=dossier.pk, moniteur_id=moniteur.pk,
            vehicule_id=vehicule.pk, type_lecon=TypeLecon.CONDUITE,
            date_debut=debut, date_fin=debut + timedelta(hours=1),
            cree_par=None,
        )
        assert lecon.statut == StatutLecon.PLANIFIEE
        confirmer_lecon(lecon)
        assert lecon.statut == StatutLecon.CONFIRMEE
        demarrer_lecon(lecon)
        assert lecon.statut == StatutLecon.EN_COURS
        terminer_lecon(lecon)
        assert lecon.statut == StatutLecon.REALISEE

    def test_annuler_lecon_sans_motif(self):
        dossier = DossierAutoEcoleFactory(statut=StatutDossier.EN_FORMATION)
        moniteur = MoniteurFactory(etablissement=dossier.etablissement)
        moniteur.categories_permis.add(dossier.categorie_permis)
        debut = timezone.now() + timedelta(hours=1)
        lecon = planifier_lecon(
            dossier_id=dossier.pk, moniteur_id=moniteur.pk,
            type_lecon=TypeLecon.THEORIE,
            date_debut=debut, date_fin=debut + timedelta(hours=1),
            cree_par=None,
        )
        with pytest.raises(MissingCancellationReasonError):
            annuler_lecon(lecon, motif="")

    def test_conflit_planning_moniteur(self):
        dossier = DossierAutoEcoleFactory(statut=StatutDossier.EN_FORMATION)
        moniteur = MoniteurFactory(etablissement=dossier.etablissement)
        moniteur.categories_permis.add(dossier.categorie_permis)
        vehicule = VehiculeFactory(
            etablissement=dossier.etablissement,
            categorie_permis=dossier.categorie_permis,
        )
        debut = timezone.now() + timedelta(hours=1)
        planifier_lecon(
            dossier_id=dossier.pk, moniteur_id=moniteur.pk,
            vehicule_id=vehicule.pk, type_lecon=TypeLecon.CONDUITE,
            date_debut=debut, date_fin=debut + timedelta(hours=1),
            cree_par=None,
        )
        with pytest.raises(LessonTimeConflictError):
            planifier_lecon(
                dossier_id=dossier.pk, moniteur_id=moniteur.pk,
                vehicule_id=vehicule.pk, type_lecon=TypeLecon.CONDUITE,
                date_debut=debut, date_fin=debut + timedelta(hours=1),
                cree_par=None,
            )


class TestExamenWorkflow:
    def test_examen_complet_admis(self):
        dossier = DossierAutoEcoleFactory(statut=StatutDossier.PRET_EXAMEN)
        dossier.categorie_permis.heures_conduite_minimum = 1
        dossier.categorie_permis.heures_theorie_minimum = 1
        dossier.categorie_permis.nombre_evaluations_minimum = 0
        dossier.categorie_permis.save()
        dossier.heures_conduite_validees = 2
        dossier.heures_theorie_validees = 2
        dossier.save(update_fields=["heures_conduite_validees", "heures_theorie_validees"])
        dossier.refresh_from_db()
        examen = planifier_examen(
            dossier_id=dossier.pk, type_examen=TypeExamen.CODE_OFFICIEL,
            date_examen=timezone.now() + timedelta(days=30),
            cree_par=None,
        )
        confirmer_examen(examen)
        marquer_candidat_presente(examen)
        enregistrer_resultat_examen(
            examen, resultat=ResultatExamen.ADMIS, score=Decimal("15.00"),
        )
        assert examen.resultat == ResultatExamen.ADMIS
        assert examen.statut == StatutExamen.RESULTAT_DISPONIBLE

    def test_examen_dossier_not_ready(self):
        dossier = DossierAutoEcoleFactory(statut=StatutDossier.BROUILLON)
        with pytest.raises(DossierNotExamReadyError):
            planifier_examen(
                dossier_id=dossier.pk, type_examen=TypeExamen.CODE_OFFICIEL,
                date_examen=timezone.now() + timedelta(days=30),
                cree_par=None,
            )


class TestVehiculeServices:
    def test_cycle_complet_vehicule(self):
        etab = EtablissementFactory()
        cat = CategoriePermisFactory(etablissement=etab)
        v = creer_vehicule(
            etablissement=etab, categorie_permis_id=cat.pk,
            immatriculation="TEST-001", marque="Test", modele="Test",
        )
        assert v.statut == StatutVehicule.DISPONIBLE
        from django_autoecole.services.vehicules import (
            reserver_vehicule, liberer_vehicule,
            mettre_vehicule_en_entretien, remettre_vehicule_disponible,
        )
        reserver_vehicule(v)
        assert v.statut == StatutVehicule.RESERVE
        liberer_vehicule(v)
        assert v.statut == StatutVehicule.DISPONIBLE
        mettre_vehicule_en_entretien(v)
        assert v.statut == StatutVehicule.ENTRETIEN
        remettre_vehicule_disponible(v)
        assert v.statut == StatutVehicule.DISPONIBLE

    def test_mileage_tracking(self):
        etab = EtablissementFactory()
        cat = CategoriePermisFactory(etablissement=etab)
        v = creer_vehicule(
            etablissement=etab, categorie_permis_id=cat.pk,
            immatriculation="TEST-002", marque="Test", modele="Test",
        )
        from django_autoecole.services.vehicules import mettre_a_jour_kilometrage
        mettre_a_jour_kilometrage(v, 1000)
        from django_autoecole.services.vehicules import mettre_a_jour_kilometrage
        with pytest.raises(InvalidMileageError):
            mettre_a_jour_kilometrage(v, 999)
        mettre_a_jour_kilometrage(v, 1100)
        v.refresh_from_db()
        assert v.kilometrage_actuel == 1100


class TestMoniteurServices:
    def test_cycle_complet_moniteur(self):
        etab = EtablissementFactory()
        m = creer_moniteur(
            etablissement=etab, matricule="MON-TEST-001",
            nom="Test", prenom="Moniteur",
        )
        assert m.statut == StatutMoniteur.ACTIF
        from django_autoecole.services.moniteurs import (
            rendre_moniteur_indisponible, activer_moniteur,
            suspendre_moniteur, reactiver_moniteur, archiver_moniteur,
        )
        rendre_moniteur_indisponible(m)
        assert m.statut == StatutMoniteur.INDISPONIBLE
        activer_moniteur(m)
        assert m.statut == StatutMoniteur.ACTIF
        suspendre_moniteur(m)
        assert m.statut == StatutMoniteur.SUSPENDU
        reactiver_moniteur(m)
        assert m.statut == StatutMoniteur.ACTIF
        archiver_moniteur(m)
        assert m.statut == StatutMoniteur.ARCHIVE

    def test_habilitation_permis(self):
        etab = EtablissementFactory()
        m = creer_moniteur(etablissement=etab, matricule="MON-TEST-002", nom="Test", prenom="M")
        cat = CategoriePermisFactory(etablissement=etab)
        from django_autoecole.services.moniteurs import (
            ajouter_habilitation_permis, retirer_habilitation_permis,
        )
        ajouter_habilitation_permis(m, cat)
        assert cat in m.categories_permis.all()
        retirer_habilitation_permis(m, cat)
        assert cat not in m.categories_permis.all()


class TestConfigurationAutoPilotIntegration:
    def test_config_auto_created_by_command(self):
        from django.core.management import call_command
        call_command("setup_demo_autoecole")
        etab = Etablissement.objects.get(code="autopilot-demo")
        config = ConfigurationAutoPilot.objects.get(etablissement=etab)
        assert config.devise == "XOF"
        assert config.duree_lecon_defaut_minutes == 60


class TestJournalAuditIntegration:
    def test_audit_entry_creation(self):
        etab = EtablissementFactory()
        user = UserFactory()
        entry = JournalAuditAutoPilot.objects.create(
            etablissement=etab, utilisateur=user,
            action="DOSSIER_CREE", categorie="DOSSIER",
            entite_type="DossierAutoEcole",
            details={"dossier_numero": "DOS-001"},
        )
        assert entry.pk is not None
        assert entry.action == "DOSSIER_CREE"

    def test_audit_filtering_by_action(self):
        JournalAuditAutoPilot.objects.create(action="ACTION_A")
        JournalAuditAutoPilot.objects.create(action="ACTION_B")
        assert JournalAuditAutoPilot.objects.filter(action="ACTION_A").count() == 1


class TestErrorResponses:
    def test_formation_domain_error_message(self):
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework.views import APIView
        from rest_framework.response import Response
        from django.urls import path
        factory = APIRequestFactory()

        class ErrorView(APIView):
            def get(self, request):
                raise FormationDomainError("Erreur formation")

        from apps.core.api.exceptions import autopilot_exception_handler
        request = factory.get("/test/")
        request.user = UserFactory()
        view = ErrorView.as_view()
        try:
            view(request)
        except FormationDomainError as e:
            response = autopilot_exception_handler(e, {"view": None, "request": request})
            assert response.status_code == 400
            assert "Erreur formation" in str(response.data["message"])
