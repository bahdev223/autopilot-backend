from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone

from django_autoecole.models import (
    CategoriePermis, DossierAutoEcole, Moniteur, Vehicule,
    LeconConduite, EvaluationLecon, ExamenAutoEcole,
    IndisponibiliteMoniteur, IndisponibiliteVehicule,
)
from django_autoecole.constants import (
    StatutDossier, StatutLecon, StatutVehicule, StatutMoniteur,
)
from django_autoecole.services import categories as cat_svc
from django_autoecole.services import vehicules as veh_svc
from django_autoecole.services import moniteurs as mon_svc
from django_autoecole.services import dossiers as dos_svc


# ── Catégories de permis ────────────────────────────────────

@login_required
def categories_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "autoecole/categories_permis/liste.html", {"categories": []})
    qs = CategoriePermis.objects.filter(etablissement=etab)
    return render(request, "autoecole/categories_permis/liste.html", {
        "categories": qs.order_by("code"),
    })


@login_required
def categorie_creer(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")
    if request.method == "POST":
        try:
            cat = CategoriePermis.objects.create(
                etablissement=etab,
                code=request.POST["code"],
                nom=request.POST["nom"],
                description=request.POST.get("description", ""),
                heures_theorie_minimum=request.POST.get("heures_theorie", 0),
                heures_conduite_minimum=request.POST.get("heures_conduite", 0),
                nombre_evaluations_minimum=request.POST.get("nb_evaluations", 0),
                actif=True,
            )
            messages.success(request, f"Catégorie {cat.code} créée.")
            return redirect("categories_liste")
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "autoecole/categories_permis/formulaire.html", {"mode": "creer"})


@login_required
def categorie_activer(request, id):
    etab = getattr(request, "etablissement_actif", None)
    cat = get_object_or_404(CategoriePermis, id=id, etablissement=etab)
    cat_svc.activer_categorie_permis(cat)
    messages.success(request, f"Catégorie {cat.code} activée.")
    return redirect("categories_liste")


@login_required
def categorie_desactiver(request, id):
    etab = getattr(request, "etablissement_actif", None)
    cat = get_object_or_404(CategoriePermis, id=id, etablissement=etab)
    cat_svc.desactiver_categorie_permis(cat)
    messages.success(request, f"Catégorie {cat.code} désactivée.")
    return redirect("categories_liste")


# ── Dossiers candidats ──────────────────────────────────────

@login_required
def dossiers_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "autoecole/dossiers/liste.html", {"dossiers": []})
    qs = DossierAutoEcole.objects.filter(etablissement=etab).select_related(
        "inscription__apprenant", "categorie_permis", "moniteur_referent"
    )
    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(Q(numero_dossier__icontains=q) | Q(inscription__apprenant__nom__icontains=q))
    statut = request.GET.get("statut", "")
    if statut:
        qs = qs.filter(statut=statut)
    return render(request, "autoecole/dossiers/liste.html", {
        "dossiers": qs.order_by("-date_ouverture")[:50],
        "q": q,
        "statut": statut,
    })


@login_required
def dossier_fiche(request, id):
    etab = getattr(request, "etablissement_actif", None)
    dossier = get_object_or_404(DossierAutoEcole, id=id, etablissement=etab)
    lecons = LeconConduite.objects.filter(dossier=dossier).select_related("moniteur", "vehicule").order_by("-date_debut")
    examens = ExamenAutoEcole.objects.filter(dossier=dossier).order_by("-date_examen")
    return render(request, "autoecole/dossiers/fiche.html", {
        "dossier": dossier,
        "lecons": lecons,
        "examens": examens,
        "breadcrumbs": [
            {"url": "/autoecole/dossiers/", "label": "Dossiers"},
            {"label": dossier.numero_dossier},
        ],
    })


