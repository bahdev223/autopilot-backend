from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone

from django_formation.models import Apprenant, Formation, SessionFormation, Inscription
from django_formation.constants import StatutInscription
from django_formation.services import inscriptions as inscription_service
from django_autoecole.constants import StatutDossier
from django_autoecole.models import DossierAutoEcole


# ── Apprenants ──────────────────────────────────────────────

@login_required
def apprenants_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "apprenants/liste.html", {"apprenants": [], "stats": {}})

    qs = Apprenant.objects.filter(etablissement=etab)
    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(matricule__icontains=q) | Q(telephone__icontains=q))
    statut = request.GET.get("statut", "")
    if statut:
        qs = qs.filter(statut=statut)

    stats = {
        "total": qs.count(),
        "actifs": qs.filter(statut="ACTIF").count(),
        "inactifs": qs.filter(statut="INACTIF").count(),
        "archives": qs.filter(statut="ARCHIVE").count(),
    }
    return render(request, "apprenants/liste.html", {
        "apprenants": qs.select_related("etablissement").order_by("-created_at")[:50],
        "stats": stats,
        "q": q,
        "statut": statut,
    })


@login_required
def apprenant_creer(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")

    if request.method == "POST":
        from django_formation.services.apprenants import creer_apprenant
        try:
            apprenant = creer_apprenant(
                etablissement=etab,
                nom=request.POST["nom"],
                prenom=request.POST["prenom"],
                sexe=request.POST.get("sexe", ""),
                date_naissance=request.POST.get("date_naissance") or None,
                telephone=request.POST.get("telephone", ""),
                email=request.POST.get("email", ""),
                adresse=request.POST.get("adresse", ""),
                cree_par=request.user,
            )
            messages.success(request, f"Apprenant {apprenant} créé.")
            if "continuer_inscription" in request.POST:
                return redirect("inscription_creer", apprenant_id=apprenant.id)
            return redirect("apprenant_fiche", id=apprenant.id)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "apprenants/formulaire.html", {"mode": "creer"})


@login_required
def apprenant_fiche(request, id):
    etab = getattr(request, "etablissement_actif", None)
    apprenant = get_object_or_404(Apprenant, id=id, etablissement=etab)
    inscriptions = Inscription.objects.filter(apprenant=apprenant).select_related("session", "session__formation").order_by("-created_at")
    dossiers = DossierAutoEcole.objects.filter(etablissement=etab, inscription__apprenant=apprenant).select_related("categorie_permis", "moniteur_referent")
    return render(request, "apprenants/fiche.html", {
        "apprenant": apprenant,
        "inscriptions": inscriptions,
        "dossiers": dossiers,
        "breadcrumbs": [
            {"url": "/apprenants/", "label": "Apprenants"},
            {"label": str(apprenant)},
        ],
    })


@login_required
def apprenant_modifier(request, id):
    etab = getattr(request, "etablissement_actif", None)
    apprenant = get_object_or_404(Apprenant, id=id, etablissement=etab)
    if request.method == "POST":
        for field in ("nom", "prenom", "sexe", "date_naissance", "telephone", "email", "adresse", "statut"):
            if field in request.POST:
                setattr(apprenant, field, request.POST[field] or None)
        apprenant.save()
        messages.success(request, "Apprenant mis à jour.")
        return redirect("apprenant_fiche", id=apprenant.id)
    return render(request, "apprenants/formulaire.html", {
        "apprenant": apprenant,
        "mode": "modifier",
    })


# ── Formations ──────────────────────────────────────────────

@login_required
def formations_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "formations/liste.html", {"formations": []})
    qs = Formation.objects.filter(etablissement=etab)
    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(nom__icontains=q))
    return render(request, "formations/liste.html", {
        "formations": qs.annotate(nb_sessions=Count("sessions")).order_by("-created_at")[:50],
        "q": q,
    })


@login_required
def formation_creer(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")
    if request.method == "POST":
        from django_formation.services.formations import creer_formation
        try:
            formation = creer_formation(
                etablissement=etab,
                code=request.POST["code"],
                nom=request.POST["nom"],
                description=request.POST.get("description", ""),
                duree_heures=request.POST.get("duree_heures") or 0,
                cree_par=request.user,
            )
            messages.success(request, f"Formation {formation.code} créée.")
            return redirect("formation_fiche", id=formation.id)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "formations/formulaire.html", {"mode": "creer"})


