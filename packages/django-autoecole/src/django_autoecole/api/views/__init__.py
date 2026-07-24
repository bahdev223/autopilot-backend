from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_autoecole.models import (
    CategoriePermis, Moniteur, Vehicule, DossierAutoEcole,
    LeconConduite, ExamenAutoEcole,
    IndisponibiliteMoniteur, IndisponibiliteVehicule, HistoriqueStatutDossier,
)
from ..serializers import (
    CategoriePermisSerializer, MoniteurListSerializer, MoniteurDetailSerializer,
    VehiculeListSerializer, VehiculeDetailSerializer,
    DossierAutoEcoleListSerializer, DossierAutoEcoleDetailSerializer,
    LeconConduiteListSerializer, LeconConduiteDetailSerializer,
    EvaluationLeconSerializer, ExamenAutoEcoleListSerializer, ExamenAutoEcoleDetailSerializer,
    IndisponibiliteMoniteurSerializer, IndisponibiliteVehiculeSerializer,
    HistoriqueStatutDossierSerializer,
    CreerDossierSerializer, PlanifierLeconSerializer, CreerMoniteurSerializer,
    CreerVehiculeSerializer, PlanifierExamenSerializer, TerminerLeconSerializer,
    AnnulerLeconSerializer, ReporterLeconSerializer, EnregistrerResultatExamenSerializer,
)
from ...services import dossiers, lecons, examens, vehicules, moniteurs, categories, indisponibilites
from ...exceptions import AutoEcoleDomainError
from ..permissions import IsAuthenticatedFormationMember, HasRoleLevel
from ..pagination import AutoEcolePagination
from ..filters import (
    CategoriePermisFilter, MoniteurFilter, VehiculeFilter,
    DossierAutoEcoleFilter, LeconConduiteFilter, ExamenAutoEcoleFilter,
)


class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedFormationMember, HasRoleLevel]
    pagination_class = AutoEcolePagination

    def get_queryset(self):
        queryset = super().get_queryset()
        memberships = self.request.user.adhesions_formation.filter(actif=True)
        establishment_ids = memberships.values_list("etablissement_id", flat=True)
        model = queryset.model
        if any(field.name == "etablissement" for field in model._meta.fields):
            return queryset.filter(etablissement_id__in=establishment_ids)
        if any(field.name == "moniteur" for field in model._meta.fields):
            return queryset.filter(moniteur__etablissement_id__in=establishment_ids)
        if any(field.name == "vehicule" for field in model._meta.fields):
            return queryset.filter(vehicule__etablissement_id__in=establishment_ids)
        return queryset.none()

    def create(self, request, *args, **kwargs):
        establishment_id = request.data.get("etablissement") or request.data.get("etablissement_id")
        if not establishment_id and request.data.get("dossier_id"):
            establishment_id = DossierAutoEcole.objects.filter(
                pk=request.data["dossier_id"]
            ).values_list("etablissement_id", flat=True).first()
        if not establishment_id and request.data.get("inscription_id"):
            from django_formation.models import Inscription
            establishment_id = Inscription.objects.filter(
                pk=request.data["inscription_id"]
            ).values_list("etablissement_id", flat=True).first()
        if establishment_id and not request.user.adhesions_formation.filter(
            actif=True,
            etablissement_id=establishment_id,
        ).exists():
            raise PermissionDenied("Établissement inaccessible")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        response_serializers = {
            CategoriePermis: CategoriePermisSerializer,
            Moniteur: MoniteurDetailSerializer,
            Vehicule: VehiculeDetailSerializer,
            DossierAutoEcole: DossierAutoEcoleDetailSerializer,
            LeconConduite: LeconConduiteDetailSerializer,
            ExamenAutoEcole: ExamenAutoEcoleDetailSerializer,
            IndisponibiliteMoniteur: IndisponibiliteMoniteurSerializer,
            IndisponibiliteVehicule: IndisponibiliteVehiculeSerializer,
        }
        response_serializer = response_serializers[type(instance)]
        return Response(response_serializer(instance).data, status=status.HTTP_201_CREATED)


