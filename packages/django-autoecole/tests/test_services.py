import pytest
from datetime import timedelta
from django.utils import timezone
from django_autoecole.constants import StatutMoniteur, StatutVehicule
from django_autoecole.exceptions import (
    AutoEcoleDomainError,
    InvalidStatusTransitionError,
    VehicleUnavailableError,
    InstructorUnavailableError,
    DossierNotExamReadyError,
)
from factories import (
    DossierAutoEcoleFactory,
    MoniteurFactory,
    VehiculeFactory,
    LeconConduiteFactory,
    ExamenAutoEcoleFactory,
    CategoriePermisFactory,
    InscriptionFactory,
    EtablissementFactory,
)


pytestmark = pytest.mark.django_db


def _prepare_dossier_pret_examen():
    """Create a dossier ready for exam with all requirements met."""
    dossier = DossierAutoEcoleFactory(
        statut="EN_FORMATION",
        heures_conduite_validees=20,
        heures_theorie_validees=10,
        categorie_permis__heures_conduite_minimum=20,
        categorie_permis__heures_theorie_minimum=10,
        categorie_permis__nombre_evaluations_minimum=1,
    )
    from django_autoecole.models import LeconConduite
    for i in range(3):
        debut = timezone.now() - timedelta(days=30 - i)
        lecon = LeconConduite.objects.create(
            dossier=dossier,
            type_lecon="CONDUITE",
            statut="REALISEE",
            duree_minutes=60,
            date_debut=debut,
            date_fin=debut + timedelta(minutes=60),
            etablissement=dossier.etablissement,
            moniteur=MoniteurFactory(etablissement=dossier.etablissement),
            vehicule=VehiculeFactory(etablissement=dossier.etablissement),
            realisee_le=timezone.now(),
            kilometrage_depart=1000,
            kilometrage_fin=1018,
        )
        from django_autoecole.models import EvaluationLecon
        EvaluationLecon.objects.create(
            lecon=lecon,
            moniteur=MoniteurFactory(etablissement=dossier.etablissement),
            note_globale=14,
            niveau="EXCELLENT",
            recommande_examen=True,
        )
    dossier.heures_conduite_validees = 20
    dossier.save(update_fields=["heures_conduite_validees"])
    return dossier


