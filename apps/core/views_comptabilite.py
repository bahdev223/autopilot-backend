from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum

from comptabilite_ohada.models import (
    CompteComptable, EcritureComptable, LigneEcritureComptable,
    JournalComptable, ExerciceComptable, Immobilisation, PlanAmortissement,
    ReleveBancaire, LigneReleveBancaire, ConfigurationComptable,
)
from comptabilite_ohada.services.dashboard_service import DashboardService
from comptabilite_ohada.services.ecriture_service import EcritureService
from comptabilite_ohada.services.exercice_service import ExerciceService
from comptabilite_ohada.services.journal_service import BalanceService, GrandLivreService, JournalService
from comptabilite_ohada.services.bilan_service import BilanService


@login_required
def comptabilite_dashboard(request):
    service = DashboardService()
    context = {
        "total_ecritures": service.compter_ecritures(),
        "ecritures_non_validees": service.compter_ecritures_non_validees(),
        "dernieres_ecritures": service.dernieres_ecritures(),
        "exercice_courant": service.exercice_courant(),
        "totaux_par_journal": service.totaux_par_journal(),
    }
    return render(request, "comptabilite/dashboard.html", context)


@login_required
def ecritures_liste(request):
    qs = EcritureComptable.objects.select_related("journal", "exercice").prefetch_related("lignes__compte")
    status = request.GET.get("status")
    if status == "validee":
        qs = qs.filter(validee=True)
    elif status == "non_validee":
        qs = qs.filter(validee=False)
    q = request.GET.get("q")
    if q:
        qs = qs.filter(Q(reference__icontains=q) | Q(libelle__icontains=q))
    stats = {
        "total": qs.count(),
        "validees": qs.filter(validee=True).count(),
        "non_validees": qs.filter(validee=False).count(),
    }
    return render(request, "comptabilite/ecritures_liste.html", {
        "ecritures": qs.order_by("-date_ecriture", "-created_at")[:50],
        "stats": stats,
        "status": status,
        "q": q,
    })


@login_required
def ecriture_creer(request):
    if request.method == "POST":
        try:
            ecriture = EcritureService.creer_ecriture(
                journal_id=request.POST["journal_id"],
                date_ecriture=request.POST["date_ecriture"],
                libelle=request.POST["libelle"],
                reference=request.POST.get("reference", ""),
                lignes_data=[],
                user=request.user,
            )
            messages.success(request, "Écriture créée.")
            return redirect("ecriture_fiche", id=ecriture.pk)
        except Exception as e:
            messages.error(request, str(e))
    journaux = JournalComptable.objects.filter(actif=True)
    exercices = ExerciceComptable.objects.filter(cloture=False)
    return render(request, "comptabilite/ecriture_formulaire.html", {
        "mode": "creer", "journaux": journaux, "exercices": exercices,
    })


@login_required
def ecriture_fiche(request, id):
    ecriture = get_object_or_404(
        EcritureComptable.objects.select_related("journal", "exercice").prefetch_related("lignes__compte"),
        pk=id,
    )
    return render(request, "comptabilite/ecriture_fiche.html", {
        "ecriture": ecriture,
        "breadcrumbs": [
            {"url": "/comptabilite/ecritures/", "label": "Écritures"},
            {"label": ecriture.reference},
        ],
    })


@login_required
def ecriture_modifier(request, id):
    ecriture = get_object_or_404(EcritureComptable, pk=id)
    if ecriture.validee:
        messages.error(request, "Impossible de modifier une écriture validée.")
        return redirect("ecriture_fiche", id=ecriture.pk)
    if request.method == "POST":
        ecriture.journal_id = request.POST.get("journal_id", ecriture.journal_id)
        ecriture.date_ecriture = request.POST.get("date_ecriture", ecriture.date_ecriture)
        ecriture.libelle = request.POST.get("libelle", ecriture.libelle)
        ecriture.save()
        messages.success(request, "Écriture mise à jour.")
        return redirect("ecriture_fiche", id=ecriture.pk)
    journaux = JournalComptable.objects.filter(actif=True)
    return render(request, "comptabilite/ecriture_formulaire.html", {
        "mode": "modifier", "ecriture": ecriture, "journaux": journaux,
    })


