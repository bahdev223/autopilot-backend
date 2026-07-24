from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone

from django_formation.models import Etablissement
from django_autoecole.models import (
    LeconConduite, Moniteur, Vehicule, DossierAutoEcole,
    IndisponibiliteMoniteur, IndisponibiliteVehicule, EvaluationLecon,
)
from django_autoecole.constants import StatutLecon, StatutDossier
from django_autoecole.services import lecons as lecon_svc
from django_autoecole.services import indisponibilites as indispo_svc


# ── Planning ────────────────────────────────────────────────

@login_required
def planning_view(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "autoecole/planning/planning.html", {"semaine": []})

    aujourdhui = timezone.localdate()
    semaine = []
    for i in range(7):
        jour = aujourdhui + timedelta(days=i)
        lecons = LeconConduite.objects.filter(
            etablissement=etab, date_debut__date=jour,
        ).select_related(
            "dossier__inscription__apprenant", "moniteur", "vehicule"
        ).order_by("date_debut")
        semaine.append({"date": jour, "lecons": lecons})

    moniteurs = Moniteur.objects.filter(etablissement=etab, statut="ACTIF")
    return render(request, "autoecole/planning/planning.html", {
        "semaine": semaine,
        "moniteurs": moniteurs,
        "breadcrumbs": [{"label": "Planning"}],
    })


# ── Leçons ──────────────────────────────────────────────────

@login_required
def lecons_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "autoecole/lecons/liste.html", {"lecons": []})

    qs = LeconConduite.objects.filter(etablissement=etab).select_related(
        "dossier__inscription__apprenant", "moniteur", "vehicule"
    )
    date_debut = request.GET.get("date_debut", "")
    date_fin = request.GET.get("date_fin", "")
    moniteur_id = request.GET.get("moniteur", "")
    statut = request.GET.get("statut", "")
    if date_debut:
        qs = qs.filter(date_debut__date__gte=date_debut)
    if date_fin:
        qs = qs.filter(date_debut__date__lte=date_fin)
    if moniteur_id:
        qs = qs.filter(moniteur_id=moniteur_id)
    if statut:
        qs = qs.filter(statut=statut)

    moniteurs = Moniteur.objects.filter(etablissement=etab, statut="ACTIF")
    return render(request, "autoecole/lecons/liste.html", {
        "lecons": qs.order_by("-date_debut")[:50],
        "moniteurs": moniteurs,
        "date_debut": date_debut,
        "date_fin": date_fin,
        "moniteur_id": moniteur_id,
        "statut": statut,
        "breadcrumbs": [{"url": "/planning/", "label": "Planning"}, {"label": "Leçons"}],
    })