class TestServiceDossiers:
    def test_creer_dossier(self, db):
        from django_autoecole.services.dossiers import creer_dossier_autoecole
        etab = EtablissementFactory()
        cat = CategoriePermisFactory(etablissement=etab)
        inscription = InscriptionFactory(etablissement=etab)
        dossier = creer_dossier_autoecole(
            inscription=inscription,
            categorie_permis_id=cat.id,
        )
        assert dossier.statut == "BROUILLON"
        assert dossier.inscription == inscription

    def test_ouvrir_dossier(self, db):
        from django_autoecole.services.dossiers import ouvrir_dossier
        dossier = DossierAutoEcoleFactory(statut="BROUILLON")
        ouvrir_dossier(dossier)
        assert dossier.statut == "OUVERT"

    def test_ouvrir_dossier_deja_ouvert(self, db):
        from django_autoecole.services.dossiers import ouvrir_dossier
        dossier = DossierAutoEcoleFactory(statut="OUVERT")
        with pytest.raises(InvalidStatusTransitionError):
            ouvrir_dossier(dossier)

    def test_demarrer_formation(self, db):
        from django_autoecole.services.dossiers import demarrer_formation_dossier
        dossier = DossierAutoEcoleFactory(statut="OUVERT")
        demarrer_formation_dossier(dossier)
        assert dossier.statut == "EN_FORMATION"

    def test_suspendre_dossier(self, db):
        from django_autoecole.services.dossiers import suspendre_dossier
        dossier = DossierAutoEcoleFactory(statut="EN_FORMATION")
        suspendre_dossier(dossier, commentaire="Absence prolongée")
        assert dossier.statut == "SUSPENDU"

    def test_reprendre_dossier(self, db):
        from django_autoecole.services.dossiers import reprendre_dossier
        dossier = DossierAutoEcoleFactory(statut="SUSPENDU")
        reprendre_dossier(dossier)
        assert dossier.statut == "OUVERT"

    def test_declarer_pret_examen(self, db):
        from django_autoecole.services.dossiers import declarer_dossier_pret_examen
        dossier = _prepare_dossier_pret_examen()
        declarer_dossier_pret_examen(dossier)
        assert dossier.statut == "PRET_EXAMEN"

    def test_annuler_dossier(self, db):
        from django_autoecole.services.dossiers import annuler_dossier
        dossier = DossierAutoEcoleFactory(statut="OUVERT")
        annuler_dossier(dossier, commentaire="Abandon")
        assert dossier.statut == "ANNULE"

    def test_cloturer_dossier(self, db):
        from django_autoecole.services.dossiers import cloturer_dossier
        dossier = DossierAutoEcoleFactory(statut="REUSSI")
        cloturer_dossier(dossier)
        assert dossier.statut == "CLOTURE"

    def test_cloturer_sans_reussite(self, db):
        from django_autoecole.services.dossiers import cloturer_dossier
        dossier = DossierAutoEcoleFactory(statut="OUVERT")
        with pytest.raises(InvalidStatusTransitionError):
            cloturer_dossier(dossier)

    def test_marquer_reussi(self, db):
        from django_autoecole.services.dossiers import marquer_dossier_reussi
        dossier = DossierAutoEcoleFactory(statut="PRESENTE_EXAMEN")
        marquer_dossier_reussi(dossier)
        assert dossier.statut == "REUSSI"

    def test_marquer_echoue(self, db):
        from django_autoecole.services.dossiers import marquer_dossier_echoue
        dossier = DossierAutoEcoleFactory(statut="PRESENTE_EXAMEN")
        marquer_dossier_echoue(dossier)
        assert dossier.statut == "ECHOUE"

    def test_affecter_moniteur_referent(self, db):
        from django_autoecole.services.dossiers import affecter_moniteur_referent
        dossier = DossierAutoEcoleFactory(statut="OUVERT")
        moniteur = MoniteurFactory(etablissement=dossier.etablissement)
        moniteur.categories_permis.add(dossier.categorie_permis)
        affecter_moniteur_referent(dossier, moniteur)
        dossier.refresh_from_db()
        assert dossier.moniteur_referent == moniteur