class CategoriePermisViewSet(TenantScopedViewSet):
    queryset = CategoriePermis.objects.select_related("etablissement").all()
    serializer_class = CategoriePermisSerializer
    filterset_class = CategoriePermisFilter
    search_fields = ["code", "nom"]
    ordering_fields = ["code", "nom"]

    @action(detail=True, methods=["post"])
    def activer(self, request, pk=None):
        obj = self.get_object()
        categories.activer_categorie_permis(obj)
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=["post"])
    def desactiver(self, request, pk=None):
        obj = self.get_object()
        categories.desactiver_categorie_permis(obj)
        return Response(self.get_serializer(obj).data)


class MoniteurViewSet(TenantScopedViewSet):
    queryset = Moniteur.objects.select_related("etablissement", "utilisateur").prefetch_related("categories_permis").all()
    filterset_class = MoniteurFilter
    search_fields = ["nom", "prenom", "matricule", "numero_agrement"]
    ordering_fields = ["nom", "matricule", "date_embauche"]

    def get_serializer_class(self):
        if self.action == "create":
            return CreerMoniteurSerializer
        if self.action == "list":
            return MoniteurListSerializer
        return MoniteurDetailSerializer

    @action(detail=True, methods=["post"])
    def activer(self, request, pk=None):
        m = self.get_object()
        moniteurs.activer_moniteur(m)
        return Response(MoniteurDetailSerializer(m).data)

    @action(detail=True, methods=["post"])
    def indisponible(self, request, pk=None):
        m = self.get_object()
        moniteurs.rendre_moniteur_indisponible(m)
        return Response(MoniteurDetailSerializer(m).data)

    @action(detail=True, methods=["post"])
    def suspendre(self, request, pk=None):
        m = self.get_object()
        moniteurs.suspendre_moniteur(m)
        return Response(MoniteurDetailSerializer(m).data)

    @action(detail=True, methods=["post"])
    def reactiver(self, request, pk=None):
        m = self.get_object()
        moniteurs.reactiver_moniteur(m)
        return Response(MoniteurDetailSerializer(m).data)

    @action(detail=True, methods=["post"])
    def archiver(self, request, pk=None):
        m = self.get_object()
        moniteurs.archiver_moniteur(m)
        return Response(MoniteurDetailSerializer(m).data)

    @action(detail=True, methods=["get"])
    def planning(self, request, pk=None):
        from ...selectors import lister_lecons_moniteur
        lecons = lister_lecons_moniteur(
            moniteur_id=pk,
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        )
        return Response(LeconConduiteListSerializer(lecons, many=True).data)


