import factory
from datetime import date, timedelta
from django.utils import timezone


# Factories pour les modèles formation (nécessaires pour les relations)

class EtablissementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_formation.Etablissement"
        django_get_or_create = ["code"]

    code = factory.Sequence(lambda n: f"AE-{n:03d}")
    nom = "Auto-École Test"
    actif = True


class ApprenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_formation.Apprenant"

    nom = "DIARRA"
    prenom = "Mamadou"
    matricule = factory.Sequence(lambda n: f"APP-{n:06d}")
    email = factory.Sequence(lambda n: f"apprenant{n}@test.com")
    telephone = "70000000"
    etablissement = factory.SubFactory(EtablissementFactory)
    statut = "ACTIF"


class FormationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_formation.Formation"

    nom = "Permis B"
    code = factory.Sequence(lambda n: f"PERMIS-{n}")
    etablissement = factory.SubFactory(EtablissementFactory)
    statut = "PUBLIEE"


class SessionFormationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_formation.SessionFormation"

    code = factory.Sequence(lambda n: f"SESS-{n}")
    date_debut = date.today()
    date_fin = date.today() + timedelta(days=90)
    etablissement = factory.SubFactory(EtablissementFactory)
    formation = factory.SubFactory(FormationFactory, etablissement=factory.SelfAttribute("..etablissement"))
    statut = "INSCRIPTIONS_OUVERTES"


class InscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_formation.Inscription"

    numero = factory.Sequence(lambda n: f"INS-{n:06d}")
    statut = "CONFIRMEE"
    date_inscription = date.today()
    etablissement = factory.SubFactory(EtablissementFactory)
    apprenant = factory.SubFactory(ApprenantFactory, etablissement=factory.SelfAttribute("..etablissement"))
    session = factory.SubFactory(SessionFormationFactory, etablissement=factory.SelfAttribute("..etablissement"))


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "auth.User"

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.com")


# Factories Auto-école

class CategoriePermisFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_autoecole.CategoriePermis"

    code = factory.Sequence(lambda n: f"B-{n}")
    nom = "Permis B"
    age_minimum = 18
    heures_theorie_minimum = 10
    heures_conduite_minimum = 20
    nombre_evaluations_minimum = 3
    actif = True
    etablissement = factory.SubFactory(EtablissementFactory)


class MoniteurFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_autoecole.Moniteur"

    matricule = factory.Sequence(lambda n: f"MON-2026-{n:06d}")
    nom = "TRAORE"
    prenom = "Moussa"
    telephone = "71000000"
    numero_agrement = "AGR-001"
    statut = "ACTIF"
    etablissement = factory.SubFactory(EtablissementFactory)

    @factory.post_generation
    def categories_permis(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.categories_permis.add(*extracted)
        else:
            self.categories_permis.add(CategoriePermisFactory())


class VehiculeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_autoecole.Vehicule"

    immatriculation = factory.Sequence(lambda n: f"AB-{n:04d}-CD")
    marque = "Toyota"
    modele = "Yaris"
    type_boite = "MANUELLE"
    kilometrage_actuel = 125000
    statut = "DISPONIBLE"
    date_expiration_assurance = factory.LazyFunction(lambda: date.today() + timedelta(days=365))
    date_expiration_visite_technique = factory.LazyFunction(lambda: date.today() + timedelta(days=365))
    etablissement = factory.SubFactory(EtablissementFactory)
    categorie_permis = factory.SubFactory(CategoriePermisFactory, etablissement=factory.SelfAttribute("..etablissement"))


class DossierAutoEcoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_autoecole.DossierAutoEcole"

    numero_dossier = factory.Sequence(lambda n: f"AE-2026-{n:06d}")
    date_ouverture = factory.LazyFunction(date.today)
    statut = "BROUILLON"
    heures_theorie_validees = 0
    heures_conduite_validees = 0
    etablissement = factory.SubFactory(EtablissementFactory)
    categorie_permis = factory.SubFactory(CategoriePermisFactory, etablissement=factory.SelfAttribute("..etablissement"))

    @factory.lazy_attribute
    def inscription(self):
        etab = self.etablissement
        apprenant = ApprenantFactory(etablissement=etab)
        formation = FormationFactory(etablissement=etab)
        session = SessionFormationFactory(
            etablissement=etab,
            formation=formation,
        )
        return InscriptionFactory(
            session=session,
            apprenant=apprenant,
            etablissement=etab,
        )


class LeconConduiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_autoecole.LeconConduite"

    type_lecon = "CONDUITE"
    duree_minutes = 60
    statut = "PLANIFIEE"
    dossier = factory.SubFactory(DossierAutoEcoleFactory)
    date_debut = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1))
    date_fin = factory.LazyAttribute(lambda o: o.date_debut + timedelta(minutes=60))

    @factory.lazy_attribute
    def etablissement(self):
        return self.dossier.etablissement

    @factory.lazy_attribute
    def moniteur(self):
        return MoniteurFactory(etablissement=self.dossier.etablissement)

    @factory.lazy_attribute
    def vehicule(self):
        return VehiculeFactory(
            etablissement=self.dossier.etablissement,
            categorie_permis=self.dossier.categorie_permis,
        )


class LeconConduiteRealiseeFactory(LeconConduiteFactory):
    statut = "REALISEE"
    realisee_le = factory.LazyFunction(timezone.now)
    kilometrage_depart = 1000
    kilometrage_fin = 1018

    @factory.lazy_attribute
    def dossier(self):
        return DossierAutoEcoleFactory(statut="EN_FORMATION")


class ExamenAutoEcoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_autoecole.ExamenAutoEcole"

    type_examen = "CONDUITE_OFFICIELLE"
    statut = "BROUILLON"
    resultat = "EN_ATTENTE"
    dossier = factory.SubFactory(DossierAutoEcoleFactory)
    date_examen = factory.LazyFunction(lambda: timezone.now() + timedelta(days=30))

    @factory.lazy_attribute
    def etablissement(self):
        return self.dossier.etablissement


class IndisponibiliteMoniteurFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_autoecole.IndisponibiliteMoniteur"

    motif = "Congés"
    statut = "ACTIVE"
    date_debut = factory.LazyFunction(timezone.now)
    date_fin = factory.LazyAttribute(lambda o: o.date_debut + timedelta(days=3))


class IndisponibiliteVehiculeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "django_autoecole.IndisponibiliteVehicule"

    motif = "Entretien"
    statut = "ACTIVE"
    date_debut = factory.LazyFunction(timezone.now)
    date_fin = factory.LazyAttribute(lambda o: o.date_debut + timedelta(days=1))
