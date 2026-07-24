import factory
from django.contrib.auth.models import User
from django_formation.models.etablissement import Etablissement
from django_formation.models.membre import MembreEtablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_autoecole.models import CategoriePermis, Moniteur, Vehicule, DossierAutoEcole, LeconConduite, ExamenAutoEcole, EvaluationLecon
from django_autoecole.constants import StatutDossier, StatutLecon, StatutExamen, ResultatExamen, TypeLecon, TypeExamen, TypeBoite, TypeCarburant, NiveauEvaluation, StatutMoniteur, StatutVehicule
from apps.core.models import ConfigurationAutoPilot, JournalAuditAutoPilot
from datetime import date, timedelta
from django.utils import timezone


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True
    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall("set_password", "pass123")


class EtablissementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Etablissement
    code = factory.Sequence(lambda n: f"etab-{n:04d}")
    nom = factory.Sequence(lambda n: f"Auto-Ecole {n}")
    ville = "Bamako"
    pays = "Mali"


class MembreEtablissementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MembreEtablissement
    etablissement = factory.SubFactory(EtablissementFactory)
    utilisateur = factory.SubFactory(UserFactory)
    role = "PROPRIETAIRE"


class ApprenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Apprenant
    etablissement = factory.SubFactory(EtablissementFactory)
    nom = factory.Sequence(lambda n: f"Nom{n}")
    prenom = factory.Sequence(lambda n: f"Prenom{n}")
    telephone = factory.Sequence(lambda n: f"+223 70 {n:02d} 00 00")
    email = factory.LazyAttribute(lambda o: f"{o.prenom}.{o.nom}@email.com".lower())


class FormationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Formation
    etablissement = factory.SubFactory(EtablissementFactory)
    code = factory.Sequence(lambda n: f"CODE-{n:04d}")
    nom = factory.Sequence(lambda n: f"Formation {n}")
    duree_heures = 240
    duree_jours = 30
    tarif_indicatif = 150000


class SessionFormationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SessionFormation
    etablissement = factory.SubFactory(EtablissementFactory)
    formation = factory.SubFactory(FormationFactory)
    code = factory.Sequence(lambda n: f"SESS-{n:04d}")
    nom = factory.Sequence(lambda n: f"Session {n}")
    date_debut = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    capacite = 20


class InscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Inscription
    apprenant = factory.SubFactory(ApprenantFactory)
    session = factory.SubFactory(SessionFormationFactory)
    etablissement = factory.LazyAttribute(lambda o: o.session.etablissement)
    statut = "CONFIRMEE"
    date_inscription = factory.LazyFunction(lambda: date.today())
    numero = factory.Sequence(lambda n: f"INS-{n:06d}")
    commentaire = ""


class CategoriePermisFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CategoriePermis
    etablissement = factory.SubFactory(EtablissementFactory)
    code = factory.Sequence(lambda n: f"CAT-{n}")
    nom = factory.Sequence(lambda n: f"Categorie {n}")
    heures_theorie_minimum = 12
    heures_conduite_minimum = 20
    nombre_evaluations_minimum = 4


class MoniteurFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Moniteur
    etablissement = factory.SubFactory(EtablissementFactory)
    matricule = factory.Sequence(lambda n: f"MON-{n:04d}")
    nom = factory.Sequence(lambda n: f"MoniteurNom{n}")
    prenom = factory.Sequence(lambda n: f"MoniteurPrenom{n}")
    statut = StatutMoniteur.ACTIF


class VehiculeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vehicule
    etablissement = factory.SubFactory(EtablissementFactory)
    categorie_permis = factory.SubFactory(CategoriePermisFactory)
    immatriculation = factory.Sequence(lambda n: f"AA-{n:03d}-B")
    marque = "Toyota"
    modele = "Yaris"
    type_boite = TypeBoite.MANUELLE
    type_carburant = TypeCarburant.ESSENCE
    statut = StatutVehicule.DISPONIBLE


class DossierAutoEcoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DossierAutoEcole
    etablissement = factory.SubFactory(EtablissementFactory)
    inscription = factory.SubFactory(InscriptionFactory)
    categorie_permis = factory.SubFactory(CategoriePermisFactory)
    numero_dossier = factory.Sequence(lambda n: f"DOS-{n:06d}")
    date_ouverture = factory.LazyFunction(lambda: date.today())
    statut = StatutDossier.OUVERT


class LeconConduiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LeconConduite
    etablissement = factory.SubFactory(EtablissementFactory)
    dossier = factory.SubFactory(DossierAutoEcoleFactory)
    moniteur = factory.SubFactory(MoniteurFactory)
    type_lecon = TypeLecon.CONDUITE
    date_debut = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=1))
    date_fin = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=2))
    duree_minutes = 60
    statut = StatutLecon.PLANIFIEE


class ExamenAutoEcoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExamenAutoEcole
    etablissement = factory.SubFactory(EtablissementFactory)
    dossier = factory.SubFactory(DossierAutoEcoleFactory)
    type_examen = TypeExamen.CONDUITE_OFFICIELLE
    date_examen = factory.LazyFunction(lambda: timezone.now() + timedelta(days=30))
    statut = StatutExamen.PLANIFIE


class ConfigurationAutoPilotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConfigurationAutoPilot
    etablissement = factory.SubFactory(EtablissementFactory)
    devise = "XOF"
    fuseau_horaire = "Africa/Bamako"
