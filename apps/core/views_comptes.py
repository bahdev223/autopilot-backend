from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from comptes.models import Compte, MouvementCompte, TransfertCompte, RapprochementBancaire, JournalCompte, StatutMouvement
from comptes.services import CompteService, MouvementCompteService, TransfertCompteService, RapprochementService, ClotureCompteService, JournalCompteService
from comptes.selectors import DashboardSelector, MouvementSelector


@login_required
def comptes_dashboard(request):
    selector = DashboardSelector()
    comptes = Compte.objects.filter(actif=True).order_by("code")
    synthese = selector.synthese_globale()
    flux = selector.flux_24h()
    mouvements = selector.mouvements_recents(50)
    transferts = selector.transferts_recents(20)
    alertes = selector.alertes()
    return render(request, "comptes/dashboard.html", {
        "comptes": comptes, "synthese": synthese,
        "flux_net": flux["flux_net"], "entrees_24h": flux["entrees"], "sorties_24h": flux["sorties"],
        "mouvements": mouvements, "transferts": transferts, "alertes": alertes,
    })


@login_required
def comptes_liste(request):
    comptes = Compte.objects.filter(actif=True).order_by("code")
    selector = DashboardSelector()
    synthese = selector.synthese_globale()
    return render(request, "comptes/liste_comptes.html", {"comptes": comptes, "synthese": synthese})


@login_required
def compte_creer(request):
    if request.method == "POST":
        try:
            compte = CompteService.creer(
                code=request.POST["code"], nom=request.POST["nom"],
                type_compte=request.POST.get("type", "ESPECES"),
                solde_initial=request.POST.get("solde_initial", 0),
                actif=request.POST.get("actif") == "on",
                role=request.POST.get("role", ""),
                devise=request.POST.get("devise", "XOF"),
                compte_comptable_code=request.POST.get("compte_comptable_code", ""),
            )
            messages.success(request, f'Compte "{compte.nom}" créé.')
            return redirect("compte_detail", compte_id=compte.id)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "comptes/form_compte.html", {"mode": "ajout"})


@login_required
def compte_detail(request, compte_id):
    compte = get_object_or_404(Compte, id=compte_id)
    historiques = compte.historique.all()[:20]
    return render(request, "comptes/detail_compte.html", {
        "compte": compte, "historiques": historiques,
        "breadcrumbs": [
            {"url": "/comptes/", "label": "Comptes"},
            {"label": compte.nom},
        ],
    })


@login_required
def compte_modifier(request, compte_id):
    compte = get_object_or_404(Compte, id=compte_id)
    if request.method == "POST":
        try:
            CompteService.modifier(compte,
                nom=request.POST.get("nom"), type=request.POST.get("type"),
                role=request.POST.get("role", ""), actif=request.POST.get("actif") == "on",
                autoriser_decouvert=request.POST.get("autoriser_decouvert") == "on",
                limite_decouvert=request.POST.get("limite_decouvert", 0),
                compte_comptable_code=request.POST.get("compte_comptable_code", ""),
            )
            messages.success(request, f'Compte "{compte.nom}" modifié.')
            return redirect("compte_detail", compte_id=compte.id)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "comptes/form_compte.html", {"mode": "modification", "compte": compte})


@login_required
def compte_cloturer(request, compte_id):
    compte = get_object_or_404(Compte, id=compte_id, actif=True)
    if request.method == "POST":
        try:
            ClotureCompteService.cloturer(compte=compte, solde_reel=request.POST.get("solde_reel"), user=request.user, commentaire=request.POST.get("commentaire", ""))
            messages.success(request, f"Clôture de {compte.nom} effectuée.")
            return redirect("compte_journal", compte_id=compte.id)
        except Exception as e:
            messages.error(request, str(e))
    journal_ouvert = JournalCompte.objects.filter(compte=compte, cloture=False).first()
    return render(request, "comptes/cloture.html", {"compte": compte, "journal": journal_ouvert})