class TestServiceLecons:
    def test_planifier_lecon(self, db):
        from django_autoecole.services.lecons import planifier_lecon
        dossier = DossierAutoEcoleFactory(statut="EN_FORMATION")
        moniteur = MoniteurFactory(etablissement=dossier.etablissement)
        moniteur.categories_permis.add(dossier.categorie_permis)
        vehicule = VehiculeFactory(
            etablissement=dossier.etablissement,
            categorie_permis=dossier.categorie_permis,
        )
        date_debut = timezone.now() + timedelta(days=1)
        lecon = planifier_lecon(
            dossier_id=dossier.id,
            moniteur_id=moniteur.id,
            vehicule_id=vehicule.id,
            type_lecon="CONDUITE",
            date_debut=date_debut,
            date_fin=date_debut + timedelta(minutes=60),
        )
        assert lecon.statut == "PLANIFIEE"
        assert lecon.duree_minutes == 60

    def test_planifier_sans_dossier_ouvert(self, db):
        from django_autoecole.services.lecons import planifier_lecon
        dossier = DossierAutoEcoleFactory(statut="BROUILLON")
        moniteur = MoniteurFactory(etablissement=dossier.etablissement)
        moniteur.categories_permis.add(dossier.categorie_permis)
        vehicule = VehiculeFactory(etablissement=dossier.etablissement)
        date_debut = timezone.now() + timedelta(days=1)
        with pytest.raises(AutoEcoleDomainError):
            planifier_lecon(
                dossier_id=dossier.id,
                moniteur_id=moniteur.id,
                vehicule_id=vehicule.id,
                type_lecon="CONDUITE",
                date_debut=date_debut,
                date_fin=date_debut + timedelta(minutes=60),
            )

    def test_planifier_vehicule_indisponible(self, db):
        from django_autoecole.services.lecons import planifier_lecon
        dossier = DossierAutoEcoleFactory(statut="EN_FORMATION")
        moniteur = MoniteurFactory(etablissement=dossier.etablissement)
        moniteur.categories_permis.add(dossier.categorie_permis)
        vehicule = VehiculeFactory(
            etablissement=dossier.etablissement,
            categorie_permis=dossier.categorie_permis,
            statut=StatutVehicule.ENTRETIEN,
        )
        date_debut = timezone.now() + timedelta(days=1)
        with pytest.raises(VehicleUnavailableError):
            planifier_lecon(
                dossier_id=dossier.id,
                moniteur_id=moniteur.id,
                vehicule_id=vehicule.id,
                type_lecon="CONDUITE",
                date_debut=date_debut,
                date_fin=date_debut + timedelta(minutes=60),
            )

    def test_planifier_moniteur_indisponible(self, db):
        from django_autoecole.services.lecons import planifier_lecon
        dossier = DossierAutoEcoleFactory(statut="EN_FORMATION")
        moniteur = MoniteurFactory(
            etablissement=dossier.etablissement,
            statut=StatutMoniteur.SUSPENDU,
        )
        moniteur.categories_permis.add(dossier.categorie_permis)
        vehicule = VehiculeFactory(etablissement=dossier.etablissement)
        date_debut = timezone.now() + timedelta(days=1)
        with pytest.raises(InstructorUnavailableError):
            planifier_lecon(
                dossier_id=dossier.id,
                moniteur_id=moniteur.id,
                vehicule_id=vehicule.id,
                type_lecon="CONDUITE",
                date_debut=date_debut,
                date_fin=date_debut + timedelta(minutes=60),
            )

    def test_confirmer_lecon(self, db):
        from django_autoecole.services.lecons import confirmer_lecon
        lecon = LeconConduiteFactory(statut="PLANIFIEE")
        confirmer_lecon(lecon)
        assert lecon.statut == "CONFIRMEE"

    def test_demarrer_lecon(self, db):
        from django_autoecole.services.lecons import demarrer_lecon
        lecon = LeconConduiteFactory(statut="CONFIRMEE", kilometrage_depart=1000)
        demarrer_lecon(lecon, kilometrage_depart=1000)
        assert lecon.statut == "EN_COURS"

    def test_terminer_lecon(self, db):
        from django_autoecole.services.lecons import terminer_lecon
        lecon = LeconConduiteFactory(
            statut="EN_COURS",
            kilometrage_depart=1000,
            dossier__statut="EN_FORMATION",
        )
        terminer_lecon(
            lecon,
            kilometrage_fin=1018,
            observation="Bonne progression",
        )
        assert lecon.statut == "REALISEE"
        assert lecon.kilometrage_fin == 1018
        lecon.dossier.refresh_from_db()
        assert lecon.dossier.heures_conduite_validees == lecon.duree_minutes // 60

    def test_annuler_lecon(self, db):
        from django_autoecole.services.lecons import annuler_lecon
        lecon = LeconConduiteFactory(statut="PLANIFIEE")
        annuler_lecon(lecon, motif="Intempéries")
        assert lecon.statut == "ANNULEE"

    def test_reporter_lecon(self, db):
        from django_autoecole.services.lecons import reporter_lecon
        lecon = LeconConduiteFactory(statut="PLANIFIEE")
        nouvelle_date = lecon.date_debut + timedelta(days=3)
        reporter_lecon(lecon, nouvelle_date_debut=nouvelle_date, nouvelle_date_fin=nouvelle_date + timedelta(minutes=60))
        assert lecon.statut == "REPORTEE"

    def test_absence_candidat(self, db):
        from django_autoecole.services.lecons import marquer_absence_candidat
        lecon = LeconConduiteFactory(statut="CONFIRMEE")
        marquer_absence_candidat(lecon, observation="Maladie")
        assert lecon.statut == "ABSENT_CANDIDAT"

    def test_absence_moniteur(self, db):
        from django_autoecole.services.lecons import marquer_absence_moniteur
        lecon = LeconConduiteFactory(statut="CONFIRMEE")
        marquer_absence_moniteur(lecon, observation="Urgence")
        assert lecon.statut == "ABSENT_MONITEUR"