class VehiculeViewSet(TenantScopedViewSet):
    queryset = Vehicule.objects.select_related("etablissement", "categorie_permis").all()
    filterset_class = VehiculeFilter
    search_fields = ["immatriculation", "marque", "modele"]
    ordering_fields = ["immatriculation", "marque", "kilometrage_actuel"]

    def get_serializer_class(self):
        if self.action == "create":
            return CreerVehiculeSerializer
        if self.action == "list":
            return VehiculeListSerializer
        return VehiculeDetailSerializer

    @action(detail=True, methods=["post"])
    def mettre_en_entretien(self, request, pk=None):
        v = self.get_object()
        vehicules.mettre_vehicule_en_entretien(v)
        return Response(VehiculeDetailSerializer(v).data)

    @action(detail=True, methods=["post"])
    def declarer_en_panne(self, request, pk=None):
        v = self.get_object()
        vehicules.declarer_vehicule_en_panne(v)
        return Response(VehiculeDetailSerializer(v).data)

    @action(detail=True, methods=["post"])
    def rendre_disponible(self, request, pk=None):
        v = self.get_object()
        vehicules.remettre_vehicule_disponible(v)
        return Response(VehiculeDetailSerializer(v).data)

    @action(detail=True, methods=["post"])
    def mettre_hors_service(self, request, pk=None):
        v = self.get_object()
        vehicules.mettre_vehicule_hors_service(v)
        return Response(VehiculeDetailSerializer(v).data)

    @action(detail=True, methods=["post"])
    def archiver(self, request, pk=None):
        v = self.get_object()
        vehicules.archiver_vehicule(v)
        return Response(VehiculeDetailSerializer(v).data)

    @action(detail=True, methods=["post"])
    def mettre_a_jour_kilometrage(self, request, pk=None):
        v = self.get_object()
        km = request.data.get("kilometrage")
        if km is None:
            return Response({"error": "kilometrage requis"}, status=status.HTTP_400_BAD_REQUEST)
        vehicules.mettre_a_jour_kilometrage(v, km)
        return Response(VehiculeDetailSerializer(v).data)

    @action(detail=True, methods=["get"])
    def planning(self, request, pk=None):
        from ...selectors import lister_lecons_vehicule
        lecons = lister_lecons_vehicule(
            vehicule_id=pk,
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        )
        return Response(LeconConduiteListSerializer(lecons, many=True).data)

    @action(detail=True, methods=["get"])
    def indisponibilites(self, request, pk=None):
        indispos = IndisponibiliteVehicule.objects.filter(vehicule_id=pk)
        return Response(IndisponibiliteVehiculeSerializer(indispos, many=True).data)