@login_required
def lecon_creer(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")
    dossiers = DossierAutoEcole.objects.filter(
        etablissement=etab, statut__in=[StatutDossier.OUVERT, StatutDossier.EN_FORMATION, StatutDossier.PRET_EXAMEN]
    ).select_related("inscription__apprenant", "categorie_permis")
    moniteurs = Moniteur.objects.filter(etablissement=etab, statut="ACTIF").prefetch_related("categories_permis")
    vehicules = Vehicule.objects.filter(etablissement=etab).exclude(statut__in=["HORS_SERVICE", "ARCHIVE"])

    if request.method == "POST":
        try:
            from_dt = timezone.datetime.fromisoformat(request.POST["date_debut"]).replace(tzinfo=timezone.get_current_timezone())
            to_dt = timezone.datetime.fromisoformat(request.POST["date_fin"]).replace(tzinfo=timezone.get_current_timezone())
            lecon = lecon_svc.planifier_lecon(
                dossier_id=request.POST["dossier_id"],
                moniteur_id=request.POST["moniteur_id"],
                vehicule_id=request.POST.get("vehicule_id") or None,
                type_lecon=request.POST["type_lecon"],
                date_debut=from_dt,
                date_fin=to_dt,
                lieu_depart=request.POST.get("lieu_depart", ""),
                lieu_arrivee=request.POST.get("lieu_arrivee", ""),
                cree_par=request.user,
            )
            messages.success(request, f"Leçon planifiée.")
            return redirect("lecon_fiche", id=lecon.id)
        except Exception as e:
            messages.error(request, str(e))

    return render(request, "autoecole/lecons/formulaire.html", {
        "dossiers": dossiers,
        "moniteurs": moniteurs,
        "vehicules": vehicules,
        "mode": "creer",
        "breadcrumbs": [{"url": "/planning/", "label": "Planning"}, {"url": "/lecons/", "label": "Leçons"}, {"label": "Nouvelle"}],
    })


@login_required
def lecon_fiche(request, id):
    etab = getattr(request, "etablissement_actif", None)
    lecon = get_object_or_404(LeconConduite, id=id, etablissement=etab)
    evaluation = EvaluationLecon.objects.filter(lecon=lecon).select_related("moniteur").first()
    actions = []
    if lecon.statut == StatutLecon.PLANIFIEE:
        actions.append(("confirmer", "Confirmer", "btn-blue"))
    if lecon.statut in (StatutLecon.PLANIFIEE, StatutLecon.CONFIRMEE):
        actions.append(("demarrer", "Démarrer", "btn-green"))
        actions.append(("annuler", "Annuler", "btn-red"))
    if lecon.statut in (StatutLecon.CONFIRMEE, StatutLecon.EN_COURS):
        actions.append(("terminer", "Terminer", "btn-green"))
    if lecon.statut == StatutLecon.PLANIFIEE:
        actions.append(("reporter", "Reporter", "btn-orange"))
    if lecon.statut in (StatutLecon.PLANIFIEE, StatutLecon.CONFIRMEE):
        actions.append(("absence_candidat", "Absent candidat", "btn-red"))
        actions.append(("absence_moniteur", "Absent moniteur", "btn-red"))
    if lecon.statut == StatutLecon.REALISEE:
        actions.append(("evaluer", "Évaluer", "btn-indigo"))

    return render(request, "autoecole/lecons/fiche.html", {
        "lecon": lecon,
        "evaluation": evaluation,
        "actions": actions,
        "breadcrumbs": [{"url": "/planning/", "label": "Planning"}, {"url": "/lecons/", "label": "Leçons"}, {"label": str(lecon)}],
    })


def _executer_action_lecon(request, id, action_func, *args, success_msg="Opération réussie.", **kwargs):
    etab = getattr(request, "etablissement_actif", None)
    lecon = get_object_or_404(LeconConduite, id=id, etablissement=etab)
    try:
        action_func(lecon, *args, **kwargs)
        messages.success(request, success_msg)
    except Exception as e:
        messages.error(request, str(e))
    return redirect("lecon_fiche", id=lecon.id)


@login_required
def lecon_confirmer(request, id):
    return _executer_action_lecon(request, id, lecon_svc.confirmer_lecon, success_msg="Leçon confirmée.")


@login_required
def lecon_demarrer(request, id):
    km = request.POST.get("kilometrage_depart")
    try:
        km_val = int(km) if km else None
    except (ValueError, TypeError):
        km_val = None
    return _executer_action_lecon(request, id, lecon_svc.demarrer_lecon, success_msg="Leçon démarrée.", kilometrage_depart=km_val)


@login_required
def lecon_terminer(request, id):
    km = request.POST.get("kilometrage_fin")
    try:
        km_val = int(km) if km else None
    except (ValueError, TypeError):
        km_val = None
    return _executer_action_lecon(request, id, lecon_svc.terminer_lecon, success_msg="Leçon terminée.", kilometrage_fin=km_val, observation=request.POST.get("observation", ""))


@login_required
def lecon_annuler(request, id):
    motif = request.POST.get("motif", "")
    if request.method == "POST":
        return _executer_action_lecon(request, id, lecon_svc.annuler_lecon, motif=motif, success_msg="Leçon annulée.")
    return render(request, "autoecole/lecons/annuler.html", {
        "lecon": get_object_or_404(LeconConduite, id=id, etablissement=getattr(request, "etablissement_actif", None)),
    })


@login_required
def lecon_reporter(request, id):
    lecon = get_object_or_404(LeconConduite, id=id, etablissement=getattr(request, "etablissement_actif", None))
    if request.method == "POST":
        try:
            from_dt = timezone.datetime.fromisoformat(request.POST["date_debut"]).replace(tzinfo=timezone.get_current_timezone())
            to_dt = timezone.datetime.fromisoformat(request.POST["date_fin"]).replace(tzinfo=timezone.get_current_timezone())
            lecon_svc.reporter_lecon(lecon, from_dt, to_dt)
            messages.success(request, "Leçon reportée.")
            return redirect("lecon_fiche", id=lecon.id)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "autoecole/lecons/reporter.html", {
        "lecon": lecon,
    })


@login_required
def lecon_absence_candidat(request, id):
    return _executer_action_lecon(request, id, lecon_svc.marquer_absence_candidat, success_msg="Absence candidat enregistrée.", observation=request.POST.get("observation", ""))


@login_required
def lecon_absence_moniteur(request, id):
    return _executer_action_lecon(request, id, lecon_svc.marquer_absence_moniteur, success_msg="Absence moniteur enregistrée.", observation=request.POST.get("observation", ""))


# ── Évaluation ──────────────────────────────────────────────

