from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.contrib import messages
from django.utils import timezone
from django_formation.models import Apprenant
from django_autoecole.models import ExamenAutoEcole, DossierAutoEcole
from django_autoecole.constants import StatutExamen, TypeExamen, StatutDossier
from django_autoecole.services import examens as examens_service


@login_required
def examens_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "autoecole/examens/liste.html", {"examens": []})

    qs = ExamenAutoEcole.objects.filter(etablissement=etab).select_related(
        "dossier__inscription__apprenant", "dossier__categorie_permis"
    ).order_by("-date_examen")

    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(
            Q(dossier__inscription__apprenant__nom__icontains=q) |
            Q(dossier__inscription__apprenant__prenom__icontains=q) |
            Q(numero_convocation__icontains=q)
        )
    statut = request.GET.get("statut", "")
    if statut:
        qs = qs.filter(statut=statut)
    type_examen = request.GET.get("type", "")
    if type_examen:
        qs = qs.filter(type_examen=type_examen)

    stats = {
        "total": qs.count(),
        "planifies": qs.filter(statut__in=[StatutExamen.PLANIFIE, StatutExamen.CONFIRME]).count(),
        "admis": qs.filter(resultat="ADMIS").count(),
        "attente": qs.filter(statut=StatutExamen.RESULTAT_DISPONIBLE, resultat__in=["EN_ATTENTE", ""]).count(),
    }

    return render(request, "autoecole/examens/liste.html", {
        "examens": qs[:50],
        "stats": stats,
        "q": q,
        "statut": statut,
        "type_examen": type_examen,
        "StatutExamen": StatutExamen,
        "TypeExamen": TypeExamen,
        "breadcrumbs": [{"label": "Examens"}],
    })


@login_required
def examen_creer(request):
    etab = getattr(request, "etablissement_actif", None)
    dossiers = DossierAutoEcole.objects.filter(
        etablissement=etab,
        statut__in=[StatutDossier.EN_FORMATION, StatutDossier.PRET_EXAMEN],
    ).select_related("inscription__apprenant", "categorie_permis", "moniteur_referent")

    if request.method == "POST":
        dossier_id = request.POST.get("dossier")
        type_examen = request.POST.get("type_examen")
        date_examen = request.POST.get("date_examen")
        heure_examen = request.POST.get("heure_examen")
        centre_examen = request.POST.get("centre_examen", "")
        numero_convocation = request.POST.get("numero_convocation", "")
        observation = request.POST.get("observation", "")

        try:
            date_iso = f"{date_examen}T{heure_examen}:00" if heure_examen else f"{date_examen}T08:00:00"
            examen = examens_service.planifier_examen(
                dossier_id=dossier_id,
                type_examen=type_examen,
                date_examen=date_iso,
                centre_examen=centre_examen,
                numero_convocation=numero_convocation,
                observation=observation,
                cree_par=request.user,
            )
            messages.success(request, "Examen planifié avec succès.")
            return redirect("examen_fiche", id=examen.id)
        except Exception as e:
            messages.error(request, str(e))

    return render(request, "autoecole/examens/formulaire.html", {
        "dossiers": dossiers,
        "TypeExamen": TypeExamen,
        "breadcrumbs": [
            {"url": "/examens/", "label": "Examens"},
            {"label": "Planifier un examen"},
        ],
    })


@login_required
def examen_fiche(request, id):
    etab = getattr(request, "etablissement_actif", None)
    examen = get_object_or_404(
        ExamenAutoEcole.objects.select_related(
            "dossier__inscription__apprenant", "dossier__categorie_permis",
            "dossier__moniteur_referent",
        ),
        id=id, etablissement=etab,
    )
    return render(request, "autoecole/examens/fiche.html", {
        "examen": examen,
        "StatutExamen": StatutExamen,
        "TypeExamen": TypeExamen,
        "StatutDossier": StatutDossier,
        "breadcrumbs": [
            {"url": "/examens/", "label": "Examens"},
            {"label": f"Examen #{examen.numero_convocation or examen.id}"},
        ],
    })


@login_required
def examen_confirmer(request, id):
    etab = getattr(request, "etablissement_actif", None)
    examen = get_object_or_404(ExamenAutoEcole, id=id, etablissement=etab)
    try:
        examens_service.confirmer_examen(examen)
        messages.success(request, "Examen confirmé.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("examen_fiche", id=id)


@login_required
def examen_presenter(request, id):
    etab = getattr(request, "etablissement_actif", None)
    examen = get_object_or_404(ExamenAutoEcole, id=id, etablissement=etab)
    try:
        examens_service.marquer_candidat_presente(examen)
        messages.success(request, "Candidat marqué présent.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("examen_fiche", id=id)


@login_required
def examen_absent(request, id):
    etab = getattr(request, "etablissement_actif", None)
    examen = get_object_or_404(ExamenAutoEcole, id=id, etablissement=etab)
    try:
        examens_service.marquer_candidat_absent(examen)
        messages.success(request, "Candidat marqué absent.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("examen_fiche", id=id)


@login_required
def examen_annuler(request, id):
    etab = getattr(request, "etablissement_actif", None)
    examen = get_object_or_404(ExamenAutoEcole, id=id, etablissement=etab)
    try:
        examens_service.annuler_examen(examen)
        messages.success(request, "Examen annulé.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("examen_fiche", id=id)


@login_required
def examen_resultat(request, id):
    etab = getattr(request, "etablissement_actif", None)
    examen = get_object_or_404(
        ExamenAutoEcole.objects.select_related("dossier"),
        id=id, etablissement=etab,
    )

    if request.method == "POST":
        resultat = request.POST.get("resultat")
        score = request.POST.get("score")
        observation = request.POST.get("observation", "")
        try:
            examens_service.enregistrer_resultat_examen(
                examen, resultat,
                score=float(score) if score else None,
                observation=observation,
            )
            messages.success(request, "Résultat enregistré.")
            return redirect("examen_fiche", id=id)
        except Exception as e:
            messages.error(request, str(e))

    return render(request, "autoecole/examens/resultat.html", {
        "examen": examen,
        "breadcrumbs": [
            {"url": "/examens/", "label": "Examens"},
            {"url": f"/examens/{examen.id}/", "label": f"Examen #{examen.numero_convocation or examen.id}"},
            {"label": "Résultat"},
        ],
    })
