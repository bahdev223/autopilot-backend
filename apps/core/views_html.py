from datetime import date, timedelta
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from django_formation.models import Apprenant, Formation, SessionFormation, Inscription, Etablissement
from django_formation.models.membre import MembreEtablissement
from django_autoecole.models import (
    DossierAutoEcole, Moniteur, Vehicule, LeconConduite,
    ExamenAutoEcole, EvaluationLecon, CategoriePermis,
    IndisponibiliteVehicule,
)
from django_autoecole.constants import (
    StatutDossier, StatutLecon, StatutVehicule, StatutMoniteur, StatutExamen,
)
from apps.core.models import JournalAuditAutoPilot


class AutopilotLoginView(LoginView):
    template_name = "authentication/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("dashboard")


@require_POST
def deconnexion(request):
    logout(request)
    return redirect("connexion")


@login_required
def dashboard_view(request):
    etab = getattr(request, "etablissement_actif", None)
    aujourdhui = timezone.localdate()
    stats = {"apprenants_actifs": 0, "dossiers_formation": 0, "lecons_ajourdhui": 0, "lecons_restantes": 0, "vehicules_disponibles": 0, "vehicules_indisponibles": 0}
    lecons_jour = []
    candidats_prets = []
    alertes_vehicules = []
    activite_recente = []

    if etab:
        stats["apprenants_actifs"] = Apprenant.objects.filter(etablissement=etab, statut="ACTIF").count()
        stats["dossiers_formation"] = DossierAutoEcole.objects.filter(etablissement=etab, statut=StatutDossier.EN_FORMATION).count()
        stats["vehicules_disponibles"] = Vehicule.objects.filter(etablissement=etab, statut=StatutVehicule.DISPONIBLE).count()
        stats["vehicules_indisponibles"] = Vehicule.objects.filter(etablissement=etab).exclude(statut=StatutVehicule.DISPONIBLE).exclude(statut=StatutVehicule.ARCHIVE).count()

        lecons_qs = LeconConduite.objects.filter(
            etablissement=etab,
            date_debut__date=aujourdhui,
        ).select_related("dossier", "moniteur", "dossier__inscription__apprenant").order_by("date_debut")
        stats["lecons_ajourdhui"] = lecons_qs.count()
        stats["lecons_restantes"] = lecons_qs.filter(statut__in=[StatutLecon.PLANIFIEE, StatutLecon.CONFIRMEE]).count()
        lecons_jour = lecons_qs[:10]

        candidats_prets = DossierAutoEcole.objects.filter(
            etablissement=etab, statut=StatutDossier.PRET_EXAMEN,
        ).select_related("inscription__apprenant", "categorie_permis")[:5]

        alerte_vehicules = []
        for v in Vehicule.objects.filter(etablissement=etab).exclude(statut=StatutVehicule.ARCHIVE):
            if v.date_expiration_assurance and v.date_expiration_assurance <= aujourdhui + timedelta(days=30):
                j = (v.date_expiration_assurance - aujourdhui).days
                if j <= 0:
                    alerte_vehicules.append({"vehicule": v, "message": "Assurance expirée", "niveau": "CRITIQUE"})
                elif j <= 7:
                    alerte_vehicules.append({"vehicule": v, "message": f"Assurance expirera dans {j} jour(s)", "niveau": "AVERTISSEMENT"})
            if v.date_expiration_visite_technique and v.date_expiration_visite_technique <= aujourdhui + timedelta(days=30):
                j = (v.date_expiration_visite_technique - aujourdhui).days
                if j <= 0:
                    alerte_vehicules.append({"vehicule": v, "message": "Visite technique expirée", "niveau": "CRITIQUE"})
                elif j <= 7:
                    alerte_vehicules.append({"vehicule": v, "message": f"Visite technique expire dans {j} jour(s)", "niveau": "AVERTISSEMENT"})
        alertes_vehicules = alerte_vehicules[:5]

        entrees = JournalAuditAutoPilot.objects.filter(etablissement=etab).order_by("-created_at")[:5]
        activite_recente = [
            {
                "title": e.action,
                "description": f"{e.entite_type} #{e.entite_id}",
                "detail": e.details or "",
                "time": e.created_at.strftime("%H:%M"),
            }
            for e in entrees
        ]

    return render(request, "dashboard/dashboard.html", {
        "stats": stats,
        "lecons_jour": lecons_jour,
        "candidats_prets": candidats_prets,
        "alertes_vehicules": alertes_vehicules,
        "activite_recente": activite_recente,
    })


@login_required
def profil_view(request):
    membre = MembreEtablissement.objects.filter(utilisateur=request.user, actif=True).first()
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.save()
        from django.contrib import messages
        messages.success(request, "Profil mis à jour.")
        return redirect("profil")
    return render(request, "profile/profil.html", {
        "membre": membre,
        "breadcrumbs": [{"label": "Mon profil"}],
    })


@login_required
@require_POST
def changer_mot_de_passe(request):
    form = PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        form.save()
        from django.contrib import messages
        messages.success(request, "Mot de passe changé avec succès.")
    else:
        from django.contrib import messages
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect("profil")


class AutopilotPasswordResetView(PasswordResetView):
    template_name = "authentication/password_reset.html"
    email_template_name = "authentication/password_reset_email.html"
    success_url = reverse_lazy("mot_de_passe_oublie_done")


class AutopilotPasswordResetDoneView(PasswordResetDoneView):
    template_name = "authentication/password_reset_done.html"