@login_required
def lecon_evaluer(request, id):
    etab = getattr(request, "etablissement_actif", None)
    lecon = get_object_or_404(LeconConduite, id=id, etablissement=etab)
    if request.method == "POST":
        try:
            note = request.POST.get("note_globale")
            note_val = int(note) if note else None
            lecon_svc.evaluer_lecon(
                lecon=lecon,
                moniteur=lecon.moniteur,
                note_globale=note_val,
                niveau=request.POST.get("niveau", ""),
                competences_acquises=request.POST.getlist("competences_acquises"),
                points_forts=request.POST.get("points_forts", ""),
                points_a_ameliorer=request.POST.get("points_a_ameliorer", ""),
                commentaire=request.POST.get("commentaire", ""),
                recommande_examen=request.POST.get("recommande_examen") == "on",
            )
            messages.success(request, "Évaluation enregistrée.")
            return redirect("lecon_fiche", id=lecon.id)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "autoecole/evaluations/formulaire.html", {
        "lecon": lecon,
    })


# ── Disponibilités Moniteur ─────────────────────────────────

@login_required
def indisponibilites_moniteur_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "autoecole/planning/indisponibilites_moniteur.html", {"indisponibilites": []})
    qs = IndisponibiliteMoniteur.objects.filter(moniteur__etablissement=etab).select_related("moniteur")
    return render(request, "autoecole/planning/indisponibilites_moniteur.html", {
        "indisponibilites": qs.order_by("-date_debut")[:50],
    })


@login_required
def indisponibilite_moniteur_creer(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")
    moniteurs = Moniteur.objects.filter(etablissement=etab)
    if request.method == "POST":
        moniteur = get_object_or_404(Moniteur, id=request.POST["moniteur_id"], etablissement=etab)
        from_dt = timezone.datetime.fromisoformat(request.POST["date_debut"]).replace(tzinfo=timezone.get_current_timezone())
        to_dt = timezone.datetime.fromisoformat(request.POST["date_fin"]).replace(tzinfo=timezone.get_current_timezone())
        try:
            indispo = IndisponibiliteMoniteur.objects.create(
                moniteur=moniteur, date_debut=from_dt, date_fin=to_dt,
                motif=request.POST.get("motif", ""), commentaire=request.POST.get("commentaire", ""),
            )
            messages.success(request, "Indisponibilité créée.")
            return redirect("indisponibilites_moniteur_liste")
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "autoecole/planning/indisponibilite_moniteur_form.html", {"moniteurs": moniteurs})


@login_required
def indisponibilite_moniteur_annuler(request, id):
    etab = getattr(request, "etablissement_actif", None)
    indispo = get_object_or_404(IndisponibiliteMoniteur, id=id, moniteur__etablissement=etab)
    indispo_svc.annuler_indisponibilite_moniteur(indispo)
    messages.success(request, "Indisponibilité annulée.")
    return redirect("indisponibilites_moniteur_liste")


# ── Disponibilités Véhicule ─────────────────────────────────

@login_required
def indisponibilites_vehicule_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        return render(request, "autoecole/planning/indisponibilites_vehicule.html", {"indisponibilites": []})
    qs = IndisponibiliteVehicule.objects.filter(vehicule__etablissement=etab).select_related("vehicule")
    return render(request, "autoecole/planning/indisponibilites_vehicule.html", {
        "indisponibilites": qs.order_by("-date_debut")[:50],
    })


@login_required
def indisponibilite_vehicule_creer(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")
    vehicules = Vehicule.objects.filter(etablissement=etab)
    if request.method == "POST":
        vehicule = get_object_or_404(Vehicule, id=request.POST["vehicule_id"], etablissement=etab)
        from_dt = timezone.datetime.fromisoformat(request.POST["date_debut"]).replace(tzinfo=timezone.get_current_timezone())
        to_dt = timezone.datetime.fromisoformat(request.POST["date_fin"]).replace(tzinfo=timezone.get_current_timezone())
        try:
            indispo = IndisponibiliteVehicule.objects.create(
                vehicule=vehicule, date_debut=from_dt, date_fin=to_dt,
                motif=request.POST.get("motif", ""), commentaire=request.POST.get("commentaire", ""),
            )
            messages.success(request, "Indisponibilité créée.")
            return redirect("indisponibilites_vehicule_liste")
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "autoecole/planning/indisponibilite_vehicule_form.html", {"vehicules": vehicules})


@login_required
def indisponibilite_vehicule_annuler(request, id):
    etab = getattr(request, "etablissement_actif", None)
    indispo = get_object_or_404(IndisponibiliteVehicule, id=id, vehicule__etablissement=etab)
    indispo_svc.annuler_indisponibilite_vehicule(indispo)
    messages.success(request, "Indisponibilité annulée.")
    return redirect("indisponibilites_vehicule_liste")
