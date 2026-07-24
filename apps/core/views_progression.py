from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone

from django_formation.models import Apprenant
from django_autoecole.models import EvaluationLecon, LeconConduite, DossierAutoEcole
from django_autoecole.constants import StatutLecon, StatutDossier


@login_required
def evaluations_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "autoecole/evaluations/liste.html", {"evaluations": []})

    qs = EvaluationLecon.objects.filter(
        lecon__etablissement=etab
    ).select_related(
        "lecon__dossier__inscription__apprenant", "moniteur", "lecon"
    )
    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(
            Q(lecon__dossier__inscription__apprenant__nom__icontains=q) |
            Q(lecon__dossier__inscription__apprenant__prenom__icontains=q) |
            Q(moniteur__nom__icontains=q)
        )
    note_min = request.GET.get("note_min", "")
    if note_min:
        qs = qs.filter(note_globale__gte=note_min)
    recommande = request.GET.get("recommande", "")
    if recommande:
        qs = qs.filter(recommande_examen=(recommande == "oui"))

    stats = {
        "total": qs.count(),
        "moyenne": qs.aggregate(avg=Avg("note_globale"))["avg"] or 0,
        "recommande": qs.filter(recommande_examen=True).count(),
    }

    return render(request, "autoecole/evaluations/liste.html", {
        "evaluations": qs.order_by("-created_at")[:50],
        "stats": stats,
        "q": q,
        "note_min": note_min,
        "recommande": recommande,
        "breadcrumbs": [{"label": "Évaluations"}],
    })


@login_required
def evaluation_fiche(request, id):
    etab = getattr(request, "etablissement_actif", None)
    evaluation = get_object_or_404(
        EvaluationLecon, id=id, lecon__etablissement=etab
    )
    return render(request, "autoecole/evaluations/fiche.html", {
        "evaluation": evaluation,
        "breadcrumbs": [
            {"url": "/evaluations/", "label": "Évaluations"},
            {"label": f"Éval. #{evaluation.id}"},
        ],
    })


@login_required
def progression_apprenant(request, id):
    etab = getattr(request, "etablissement_actif", None)
    apprenant = get_object_or_404(Apprenant, id=id, etablissement=etab)

    dossiers = DossierAutoEcole.objects.filter(
        etablissement=etab, inscription__apprenant=apprenant
    ).select_related("categorie_permis", "moniteur_referent")

    lecons = LeconConduite.objects.filter(
        dossier__inscription__apprenant=apprenant, etablissement=etab
    ).select_related("moniteur").order_by("-date_debut")

    total_heures = lecons.filter(statut=StatutLecon.REALISEE).count() * 60  # approx minutes
    heures_conduite = lecons.filter(
        statut=StatutLecon.REALISEE,
        type_lecon__in=["CONDUITE", "MANOEUVRE", "CIRCULATION"]
    ).count() * 60

    evaluations = EvaluationLecon.objects.filter(
        lecon__dossier__inscription__apprenant=apprenant
    ).select_related("moniteur", "lecon").order_by("-created_at")

    competences = {}
    for ev in evaluations:
        for c in (ev.competences_acquises or []):
            competences[c] = competences.get(c, 0) + 1

    note_moyenne = evaluations.aggregate(avg=Avg("note_globale"))["avg"] or 0

    return render(request, "autoecole/evaluations/progression.html", {
        "apprenant": apprenant,
        "dossiers": dossiers,
        "lecons": lecons[:30],
        "total_lecons": lecons.count(),
        "lecons_realisees": lecons.filter(statut=StatutLecon.REALISEE).count(),
        "total_heures": total_heures // 60,
        "heures_conduite": heures_conduite // 60,
        "evaluations": evaluations,
        "note_moyenne": note_moyenne,
        "competences": sorted(competences.items(), key=lambda x: -x[1]),
        "recommande_examen": evaluations.filter(recommande_examen=True).exists(),
        "breadcrumbs": [
            {"url": "/apprenants/", "label": "Apprenants"},
            {"url": f"/apprenants/{apprenant.id}/", "label": str(apprenant)},
            {"label": "Progression"},
        ],
    })