class TestServiceExamens:
    def test_planifier_examen(self, db):
        from django_autoecole.services.examens import planifier_examen
        dossier = _prepare_dossier_pret_examen()
        from django_autoecole.services.dossiers import declarer_dossier_pret_examen
        declarer_dossier_pret_examen(dossier)
        examen = planifier_examen(
            dossier_id=dossier.id,
            type_examen="CONDUITE_OFFICIELLE",
            date_examen=timezone.now() + timedelta(days=15),
        )
        assert examen.statut == "PLANIFIE"

    def test_planifier_examen_heures_insuffisantes(self, db):
        from django_autoecole.services.examens import planifier_examen
        dossier = DossierAutoEcoleFactory(
            statut="EN_FORMATION",
            heures_conduite_validees=5,
            categorie_permis__heures_conduite_minimum=20,
        )
        with pytest.raises(DossierNotExamReadyError):
            planifier_examen(
                dossier_id=dossier.id,
                type_examen="CONDUITE_OFFICIELLE",
                date_examen=timezone.now() + timedelta(days=15),
            )

    def test_confirmer_examen(self, db):
        from django_autoecole.services.examens import confirmer_examen
        examen = ExamenAutoEcoleFactory(statut="PLANIFIE")
        confirmer_examen(examen)
        assert examen.statut == "CONFIRME"

    def test_enregistrer_resultat_admis(self, db):
        from django_autoecole.services.examens import enregistrer_resultat_examen
        examen = ExamenAutoEcoleFactory(statut="CONFIRME", dossier__statut="PRESENTE_EXAMEN")
        enregistrer_resultat_examen(examen, resultat="ADMIS")
        assert examen.resultat == "ADMIS"
        assert examen.statut == "RESULTAT_DISPONIBLE"

    def test_enregistrer_resultat_ajourne(self, db):
        from django_autoecole.services.examens import enregistrer_resultat_examen
        examen = ExamenAutoEcoleFactory(statut="CONFIRME", dossier__statut="PRESENTE_EXAMEN")
        enregistrer_resultat_examen(examen, resultat="AJOURNE")
        assert examen.resultat == "AJOURNE"

    def test_annuler_examen(self, db):
        from django_autoecole.services.examens import annuler_examen
        examen = ExamenAutoEcoleFactory(statut="PLANIFIE")
        annuler_examen(examen)
        assert examen.statut == "ANNULE"

    def test_marquer_present(self, db):
        from django_autoecole.services.examens import marquer_candidat_presente
        examen = ExamenAutoEcoleFactory(statut="CONFIRME")
        marquer_candidat_presente(examen)
        assert examen.statut == "PRESENTE"

    def test_marquer_absent(self, db):
        from django_autoecole.services.examens import marquer_candidat_absent
        examen = ExamenAutoEcoleFactory(statut="CONFIRME")
        marquer_candidat_absent(examen)
        assert examen.statut == "ABSENT"


class TestSelecteurs:
    def test_verifier_disponibilites(self, db):
        from django_autoecole.selectors import verifier_disponibilites
        dossier = DossierAutoEcoleFactory(statut="EN_FORMATION")
        moniteur = MoniteurFactory(etablissement=dossier.etablissement)
        vehicule = VehiculeFactory(etablissement=dossier.etablissement)
        creneau_debut = timezone.now() + timedelta(days=1)
        creneau_fin = creneau_debut + timedelta(hours=2)
        resultat = verifier_disponibilites(
            moniteur_id=moniteur.id,
            vehicule_id=vehicule.id,
            date_debut=creneau_debut,
            date_fin=creneau_fin,
        )
        assert resultat["moniteur"] is False
        assert resultat["vehicule"] is False