class DossierAutoEcoleViewSet(TenantScopedViewSet):
    queryset = DossierAutoEcole.objects.select_related(
        "etablissement", "inscription", "categorie_permis", "moniteur_referent"
    ).all()
    filterset_class = DossierAutoEcoleFilter
    search_fields = ["numero_dossier", "inscription__apprenant__nom"]
    ordering_fields = ["date_ouverture", "statut"]

    def get_serializer_class(self):
        if self.action == "create":
            return CreerDossierSerializer
        if self.action == "list":
            return DossierAutoEcoleListSerializer
        return DossierAutoEcoleDetailSerializer

    @action(detail=True, methods=["post"])
    def ouvrir(self, request, pk=None):
        d = self.get_object()
        dossiers.ouvrir_dossier(d, modifie_par=request.user)
        return Response(DossierAutoEcoleDetailSerializer(d).data)

    @action(detail=True, methods=["post"])
    def demarrer_formation(self, request, pk=None):
        d = self.get_object()
        dossiers.demarrer_formation_dossier(d, modifie_par=request.user)
        return Response(DossierAutoEcoleDetailSerializer(d).data)

    @action(detail=True, methods=["post"])
    def suspendre(self, request, pk=None):
        d = self.get_object()
        dossiers.suspendre_dossier(d, modifie_par=request.user, commentaire=request.data.get("commentaire", ""))
        return Response(DossierAutoEcoleDetailSerializer(d).data)

    @action(detail=True, methods=["post"])
    def reprendre(self, request, pk=None):
        d = self.get_object()
        dossiers.reprendre_dossier(d, modifie_par=request.user)
        return Response(DossierAutoEcoleDetailSerializer(d).data)

    @action(detail=True, methods=["post"])
    def declarer_pret_examen(self, request, pk=None):
        d = self.get_object()
        try:
            dossiers.declarer_dossier_pret_examen(d, modifie_par=request.user)
            return Response(DossierAutoEcoleDetailSerializer(d).data)
        except AutoEcoleDomainError as e:
            return Response({"code": type(e).__name__, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        d = self.get_object()
        dossiers.annuler_dossier(d, modifie_par=request.user, commentaire=request.data.get("commentaire", ""))
        return Response(DossierAutoEcoleDetailSerializer(d).data)

    @action(detail=True, methods=["post"])
    def cloturer(self, request, pk=None):
        d = self.get_object()
        dossiers.cloturer_dossier(d, modifie_par=request.user)
        return Response(DossierAutoEcoleDetailSerializer(d).data)

    @action(detail=True, methods=["post"])
    def affecter_moniteur(self, request, pk=None):
        d = self.get_object()
        from django.shortcuts import get_object_or_404
        moniteur = get_object_or_404(Moniteur, id=request.data.get("moniteur_id"))
        dossiers.affecter_moniteur_referent(d, moniteur, modifie_par=request.user)
        return Response(DossierAutoEcoleDetailSerializer(d).data)

    @action(detail=True, methods=["get"])
    def progression(self, request, pk=None):
        d = self.get_object()
        return Response({
            "heures_theorie_validees": float(d.heures_theorie_validees),
            "heures_theorie_requises": float(d.categorie_permis.heures_theorie_minimum),
            "heures_conduite_validees": float(d.heures_conduite_validees),
            "heures_conduite_requises": float(d.categorie_permis.heures_conduite_minimum),
            "progression_conduite": d.progression_conduite,
            "peut_etre_presente_examen": d.peut_etre_presente_examen,
        })

    @action(detail=True, methods=["get"])
    def historique(self, request, pk=None):
        historique = HistoriqueStatutDossier.objects.filter(dossier_id=pk).order_by("-created_at")
        return Response(HistoriqueStatutDossierSerializer(historique, many=True).data)

    @action(detail=True, methods=["get"])
    def lecons(self, request, pk=None):
        from ...selectors import lister_lecons_dossier
        lecons = lister_lecons_dossier(dossier_id=pk)
        return Response(LeconConduiteListSerializer(lecons, many=True).data)

    @action(detail=True, methods=["get"])
    def examens(self, request, pk=None):
        examens = ExamenAutoEcole.objects.filter(dossier_id=pk).order_by("-date_examen")
        return Response(ExamenAutoEcoleListSerializer(examens, many=True).data)


class LeconConduiteViewSet(TenantScopedViewSet):
    queryset = LeconConduite.objects.select_related(
        "etablissement", "dossier", "moniteur", "vehicule"
    ).all()
    filterset_class = LeconConduiteFilter
    ordering_fields = ["date_debut", "duree_minutes", "statut"]

    def get_serializer_class(self):
        if self.action == "create":
            return PlanifierLeconSerializer
        if self.action == "list":
            return LeconConduiteListSerializer
        return LeconConduiteDetailSerializer

    @action(detail=True, methods=["post"])
    def confirmer(self, request, pk=None):
        lecon = self.get_object()
        lecons.confirmer_lecon(lecon)
        return Response(LeconConduiteDetailSerializer(lecon).data)

    @action(detail=True, methods=["post"])
    def demarrer(self, request, pk=None):
        lecon = self.get_object()
        km = request.data.get("kilometrage_depart")
        lecons.demarrer_lecon(lecon, kilometrage_depart=km)
        return Response(LeconConduiteDetailSerializer(lecon).data)

    @action(detail=True, methods=["post"])
    def terminer(self, request, pk=None):
        lecon = self.get_object()
        ser = TerminerLeconSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        lecons.terminer_lecon(lecon, **ser.validated_data)
        return Response(LeconConduiteDetailSerializer(lecon).data)

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        lecon = self.get_object()
        ser = AnnulerLeconSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        lecons.annuler_lecon(lecon, **ser.validated_data)
        return Response(LeconConduiteDetailSerializer(lecon).data)

    @action(detail=True, methods=["post"])
    def reporter(self, request, pk=None):
        lecon = self.get_object()
        ser = ReporterLeconSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        nouvelle = lecons.reporter_lecon(lecon, **ser.validated_data)
        return Response(LeconConduiteDetailSerializer(nouvelle).data)

    @action(detail=True, methods=["post"])
    def absence_candidat(self, request, pk=None):
        lecon = self.get_object()
        lecons.marquer_absence_candidat(lecon, observation=request.data.get("observation", ""))
        return Response(LeconConduiteDetailSerializer(lecon).data)

    @action(detail=True, methods=["post"])
    def absence_moniteur(self, request, pk=None):
        lecon = self.get_object()
        lecons.marquer_absence_moniteur(lecon, observation=request.data.get("observation", ""))
        return Response(LeconConduiteDetailSerializer(lecon).data)

    @action(detail=True, methods=["post"])
    def evaluer(self, request, pk=None):
        lecon = self.get_object()
        if lecon.statut != "REALISEE":
            return Response({"error": "La leçon doit être réalisée pour être évaluée"}, status=status.HTTP_400_BAD_REQUEST)
        ser = EvaluationLeconSerializer(data={**request.data, "lecon": lecon.id, "moniteur": lecon.moniteur_id})
        ser.is_valid(raise_exception=True)
        evaluation = lecons.evaluer_lecon(
            lecon=lecon,
            moniteur=lecon.moniteur,
            note_globale=ser.validated_data.get("note_globale"),
            niveau=ser.validated_data.get("niveau", ""),
            competences_acquises=ser.validated_data.get("competences_acquises"),
            points_forts=ser.validated_data.get("points_forts", ""),
            points_a_ameliorer=ser.validated_data.get("points_a_ameliorer", ""),
            commentaire=ser.validated_data.get("commentaire", ""),
            recommande_examen=ser.validated_data.get("recommande_examen", False),
        )
        return Response(EvaluationLeconSerializer(evaluation).data, status=status.HTTP_201_CREATED)


class ExamenAutoEcoleViewSet(TenantScopedViewSet):
    queryset = ExamenAutoEcole.objects.select_related("etablissement", "dossier").all()
    filterset_class = ExamenAutoEcoleFilter
    ordering_fields = ["date_examen", "statut", "resultat"]

    def get_serializer_class(self):
        if self.action == "create":
            return PlanifierExamenSerializer
        if self.action == "list":
            return ExamenAutoEcoleListSerializer
        return ExamenAutoEcoleDetailSerializer

    @action(detail=True, methods=["post"])
    def confirmer(self, request, pk=None):
        e = self.get_object()
        examens.confirmer_examen(e)
        return Response(ExamenAutoEcoleDetailSerializer(e).data)

    @action(detail=True, methods=["post"])
    def marquer_presente(self, request, pk=None):
        e = self.get_object()
        examens.marquer_candidat_presente(e)
        return Response(ExamenAutoEcoleDetailSerializer(e).data)

    @action(detail=True, methods=["post"])
    def marquer_absent(self, request, pk=None):
        e = self.get_object()
        examens.marquer_candidat_absent(e)
        return Response(ExamenAutoEcoleDetailSerializer(e).data)

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        e = self.get_object()
        examens.annuler_examen(e)
        return Response(ExamenAutoEcoleDetailSerializer(e).data)

    @action(detail=True, methods=["post"])
    def enregistrer_resultat(self, request, pk=None):
        e = self.get_object()
        ser = EnregistrerResultatExamenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            examens.enregistrer_resultat_examen(e, **ser.validated_data)
            return Response(ExamenAutoEcoleDetailSerializer(e).data)
        except AutoEcoleDomainError as err:
            return Response({"code": type(err).__name__, "message": str(err)}, status=status.HTTP_400_BAD_REQUEST)


class IndisponibiliteMoniteurViewSet(TenantScopedViewSet):
    queryset = IndisponibiliteMoniteur.objects.select_related("moniteur").all()
    serializer_class = IndisponibiliteMoniteurSerializer
    filterset_fields = ["moniteur", "statut"]

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        obj = self.get_object()
        indisponibilites.annuler_indisponibilite_moniteur(obj)
        return Response(self.get_serializer(obj).data)


class IndisponibiliteVehiculeViewSet(TenantScopedViewSet):
    queryset = IndisponibiliteVehicule.objects.select_related("vehicule").all()
    serializer_class = IndisponibiliteVehiculeSerializer
    filterset_fields = ["vehicule", "statut"]

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        obj = self.get_object()
        indisponibilites.annuler_indisponibilite_vehicule(obj)
        return Response(self.get_serializer(obj).data)