@login_required
def ecriture_supprimer(request, id):
    ecriture = get_object_or_404(EcritureComptable, pk=id)
    if ecriture.validee:
        messages.error(request, "Impossible de supprimer une écriture validée.")
        return redirect("ecriture_fiche", id=ecriture.pk)
    if request.method == "POST":
        ecriture.delete()
        messages.success(request, "Écriture supprimée.")
        return redirect("ecritures_liste")
    return render(request, "comptabilite/ecriture_supprimer.html", {"ecriture": ecriture})


@login_required
def ecriture_valider(request, id):
    ecriture = get_object_or_404(EcritureComptable, pk=id)
    if request.method == "POST":
        try:
            EcritureService.valider_ecriture(ecriture, request.user)
            messages.success(request, "Écriture validée.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect("ecriture_fiche", id=ecriture.pk)


@login_required
def comptes_liste(request):
    qs = CompteComptable.objects.all()
    classe = request.GET.get("classe")
    if classe:
        qs = qs.filter(code__startswith=classe)
    actif = request.GET.get("actif")
    if actif is not None:
        qs = qs.filter(actif=(actif == "1"))
    q = request.GET.get("q")
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(libelle__icontains=q))
    return render(request, "comptabilite/comptes_liste.html", {
        "comptes": qs.order_by("code"),
        "classe": classe, "actif": actif, "q": q,
    })


@login_required
def compte_fiche(request, id):
    compte = get_object_or_404(CompteComptable, pk=id)
    lignes = LigneEcritureComptable.objects.filter(compte=compte).select_related("ecriture")[:50]
    total_debit = lignes.aggregate(s=Sum("debit"))["s"] or 0
    total_credit = lignes.aggregate(s=Sum("credit"))["s"] or 0
    solde = total_debit - total_credit
    return render(request, "comptabilite/compte_fiche.html", {
        "compte": compte, "lignes": lignes,
        "total_debit": total_debit, "total_credit": total_credit, "solde": solde,
        "breadcrumbs": [
            {"url": "/comptabilite/comptes/", "label": "Comptes"},
            {"label": f"{compte.code} - {compte.libelle}"},
        ],
    })


@login_required
def journaux_liste(request):
    journaux = JournalComptable.objects.annotate(
        nb_ecritures=Sum("ecritures__pk")
    )
    return render(request, "comptabilite/journaux_liste.html", {"journaux": journaux})


@login_required
def journal_fiche(request, id):
    journal = get_object_or_404(JournalComptable, pk=id)
    ecritures = EcritureComptable.objects.filter(journal=journal).select_related("exercice").order_by("-date_ecriture")[:50]
    return render(request, "comptabilite/journal_fiche.html", {
        "journal": journal, "ecritures": ecritures,
        "breadcrumbs": [
            {"url": "/comptabilite/journaux/", "label": "Journaux"},
            {"label": journal.libelle},
        ],
    })


@login_required
def balance(request):
    service = BalanceService()
    exercice_id = request.GET.get("exercice")
    exercice = ExerciceComptable.objects.filter(pk=exercice_id).first() if exercice_id else None
    data = service.balance(exercice=exercice)
    total_debit = sum(l["total_debit"] for l in data)
    total_credit = sum(l["total_credit"] for l in data)
    exercices = ExerciceComptable.objects.all()
    return render(request, "comptabilite/balance.html", {
        "balance": data, "total_debit": total_debit, "total_credit": total_credit,
        "exercices": exercices, "exercice_id": exercice_id,
    })


@login_required
def grand_livre(request):
    service = GrandLivreService()
    compte_code = request.GET.get("compte")
    exercice_id = request.GET.get("exercice")
    exercice = ExerciceComptable.objects.filter(pk=exercice_id).first() if exercice_id else None
    lignes = service.grand_livre(compte_code=compte_code, exercice=exercice)
    comptes = CompteComptable.objects.filter(est_mouvement=True).order_by("code")
    exercices = ExerciceComptable.objects.all()
    return render(request, "comptabilite/grand_livre.html", {
        "lignes": lignes, "comptes": comptes, "exercices": exercices,
        "compte_code": compte_code, "exercice_id": exercice_id,
    })


