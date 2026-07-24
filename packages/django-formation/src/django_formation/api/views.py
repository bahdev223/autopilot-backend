from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from django_formation.models.etablissement import Etablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_formation.models.membre import MembreEtablissement
from django_formation.api.serializers import (
    EtablissementSerializer, EtablissementListSerializer,
    MembreEtablissementSerializer,
    ApprenantListSerializer, ApprenantDetailSerializer, ApprenantCreateSerializer, ApprenantUpdateSerializer,
    FormationListSerializer, FormationDetailSerializer, FormationCreateSerializer, FormationUpdateSerializer,
    SessionListSerializer, SessionDetailSerializer, SessionCreateSerializer, SessionUpdateSerializer,
    InscriptionListSerializer, InscriptionDetailSerializer, InscriptionCreateSerializer,
    SessionStatsSerializer, InscriptionHistoriqueSerializer,
)
from django_formation.services.apprenants import ApprenantService
from django_formation.services.formations import FormationService
from django_formation.services.sessions import SessionService
from django_formation.services.inscriptions import InscriptionService
from django_formation.selectors.apprenants import ApprenantSelector
from django_formation.selectors.formations import FormationSelector
from django_formation.selectors.sessions import SessionSelector
from django_formation.selectors.inscriptions import InscriptionSelector
from django_formation.domain.exceptions.formation_exceptions import FormationDomainError
from django_formation.api.pagination import paginated_response

apprenant_svc = ApprenantService()
formation_svc = FormationService()
session_svc = SessionService()
inscription_svc = InscriptionService()
apprenant_sel = ApprenantSelector()
formation_sel = FormationSelector()
session_sel = SessionSelector()
inscription_sel = InscriptionSelector()


def _domain_error_response(exc):
    return Response(
        {"code": exc.code, "message": str(exc), "details": {}},
        status=exc.status_code,
    )


def _get_accessible(model, user, pk):
    return get_object_or_404(
        model, pk=pk,
        etablissement__membres__utilisateur=user,
        etablissement__membres__actif=True,
    )


def _get_objet_editable(model, user, pk, roles):
    return get_object_or_404(
        model, pk=pk,
        etablissement__membres__utilisateur=user,
        etablissement__membres__actif=True,
        etablissement__membres__role__in=roles,
    )


def _check_etablissement_permission(user, etablissement_id, roles):
    if not MembreEtablissement.objects.filter(
        utilisateur=user, etablissement_id=etablissement_id,
        actif=True, role__in=roles,
    ).exists():
        raise PermissionDenied("Vous n'avez pas les droits nécessaires sur cet établissement")


