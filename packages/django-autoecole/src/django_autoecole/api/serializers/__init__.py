from rest_framework import serializers
from django_autoecole.models import (
    CategoriePermis, Moniteur, Vehicule, DossierAutoEcole,
    LeconConduite, EvaluationLecon, ExamenAutoEcole,
    IndisponibiliteMoniteur, IndisponibiliteVehicule, HistoriqueStatutDossier,
)
from django_autoecole.constants import DOSSIER_TRANSITIONS, LECON_TRANSITIONS
from django_autoecole.services.dossiers import creer_dossier_autoecole
from django_autoecole.services.lecons import planifier_lecon
from django_autoecole.services.moniteurs import creer_moniteur
from django_autoecole.services.vehicules import creer_vehicule
from django_autoecole.services.examens import planifier_examen


class CategoriePermisSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriePermis
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class MoniteurListSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()
    categories_permis = serializers.SlugRelatedField(slug_field="code", many=True, read_only=True)

    class Meta:
        model = Moniteur
        fields = ["id", "matricule", "nom_complet", "telephone", "statut", "categories_permis", "date_embauche"]


class MoniteurDetailSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()

    class Meta:
        model = Moniteur
        fields = "__all__"
        read_only_fields = ["id", "statut", "created_at", "updated_at"]


class VehiculeListSerializer(serializers.ModelSerializer):
    categorie_permis_code = serializers.CharField(source="categorie_permis.code", read_only=True)
    documents_en_ordre = serializers.ReadOnlyField()

    class Meta:
        model = Vehicule
        fields = ["id", "immatriculation", "marque", "modele", "categorie_permis_code", "kilometrage_actuel", "statut", "documents_en_ordre"]


class VehiculeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicule
        fields = "__all__"
        read_only_fields = ["id", "statut", "kilometrage_actuel", "created_at", "updated_at"]


class DossierAutoEcoleListSerializer(serializers.ModelSerializer):
    apprenant_nom = serializers.SerializerMethodField()
    categorie_permis_code = serializers.CharField(source="categorie_permis.code", read_only=True)
    progression = serializers.ReadOnlyField(source="progression_conduite")

    class Meta:
        model = DossierAutoEcole
        fields = ["id", "numero_dossier", "apprenant_nom", "categorie_permis_code", "statut", "date_ouverture", "progression"]

    def get_apprenant_nom(self, obj):
        return str(obj.inscription.apprenant)


class DossierAutoEcoleDetailSerializer(serializers.ModelSerializer):
    apprenant_nom = serializers.SerializerMethodField()
    transitions = serializers.SerializerMethodField()
    peut_etre_presente_examen = serializers.ReadOnlyField()
    progression_conduite = serializers.ReadOnlyField()

    class Meta:
        model = DossierAutoEcole
        fields = "__all__"
        read_only_fields = [
            "id", "statut", "heures_theorie_validees", "heures_conduite_validees",
            "pret_examen_le", "cloture_le", "created_at", "updated_at",
        ]

    def get_apprenant_nom(self, obj):
        return str(obj.inscription.apprenant)

    def get_transitions(self, obj):
        return DOSSIER_TRANSITIONS.get(obj.statut, [])


class LeconConduiteListSerializer(serializers.ModelSerializer):
    dossier_numero = serializers.CharField(source="dossier.numero_dossier", read_only=True)
    moniteur_nom = serializers.CharField(source="moniteur.nom_complet", read_only=True)
    vehicule_immatriculation = serializers.CharField(source="vehicule.immatriculation", read_only=True, allow_null=True)
    type_lecon_display = serializers.CharField(source="get_type_lecon_display", read_only=True)
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)

    class Meta:
        model = LeconConduite
        fields = ["id", "dossier_numero", "moniteur_nom", "vehicule_immatriculation",
                   "type_lecon", "type_lecon_display", "date_debut", "date_fin",
                   "duree_minutes", "statut", "statut_display"]


class LeconConduiteDetailSerializer(serializers.ModelSerializer):
    transitions = serializers.SerializerMethodField()

    class Meta:
        model = LeconConduite
        fields = "__all__"
        read_only_fields = [
            "id", "statut", "duree_minutes", "kilometrage_fin", "realisee_le",
            "created_at", "updated_at",
        ]

    def get_transitions(self, obj):
        return LECON_TRANSITIONS.get(obj.statut, [])


class EvaluationLeconSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationLecon
        fields = "__all__"
        read_only_fields = ["id", "statut", "resultat", "resultat_enregistre_le", "created_at", "updated_at"]


class ExamenAutoEcoleListSerializer(serializers.ModelSerializer):
    dossier_numero = serializers.CharField(source="dossier.numero_dossier", read_only=True)
    apprenant_nom = serializers.SerializerMethodField()
    type_examen_display = serializers.CharField(source="get_type_examen_display", read_only=True)

    class Meta:
        model = ExamenAutoEcole
        fields = ["id", "dossier_numero", "apprenant_nom", "type_examen", "type_examen_display",
                   "date_examen", "statut", "resultat"]

    def get_apprenant_nom(self, obj):
        return str(obj.dossier.inscription.apprenant)


class ExamenAutoEcoleDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamenAutoEcole
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class IndisponibiliteMoniteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndisponibiliteMoniteur
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class IndisponibiliteVehiculeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndisponibiliteVehicule
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class HistoriqueStatutDossierSerializer(serializers.ModelSerializer):
    modifie_par_nom = serializers.SerializerMethodField()

    class Meta:
        model = HistoriqueStatutDossier
        fields = "__all__"

    def get_modifie_par_nom(self, obj):
        if obj.modifie_par:
            return str(obj.modifie_par)
        return ""


# ── Serializers d'action ──

class CreerDossierSerializer(serializers.Serializer):
    inscription_id = serializers.UUIDField()
    categorie_permis_id = serializers.UUIDField()
    numero_dossier = serializers.CharField(required=False, allow_blank=True)
    moniteur_referent_id = serializers.UUIDField(required=False, allow_null=True)
    observation = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        from django_formation.models import Inscription
        return creer_dossier_autoecole(
            inscription=Inscription.objects.select_related("session").get(
                pk=self.validated_data["inscription_id"]
            ),
            categorie_permis_id=self.validated_data["categorie_permis_id"],
            numero_dossier=self.validated_data.get("numero_dossier") or None,
            moniteur_referent_id=self.validated_data.get("moniteur_referent_id"),
            cree_par=self.context.get("request").user if "request" in self.context else None,
        )


class PlanifierLeconSerializer(serializers.Serializer):
    dossier_id = serializers.UUIDField()
    moniteur_id = serializers.UUIDField()
    vehicule_id = serializers.UUIDField(required=False, allow_null=True)
    type_lecon = serializers.ChoiceField(choices=LeconConduite._meta.get_field("type_lecon").choices)
    date_debut = serializers.DateTimeField()
    date_fin = serializers.DateTimeField()
    lieu_depart = serializers.CharField(required=False, allow_blank=True)
    lieu_arrivee = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        return planifier_lecon(**self.validated_data)


class CreerMoniteurSerializer(serializers.Serializer):
    etablissement_id = serializers.UUIDField()
    matricule = serializers.CharField()
    nom = serializers.CharField()
    prenom = serializers.CharField()
    telephone = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    numero_agrement = serializers.CharField(required=False, allow_blank=True)
    date_embauche = serializers.DateField(required=False, allow_null=True)

    def save(self, **kwargs):
        from django_formation.models import Etablissement
        data = self.validated_data.copy()
        data["etablissement"] = Etablissement.objects.get(pk=data.pop("etablissement_id"))
        return creer_moniteur(**data)


class CreerVehiculeSerializer(serializers.Serializer):
    etablissement_id = serializers.UUIDField()
    categorie_permis_id = serializers.UUIDField()
    immatriculation = serializers.CharField()
    marque = serializers.CharField()
    modele = serializers.CharField()
    annee = serializers.IntegerField(required=False, allow_null=True)
    couleur = serializers.CharField(required=False, allow_blank=True)
    type_boite = serializers.ChoiceField(choices=Vehicule._meta.get_field("type_boite").choices)
    type_carburant = serializers.CharField(required=False, allow_blank=True)
    kilometrage = serializers.IntegerField(default=0)

    def save(self, **kwargs):
        from django_formation.models import Etablissement
        data = self.validated_data.copy()
        data["etablissement"] = Etablissement.objects.get(pk=data.pop("etablissement_id"))
        return creer_vehicule(**data)


class PlanifierExamenSerializer(serializers.Serializer):
    dossier_id = serializers.UUIDField()
    type_examen = serializers.ChoiceField(choices=ExamenAutoEcole._meta.get_field("type_examen").choices)
    date_examen = serializers.DateTimeField()
    centre_examen = serializers.CharField(required=False, allow_blank=True)
    numero_convocation = serializers.CharField(required=False, allow_blank=True)
    observation = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        return planifier_examen(**self.validated_data)


class TerminerLeconSerializer(serializers.Serializer):
    kilometrage_fin = serializers.IntegerField(required=False, allow_null=True)
    observation = serializers.CharField(required=False, allow_blank=True)


class AnnulerLeconSerializer(serializers.Serializer):
    motif = serializers.CharField()
    observation = serializers.CharField(required=False, allow_blank=True)


class ReporterLeconSerializer(serializers.Serializer):
    date_debut = serializers.DateTimeField()
    date_fin = serializers.DateTimeField()


class EnregistrerResultatExamenSerializer(serializers.Serializer):
    resultat = serializers.ChoiceField(choices=ExamenAutoEcole._meta.get_field("resultat").choices)
    score = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)
    observation = serializers.CharField(required=False, allow_blank=True)
