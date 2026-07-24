from rest_framework import serializers
from django_formation.models.etablissement import Etablissement
from django_formation.models.membre import MembreEtablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_formation.models.historique import HistoriqueStatutInscription


class EtablissementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Etablissement
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class EtablissementListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Etablissement
        fields = ["id", "nom", "code", "ville", "pays", "actif", "created_at"]


class MembreEtablissementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembreEtablissement
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ApprenantListSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()

    class Meta:
        model = Apprenant
        fields = ["id", "matricule", "nom", "prenom", "nom_complet", "telephone", "email", "statut", "created_at", "etablissement"]


class ApprenantDetailSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()

    class Meta:
        model = Apprenant
        fields = "__all__"
        read_only_fields = ["id", "matricule", "statut", "created_at", "updated_at"]


class ApprenantCreateSerializer(serializers.ModelSerializer):
    matricule = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Apprenant
        fields = ["matricule", "nom", "prenom", "sexe", "date_naissance", "lieu_naissance", "telephone", "email", "adresse", "contact_urgence_nom", "contact_urgence_telephone"]


class ApprenantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apprenant
        fields = ["prenom", "sexe", "date_naissance", "lieu_naissance", "telephone", "email", "adresse", "contact_urgence_nom", "contact_urgence_telephone"]


class FormationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formation
        fields = ["id", "code", "nom", "etablissement", "duree_heures", "tarif_indicatif", "devise", "statut", "created_at"]


class FormationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formation
        fields = "__all__"
        read_only_fields = ["id", "statut", "created_at", "updated_at"]


class FormationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formation
        fields = ["code", "nom", "description", "objectifs", "duree_heures", "duree_jours", "tarif_indicatif", "devise"]


class FormationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formation
        fields = ["nom", "description", "objectifs", "duree_heures", "duree_jours", "tarif_indicatif", "devise"]


class SessionListSerializer(serializers.ModelSerializer):
    formation_nom = serializers.ReadOnlyField(source="formation.nom")

    class Meta:
        model = SessionFormation
        fields = ["id", "code", "nom", "formation_nom", "date_debut", "date_fin", "capacite", "statut", "created_at"]


class SessionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionFormation
        fields = "__all__"
        read_only_fields = ["id", "statut", "created_at", "updated_at"]


class SessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionFormation
        fields = ["code", "nom", "date_debut", "date_fin", "date_ouverture_inscriptions", "date_fermeture_inscriptions", "capacite", "tarif", "devise"]


class SessionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionFormation
        fields = [
            "nom", "date_debut", "date_fin", "date_ouverture_inscriptions",
            "date_fermeture_inscriptions", "capacite", "tarif", "devise",
        ]


class InscriptionListSerializer(serializers.ModelSerializer):
    apprenant_nom = serializers.ReadOnlyField(source="apprenant.nom_complet")
    session_nom = serializers.ReadOnlyField(source="session.nom")

    class Meta:
        model = Inscription
        fields = ["id", "numero", "apprenant_nom", "session_nom", "date_inscription", "statut", "created_at"]


class InscriptionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscription
        fields = "__all__"
        read_only_fields = ["id", "numero", "statut", "date_inscription", "date_confirmation", "date_fin", "created_at", "updated_at", "etablissement"]


class InscriptionCreateSerializer(serializers.Serializer):
    apprenant = serializers.UUIDField()
    session = serializers.UUIDField()
    commentaire = serializers.CharField(required=False, allow_blank=True, default="")


class SessionStatsSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    capacite = serializers.IntegerField(allow_null=True)
    nombre_inscriptions = serializers.IntegerField()
    nombre_confirmes = serializers.IntegerField()
    nombre_en_attente = serializers.IntegerField()
    nombre_annules = serializers.IntegerField()
    places_restantes = serializers.IntegerField()
    session_complete = serializers.BooleanField()


class InscriptionHistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriqueStatutInscription
        fields = "__all__"