# ---- Établissements ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def etablissement_list_create(request):
    if request.method == "GET":
        qs = Etablissement.objects.filter(membres__utilisateur=request.user, membres__actif=True).distinct()
        return paginated_response(request, qs, EtablissementListSerializer)
    serializer = EtablissementSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    etablissement = serializer.save()
    MembreEtablissement.objects.create(etablissement=etablissement, utilisateur=request.user, role="PROPRIETAIRE")
    return Response(EtablissementSerializer(etablissement).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def etablissement_detail(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, membres__utilisateur=request.user, membres__actif=True)
    if request.method == "GET":
        return Response(EtablissementSerializer(etablissement).data)
    _check_etablissement_permission(request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR"])
    serializer = EtablissementSerializer(etablissement, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(EtablissementSerializer(etablissement).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def etablissement_activer(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, membres__utilisateur=request.user, membres__actif=True)
    _check_etablissement_permission(request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR"])
    etablissement.actif = True
    etablissement.save(update_fields=["actif"])
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def etablissement_desactiver(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, membres__utilisateur=request.user, membres__actif=True)
    _check_etablissement_permission(request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR"])
    etablissement.actif = False
    etablissement.save(update_fields=["actif"])
    return Response({"status": "ok"})


# ---- Membres ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def membre_list_create(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, membres__utilisateur=request.user, membres__actif=True)
    _check_etablissement_permission(request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR"])
    if request.method == "GET":
        qs = MembreEtablissement.objects.filter(etablissement=etablissement)
        return paginated_response(request, qs, MembreEtablissementSerializer)
    serializer = MembreEtablissementSerializer(data={**request.data, "etablissement": str(etablissement.pk)})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def membre_detail(request, pk):
    membre = get_object_or_404(MembreEtablissement, pk=pk, etablissement__membres__utilisateur=request.user, etablissement__membres__actif=True)
    _check_etablissement_permission(request.user, membre.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR"])
    if request.method == "PATCH":
        serializer = MembreEtablissementSerializer(membre, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MembreEtablissementSerializer(membre).data)
    membre.actif = False
    membre.save(update_fields=["actif"])
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---- Apprenants ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def apprenant_list_create(request):
    if request.method == "GET":
        etablissement_id = request.query_params.get("etablissement")
        statut = request.query_params.get("statut")
        search = request.query_params.get("search")
        ordering = request.query_params.get("ordering", "nom")
        if not etablissement_id:
            return Response({"error": "etablissement parameter is required"}, status=400)
        _check_etablissement_permission(request.user, etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE", "AGENT_INSCRIPTION", "LECTEUR"])
        qs = apprenant_sel.rechercher_apprenants(etablissement_id, query=search or "", statut=statut)
        qs = qs.order_by(ordering)
        return paginated_response(request, qs, ApprenantListSerializer)
    serializer = ApprenantCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    etablissement_id = request.data.get("etablissement")
    get_object_or_404(Etablissement, pk=etablissement_id, membres__utilisateur=request.user, membres__actif=True)
    _check_etablissement_permission(request.user, etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE", "AGENT_INSCRIPTION"])
    etablissement = Etablissement.objects.get(pk=etablissement_id)
    try:
        apprenant = apprenant_svc.creer_apprenant(etablissement=etablissement, **serializer.validated_data, cree_par=request.user)
        return Response(ApprenantDetailSerializer(apprenant).data, status=status.HTTP_201_CREATED)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def apprenant_detail(request, pk):
    apprenant = _get_accessible(Apprenant, request.user, pk)
    if request.method == "GET":
        return Response(ApprenantDetailSerializer(apprenant).data)
    _check_etablissement_permission(request.user, apprenant.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE", "AGENT_INSCRIPTION"])
    serializer = ApprenantUpdateSerializer(apprenant, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    apprenant_svc.modifier_apprenant(apprenant, **serializer.validated_data)
    return Response(ApprenantDetailSerializer(apprenant).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apprenant_activer(request, pk):
    apprenant = _get_accessible(Apprenant, request.user, pk)
    _check_etablissement_permission(request.user, apprenant.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        apprenant_svc.activer_apprenant(apprenant)
        return Response(ApprenantDetailSerializer(apprenant).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apprenant_desactiver(request, pk):
    apprenant = _get_accessible(Apprenant, request.user, pk)
    _check_etablissement_permission(request.user, apprenant.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        apprenant_svc.desactiver_apprenant(apprenant)
        return Response(ApprenantDetailSerializer(apprenant).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apprenant_archiver(request, pk):
    apprenant = _get_accessible(Apprenant, request.user, pk)
    _check_etablissement_permission(request.user, apprenant.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        apprenant_svc.archiver_apprenant(apprenant)
        return Response(ApprenantDetailSerializer(apprenant).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def apprenant_inscriptions(request, pk):
    apprenant = _get_accessible(Apprenant, request.user, pk)
    inscriptions = apprenant_sel.inscriptions_apprenant(apprenant)
    return paginated_response(request, inscriptions, InscriptionListSerializer)


# ---- Formations ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def formation_list_create(request):
    if request.method == "GET":
        etablissement_id = request.query_params.get("etablissement")
        statut = request.query_params.get("statut")
        search = request.query_params.get("search")
        if etablissement_id:
            _check_etablissement_permission(
                request.user,
                etablissement_id,
                ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE", "AGENT_INSCRIPTION", "LECTEUR"],
            )
            qs = formation_sel.formations_par_etablissement(etablissement_id)
        else:
            qs = formation_sel.formations_accessibles_par_utilisateur(request.user)
        if statut:
            qs = qs.filter(statut=statut)
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(nom__icontains=search) | Q(code__icontains=search))
        return paginated_response(request, qs.distinct(), FormationListSerializer)
    serializer = FormationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    etablissement_id = request.data.get("etablissement")
    get_object_or_404(Etablissement, pk=etablissement_id, membres__utilisateur=request.user, membres__actif=True)
    _check_etablissement_permission(request.user, etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    etablissement = Etablissement.objects.get(pk=etablissement_id)
    try:
        formation = formation_svc.creer_formation(etablissement=etablissement, **serializer.validated_data)
        return Response(FormationDetailSerializer(formation).data, status=status.HTTP_201_CREATED)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def formation_detail(request, pk):
    formation = _get_accessible(Formation, request.user, pk)
    if request.method == "GET":
        return Response(FormationDetailSerializer(formation).data)
    _check_etablissement_permission(request.user, formation.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    serializer = FormationUpdateSerializer(formation, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    formation_svc.modifier_formation(formation, **serializer.validated_data)
    return Response(FormationDetailSerializer(formation).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def formation_publier(request, pk):
    formation = _get_objet_editable(Formation, request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        formation_svc.publier_formation(formation)
        return Response(FormationDetailSerializer(formation).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def formation_suspendre(request, pk):
    formation = _get_objet_editable(Formation, request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        formation_svc.suspendre_formation(formation)
        return Response(FormationDetailSerializer(formation).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def formation_reactiver(request, pk):
    formation = _get_objet_editable(Formation, request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        formation_svc.reactiver_formation(formation)
        return Response(FormationDetailSerializer(formation).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def formation_archiver(request, pk):
    formation = _get_objet_editable(Formation, request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR"])
    try:
        formation_svc.archiver_formation(formation)
        return Response(FormationDetailSerializer(formation).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def formation_sessions(request, pk):
    _get_accessible(Formation, request.user, pk)
    sessions = formation_sel.sessions_formation(pk)
    return paginated_response(request, sessions, SessionListSerializer)


# ---- Sessions ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def session_list_create(request):
    if request.method == "GET":
        etablissement_id = request.query_params.get("etablissement")
        formation_id = request.query_params.get("formation")
        statut = request.query_params.get("statut")
        if etablissement_id:
            _check_etablissement_permission(
                request.user,
                etablissement_id,
                ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE", "AGENT_INSCRIPTION", "LECTEUR"],
            )
            qs = SessionFormation.objects.filter(etablissement_id=etablissement_id)
        else:
            qs = session_sel.sessions_accessibles_par_utilisateur(request.user)
        if formation_id:
            qs = qs.filter(formation_id=formation_id)
        if statut:
            qs = qs.filter(statut=statut)
        return paginated_response(request, qs.distinct(), SessionListSerializer)
    serializer = SessionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        etablissement_id = request.data.get("etablissement")
        formation = _get_accessible(Formation, request.user, request.data["formation"])
        if str(formation.etablissement_id) != etablissement_id:
            return Response({"error": "La formation n'appartient pas à cet établissement"}, status=400)
        _check_etablissement_permission(request.user, formation.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
        session = session_svc.creer_session(
            etablissement=formation.etablissement, formation=formation,
            **{k: v for k, v in serializer.validated_data.items() if k not in ("etablissement", "formation")},
        )
        return Response(SessionDetailSerializer(session).data, status=status.HTTP_201_CREATED)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def session_detail(request, pk):
    session_obj = _get_accessible(SessionFormation, request.user, pk)
    if request.method == "GET":
        return Response(SessionDetailSerializer(session_obj).data)
    _check_etablissement_permission(request.user, session_obj.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    serializer = SessionUpdateSerializer(session_obj, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    session_svc.modifier_session(session_obj, **{k: v for k, v in serializer.validated_data.items() if k not in ("etablissement", "formation", "statut")})
    return Response(SessionDetailSerializer(session_obj).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_ouvrir_inscriptions(request, pk):
    session_obj = _get_objet_editable(SessionFormation, request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        session_svc.ouvrir_inscriptions(session_obj)
        return Response(SessionDetailSerializer(session_obj).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_fermer_inscriptions(request, pk):
    session_obj = _get_objet_editable(SessionFormation, request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        session_svc.fermer_inscriptions(session_obj)
        return Response(SessionDetailSerializer(session_obj).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_demarrer(request, pk):
    session_obj = _get_objet_editable(SessionFormation, request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        session_svc.demarrer_session(session_obj, modifie_par=request.user)
        return Response(SessionDetailSerializer(session_obj).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_terminer(request, pk):
    session_obj = _get_objet_editable(SessionFormation, request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        session_svc.terminer_session(session_obj, modifie_par=request.user)
        return Response(SessionDetailSerializer(session_obj).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_annuler(request, pk):
    session_obj = _get_objet_editable(SessionFormation, request.user, pk, ["PROPRIETAIRE", "ADMINISTRATEUR"])
    try:
        session_svc.annuler_session(session_obj, modifie_par=request.user)
        return Response(SessionDetailSerializer(session_obj).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_inscriptions(request, pk):
    _get_accessible(SessionFormation, request.user, pk)
    inscrits = session_sel.inscrits_session(pk)
    return paginated_response(request, inscrits, InscriptionListSerializer)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_statistiques(request, pk):
    session_obj = _get_accessible(SessionFormation, request.user, pk)
    stats = {
        "session_id": session_obj.pk,
        "capacite": session_obj.capacite,
        "nombre_inscriptions": session_obj.inscriptions.count(),
        "nombre_confirmes": session_obj.inscriptions.filter(statut="CONFIRMEE").count(),
        "nombre_en_attente": session_obj.inscriptions.filter(statut="EN_ATTENTE").count(),
        "nombre_annules": session_obj.inscriptions.filter(statut="ANNULEE").count(),
        "places_restantes": session_obj.nombre_places_restantes,
        "session_complete": session_obj.est_complete,
    }
    return Response(SessionStatsSerializer(stats).data)


# ---- Inscriptions ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def inscription_list_create(request):
    if request.method == "GET":
        session_id = request.query_params.get("session")
        apprenant_id = request.query_params.get("apprenant")
        statut_filter = request.query_params.get("statut")
        if session_id:
            session_obj = _get_accessible(SessionFormation, request.user, session_id)
            qs = inscription_sel.inscriptions_par_session(session_obj.pk)
        elif apprenant_id:
            apprenant = _get_accessible(Apprenant, request.user, apprenant_id)
            qs = inscription_sel.inscriptions_par_apprenant(apprenant.pk)
        else:
            qs = inscription_sel.inscriptions_accessibles_par_utilisateur(request.user)
        if statut_filter:
            qs = qs.filter(statut=statut_filter)
        return paginated_response(request, qs.distinct(), InscriptionListSerializer)
    serializer = InscriptionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        apprenant = _get_accessible(Apprenant, request.user, serializer.validated_data["apprenant"])
        session_obj = _get_accessible(SessionFormation, request.user, serializer.validated_data["session"])
        if apprenant.etablissement_id != session_obj.etablissement_id:
            return Response({"error": "L'apprenant et la session doivent appartenir au même établissement"}, status=400)
        inscription = inscription_svc.creer_preinscription(
            apprenant=apprenant, session=session_obj,
            commentaire=serializer.validated_data.get("commentaire", ""), cree_par=request.user,
        )
        return Response(InscriptionDetailSerializer(inscription).data, status=status.HTTP_201_CREATED)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inscription_detail(request, pk):
    inscription = _get_accessible(Inscription, request.user, pk)
    return Response(InscriptionDetailSerializer(inscription).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_mettre_en_attente(request, pk):
    inscription = _get_accessible(Inscription, request.user, pk)
    _check_etablissement_permission(request.user, inscription.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "AGENT_INSCRIPTION"])
    try:
        inscription_svc.mettre_en_attente(inscription, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_confirmer(request, pk):
    inscription = _get_accessible(Inscription, request.user, pk)
    _check_etablissement_permission(request.user, inscription.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "AGENT_INSCRIPTION"])
    try:
        inscription_svc.confirmer_inscription(inscription, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return _domain_error_response(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_refuser(request, pk):
    inscription = _get_accessible(Inscription, request.user, pk)
    _check_etablissement_permission(request.user, inscription.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "AGENT_INSCRIPTION"])
    motif = request.data.get("motif", "")
    try:
        inscription_svc.refuser_inscription(inscription, motif=motif, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_annuler(request, pk):
    inscription = _get_accessible(Inscription, request.user, pk)
    _check_etablissement_permission(request.user, inscription.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "AGENT_INSCRIPTION"])
    motif = request.data.get("motif", "")
    try:
        inscription_svc.annuler_inscription(inscription, motif=motif, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_demarrer(request, pk):
    inscription = _get_accessible(Inscription, request.user, pk)
    _check_etablissement_permission(request.user, inscription.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        inscription_svc.demarrer_inscription(inscription, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_abandonner(request, pk):
    inscription = _get_accessible(Inscription, request.user, pk)
    _check_etablissement_permission(request.user, inscription.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        inscription_svc.marquer_abandon(inscription, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_terminer(request, pk):
    inscription = _get_accessible(Inscription, request.user, pk)
    _check_etablissement_permission(request.user, inscription.etablissement_id, ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"])
    try:
        inscription_svc.terminer_inscription(inscription, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inscription_historique(request, pk):
    _get_accessible(Inscription, request.user, pk)
    historique = inscription_sel.historique_inscription(pk)
    return paginated_response(request, historique, InscriptionHistoriqueSerializer)