@login_required
def formation_fiche(request, id):
    etab = getattr(request, "etablissement_actif", None)
    formation = get_object_or_404(Formation, id=id, etablissement=etab)
    sessions = SessionFormation.objects.filter(formation=formation).annotate(nb_inscrits=Count("inscriptions")).order_by("-date_debut")
    return render(request, "formations/fiche.html", {
        "formation": formation,
        "sessions": sessions,
        "breadcrumbs": [
            {"url": "/formations/", "label": "Formations"},
            {"label": formation.nom},
        ],
    })


# ── Sessions ────────────────────────────────────────────────

@login_required
def sessions_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "sessions/liste.html", {"sessions": []})
    qs = SessionFormation.objects.filter(etablissement=etab).select_related("formation")
    return render(request, "sessions/liste.html", {
        "sessions": qs.annotate(nb_inscrits=Count("inscriptions")).order_by("-date_debut")[:50],
    })


@login_required
def session_creer(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")
    formations = Formation.objects.filter(etablissement=etab, statut="PUBLIE")
    if request.method == "POST":
        from django_formation.services.sessions import creer_session
        try:
            formation = Formation.objects.get(id=request.POST["formation_id"], etablissement=etab)
            session = creer_session(
                etablissement=etab,
                formation=formation,
                code=request.POST["code"],
                nom=request.POST.get("nom", ""),
                date_debut=request.POST.get("date_debut"),
                date_fin=request.POST.get("date_fin"),
                capacite=request.POST.get("capacite", 0),
                cree_par=request.user,
            )
            messages.success(request, f"Session {session.code} créée.")
            return redirect("session_fiche", id=session.id)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "sessions/formulaire.html", {"formations": formations, "mode": "creer"})


@login_required
def session_fiche(request, id):
    etab = getattr(request, "etablissement_actif", None)
    session = get_object_or_404(SessionFormation, id=id, etablissement=etab)
    inscriptions = Inscription.objects.filter(session=session).select_related("apprenant").order_by("-created_at")
    return render(request, "sessions/fiche.html", {
        "session": session,
        "inscriptions": inscriptions,
        "breadcrumbs": [
            {"url": "/sessions/", "label": "Sessions"},
            {"label": session.nom or session.code},
        ],
    })


# ── Inscriptions ────────────────────────────────────────────

@login_required
def inscriptions_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "inscriptions/liste.html", {"inscriptions": []})
    qs = Inscription.objects.filter(etablissement=etab).select_related("apprenant", "session", "session__formation")
    return render(request, "inscriptions/liste.html", {
        "inscriptions": qs.order_by("-created_at")[:50],
    })


@login_required
def inscription_creer(request, apprenant_id=None):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")
    apprenant = None
    if apprenant_id:
        apprenant = get_object_or_404(Apprenant, id=apprenant_id, etablissement=etab)
    apprenants = Apprenant.objects.filter(etablissement=etab, statut="ACTIF").order_by("nom", "prenom")
    sessions = SessionFormation.objects.filter(etablissement=etab).exclude(statut="TERMINE").select_related("formation")
    if request.method == "POST":
        try:
            etab_ref = etab
            apprenant = Apprenant.objects.get(id=request.POST["apprenant_id"], etablissement=etab_ref)
            session = SessionFormation.objects.get(id=request.POST["session_id"], etablissement=etab_ref)
            inscription = inscription_service.creer_inscription(
                etablissement=etab_ref,
                apprenant=apprenant,
                session=session,
                cree_par=request.user,
            )
            messages.success(request, f"Inscription {inscription.numero} créée.")
            return redirect("inscription_fiche", id=inscription.id)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "inscriptions/formulaire.html", {
        "apprenant": apprenant,
        "apprenants": apprenants,
        "sessions": sessions,
        "mode": "creer",
    })


@login_required
def inscription_fiche(request, id):
    etab = getattr(request, "etablissement_actif", None)
    inscription = get_object_or_404(Inscription, id=id, etablissement=etab)
    return render(request, "inscriptions/fiche.html", {
        "inscription": inscription,
        "breadcrumbs": [
            {"url": "/inscriptions/", "label": "Inscriptions"},
            {"label": inscription.numero},
        ],
    })