@login_required
def compte_journal(request, compte_id=None):
    from datetime import date
    date_journal = date.today()
    if compte_id:
        compte = get_object_or_404(Compte, id=compte_id, actif=True)
        journal = JournalCompteService.obtenir_ou_creer(compte, date_journal)
        lignes = journal.lignes.all()
        JournalCompteService.alimenter_lignes(journal)
    else:
        journal, lignes, compte = None, [], None
    journaux_ouverts = JournalCompte.objects.filter(cloture=False).select_related("compte")
    return render(request, "comptes/journal.html", {
        "journal": journal, "lignes": lignes, "compte": compte,
        "date_journal": date_journal, "journaux_ouverts": journaux_ouverts,
    })


@login_required
def mouvements_liste(request):
    mouvements = MouvementCompte.objects.select_related("compte", "created_by").order_by("-date")[:200]
    comptes = Compte.objects.filter(actif=True).order_by("code")
    return render(request, "comptes/mouvements.html", {
        "mouvements": mouvements, "comptes": comptes,
        "statuts": StatutMouvement.choices,
    })


@login_required
def mouvement_encaisser(request):
    if request.method == "POST":
        try:
            compte = Compte.objects.get(id=request.POST["compte_id"], actif=True)
            MouvementCompteService.encaisser(compte=compte, montant=request.POST["montant"], libelle=request.POST.get("libelle", "Encaissement"), user=request.user, reference=request.POST.get("reference", ""))
            messages.success(request, "Encaissement effectué.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect("comptes_dashboard")


@login_required
def mouvement_decaisser(request):
    if request.method == "POST":
        try:
            compte = Compte.objects.get(id=request.POST["compte_id"], actif=True)
            MouvementCompteService.decaisser(compte=compte, montant=request.POST["montant"], libelle=request.POST.get("libelle", "Décaissement"), user=request.user, reference=request.POST.get("reference", ""))
            messages.success(request, "Décaissement effectué.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect("comptes_dashboard")


@login_required
def transfert_effectuer(request):
    if request.method == "POST":
        try:
            source = Compte.objects.get(id=request.POST["source_id"], actif=True)
            destination = Compte.objects.get(id=request.POST["dest_id"], actif=True)
            TransfertCompteService.transferer(source=source, destination=destination, montant=request.POST["montant"], user=request.user, notes=request.POST.get("notes", ""))
            messages.success(request, "Transfert effectué.")
            return redirect("transferts_liste")
        except Exception as e:
            messages.error(request, str(e))
    comptes = Compte.objects.filter(actif=True).order_by("code")
    return render(request, "comptes/transfert.html", {"comptes": comptes})


@login_required
def transferts_liste(request):
    transferts = TransfertCompte.objects.select_related("source", "destination", "valide_par").order_by("-date")[:100]
    return render(request, "comptes/transfert_liste.html", {"transferts": transferts})


@login_required
def rapprochement_liste(request):
    rapprochements = RapprochementBancaire.objects.select_related("compte").order_by("-date_fin")
    comptes = Compte.objects.filter(type__in=["BANQUE", "MOBILE_MONEY"], actif=True)
    return render(request, "comptes/rapprochement.html", {"rapprochements": rapprochements, "comptes": comptes})


@login_required
def rapprochement_detail(request, rapprochement_id):
    rapprochement = get_object_or_404(RapprochementBancaire.objects.select_related("compte"), id=rapprochement_id)
    lignes = rapprochement.lignes.all().order_by("date_operation")
    return render(request, "comptes/rapprochement_detail.html", {
        "rapprochement": rapprochement, "lignes": lignes,
        "breadcrumbs": [
            {"url": "/comptes/rapprochement/", "label": "Rapprochement"},
            {"label": f"#{rapprochement.id}"},
        ],
    })


@login_required
def rapprochement_initialiser(request):
    if request.method == "POST":
        try:
            compte = Compte.objects.get(id=request.POST["compte_id"], actif=True)
            r = RapprochementService.initialiser(compte=compte, date_debut=request.POST["date_debut"], date_fin=request.POST["date_fin"], solde_releve=request.POST["solde_releve"], date_releve=request.POST.get("date_releve", request.POST["date_fin"]))
            messages.success(request, "Rapprochement initialisé.")
            return redirect("rapprochement_detail", rapprochement_id=r.id)
        except Exception as e:
            messages.error(request, str(e))
    return redirect("rapprochement_bancaire_liste")