@login_required
def bilan(request):
    service = BilanService()
    exercice_id = request.GET.get("exercice")
    data = service.bilan(exercice=exercice_id) if exercice_id else service.bilan()
    resultat = service.compte_resultat(exercice=exercice_id) if exercice_id else service.compte_resultat()
    exercices = ExerciceComptable.objects.all()
    return render(request, "comptabilite/bilan.html", {
        "bilan": data, "resultat": resultat, "exercices": exercices, "exercice_id": exercice_id,
    })


@login_required
def compte_resultat(request):
    service = BilanService()
    exercice_id = request.GET.get("exercice")
    resultat = service.compte_resultat(exercice=exercice_id) if exercice_id else service.compte_resultat()
    exercices = ExerciceComptable.objects.all()
    return render(request, "comptabilite/compte_resultat.html", {
        "resultat": resultat, "exercices": exercices, "exercice_id": exercice_id,
    })


@login_required
def exercices_liste(request):
    exercices = ExerciceComptable.objects.all()
    return render(request, "comptabilite/exercices_liste.html", {"exercices": exercices})


@login_required
def exercice_creer(request):
    if request.method == "POST":
        try:
            exercice = ExerciceService.creer(
                code=request.POST["code"],
                date_debut=request.POST["date_debut"],
                date_fin=request.POST["date_fin"],
            )
            messages.success(request, "Exercice créé.")
            return redirect("exercice_fiche", id=exercice.pk)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "comptabilite/exercice_formulaire.html", {"mode": "creer"})


@login_required
def exercice_fiche(request, id):
    exercice = get_object_or_404(ExerciceComptable, pk=id)
    return render(request, "comptabilite/exercice_fiche.html", {
        "exercice": exercice,
        "breadcrumbs": [
            {"url": "/comptabilite/exercices/", "label": "Exercices"},
            {"label": exercice.code},
        ],
    })


@login_required
def exercice_cloturer(request, id):
    exercice = get_object_or_404(ExerciceComptable, pk=id)
    if request.method == "POST":
        try:
            ExerciceService.cloturer(exercice, request.user)
            messages.success(request, "Exercice clôturé.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect("exercice_fiche", id=exercice.pk)


@login_required
def exercice_rouvrir(request, id):
    exercice = get_object_or_404(ExerciceComptable, pk=id)
    if request.method == "POST":
        try:
            ExerciceService.rouvrir(exercice)
            messages.success(request, "Exercice rouvert.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect("exercice_fiche", id=exercice.pk)


@login_required
def immobilisations_liste(request):
    immobilisations = Immobilisation.objects.select_related("compte_immobilisation").all()
    return render(request, "comptabilite/immobilisations_liste.html", {"immobilisations": immobilisations})


@login_required
def immobilisation_fiche(request, id):
    immobilisation = get_object_or_404(
        Immobilisation.objects.select_related("compte_immobilisation", "compte_amortissement", "compte_charge"),
        pk=id,
    )
    plan = PlanAmortissement.objects.filter(immobilisation=immobilisation)
    return render(request, "comptabilite/immobilisation_fiche.html", {
        "immobilisation": immobilisation, "plan": plan,
        "breadcrumbs": [
            {"url": "/comptabilite/immobilisations/", "label": "Immobilisations"},
            {"label": immobilisation.libelle},
        ],
    })


@login_required
def rapprochement_liste(request):
    releves = ReleveBancaire.objects.all()
    return render(request, "comptabilite/rapprochement_liste.html", {"releves": releves})


@login_required
def rapprochement_fiche(request, id):
    releve = get_object_or_404(
        ReleveBancaire.objects.prefetch_related("lignes"),
        pk=id,
    )
    return render(request, "comptabilite/rapprochement_fiche.html", {
        "releve": releve,
        "breadcrumbs": [
            {"url": "/comptabilite/rapprochement/", "label": "Rapprochement"},
            {"label": f"Relevé {releve.compte_comptable_code}"},
        ],
    })