@login_required
def dossier_ouvrir(request, id):
    etab = getattr(request, "etablissement_actif", None)
    dossier = get_object_or_404(DossierAutoEcole, id=id, etablissement=etab)
    try:
        dos_svc.ouvrir_dossier(dossier, modifie_par=request.user)
        messages.success(request, f"Dossier {dossier.numero_dossier} ouvert.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("dossier_fiche", id=dossier.id)


@login_required
def dossier_demarrer_formation(request, id):
    etab = getattr(request, "etablissement_actif", None)
    dossier = get_object_or_404(DossierAutoEcole, id=id, etablissement=etab)
    try:
        dos_svc.demarrer_formation_dossier(dossier, modifie_par=request.user)
        messages.success(request, "Formation démarrée.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("dossier_fiche", id=dossier.id)


@login_required
def dossier_declarer_pret(request, id):
    etab = getattr(request, "etablissement_actif", None)
    dossier = get_object_or_404(DossierAutoEcole, id=id, etablissement=etab)
    try:
        dos_svc.declarer_dossier_pret_examen(dossier, modifie_par=request.user)
        messages.success(request, "Dossier déclaré prêt pour l'examen.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("dossier_fiche", id=dossier.id)


# ── Moniteurs ───────────────────────────────────────────────

@login_required
def moniteurs_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "autoecole/moniteurs/liste.html", {"moniteurs": []})
    qs = Moniteur.objects.filter(etablissement=etab).prefetch_related("categories_permis")
    return render(request, "autoecole/moniteurs/liste.html", {
        "moniteurs": qs.order_by("nom", "prenom")[:50],
    })


@login_required
def moniteur_creer(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")
    categories = CategoriePermis.objects.filter(etablissement=etab)
    if request.method == "POST":
        try:
            moniteur = mon_svc.creer_moniteur(
                etablissement=etab,
                matricule=request.POST["matricule"],
                nom=request.POST["nom"],
                prenom=request.POST["prenom"],
                telephone=request.POST.get("telephone", ""),
                email=request.POST.get("email", ""),
                numero_agrement=request.POST.get("numero_agrement", ""),
                date_embauche=request.POST.get("date_embauche") or None,
                cree_par=request.user,
            )
            cat_ids = request.POST.getlist("categories_permis")
            if cat_ids:
                moniteur.categories_permis.set(cat_ids)
            messages.success(request, f"Moniteur {moniteur.nom_complet} créé.")
            return redirect("moniteur_fiche", id=moniteur.id)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "autoecole/moniteurs/formulaire.html", {
        "categories": categories,
        "mode": "creer",
        "breadcrumbs": [
            {"url": "/autoecole/moniteurs/", "label": "Moniteurs"},
            {"label": "Nouveau"},
        ],
    })


@login_required
def moniteur_fiche(request, id):
    etab = getattr(request, "etablissement_actif", None)
    moniteur = get_object_or_404(Moniteur, id=id, etablissement=etab)
    lecons_jour = LeconConduite.objects.filter(
        moniteur=moniteur, date_debut__date=timezone.localdate()
    ).select_related("dossier", "dossier__inscription__apprenant").order_by("date_debut")
    return render(request, "autoecole/moniteurs/fiche.html", {
        "moniteur": moniteur,
        "lecons_jour": lecons_jour,
        "breadcrumbs": [
            {"url": "/autoecole/moniteurs/", "label": "Moniteurs"},
            {"label": moniteur.nom_complet},
        ],
    })


@login_required
def moniteur_activer(request, id):
    etab = getattr(request, "etablissement_actif", None)
    m = get_object_or_404(Moniteur, id=id, etablissement=etab)
    mon_svc.activer_moniteur(m)
    messages.success(request, f"{m.nom_complet} activé.")
    return redirect("moniteur_fiche", id=m.id)


@login_required
def moniteur_indisponible(request, id):
    etab = getattr(request, "etablissement_actif", None)
    m = get_object_or_404(Moniteur, id=id, etablissement=etab)
    mon_svc.rendre_moniteur_indisponible(m)
    messages.success(request, f"{m.nom_complet} marqué indisponible.")
    return redirect("moniteur_fiche", id=m.id)


# ── Véhicules ───────────────────────────────────────────────

@login_required
def vehicules_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "autoecole/vehicules/liste.html", {"vehicules": []})
    qs = Vehicule.objects.filter(etablissement=etab).select_related("categorie_permis")
    return render(request, "autoecole/vehicules/liste.html", {
        "vehicules": qs.order_by("immatriculation")[:50],
    })


@login_required
def vehicule_creer(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")
    categories = CategoriePermis.objects.filter(etablissement=etab)
    if request.method == "POST":
        try:
            vehicule = veh_svc.creer_vehicule(
                etablissement=etab,
                categorie_permis_id=request.POST["categorie_permis_id"],
                immatriculation=request.POST["immatriculation"],
                marque=request.POST["marque"],
                modele=request.POST["modele"],
                annee=request.POST.get("annee") or None,
                couleur=request.POST.get("couleur", ""),
                type_boite=request.POST.get("type_boite", "MANUELLE"),
                type_carburant=request.POST.get("type_carburant", ""),
                kilometrage=int(request.POST.get("kilometrage", 0)),
                cree_par=request.user,
            )
            messages.success(request, f"Véhicule {vehicule.immatriculation} créé.")
            return redirect("vehicule_fiche", id=vehicule.id)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "autoecole/vehicules/formulaire.html", {
        "categories": categories,
        "mode": "creer",
        "breadcrumbs": [
            {"url": "/autoecole/vehicules/", "label": "Véhicules"},
            {"label": "Nouveau"},
        ],
    })


@login_required
def vehicule_fiche(request, id):
    etab = getattr(request, "etablissement_actif", None)
    vehicule = get_object_or_404(Vehicule, id=id, etablissement=etab)
    return render(request, "autoecole/vehicules/fiche.html", {
        "vehicule": vehicule,
        "breadcrumbs": [
            {"url": "/autoecole/vehicules/", "label": "Véhicules"},
            {"label": vehicule.immatriculation},
        ],
    })
