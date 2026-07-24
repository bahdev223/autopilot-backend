from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth import get_user_model

from django_formation.models import Etablissement, MembreEtablissement
from apps.core.models import ConfigurationAutoPilot, JournalAuditAutoPilot

User = get_user_model()


@login_required
def etablissement_fiche(request):
    etab = getattr(request, "etablissement_actif", None)
    if not etab:
        messages.error(request, "Aucun établissement actif.")
        return redirect("dashboard")

    if request.method == "POST":
        etab.nom = request.POST.get("nom", etab.nom)
        etab.raison_sociale = request.POST.get("raison_sociale", "")
        etab.telephone = request.POST.get("telephone", "")
        etab.email = request.POST.get("email", "")
        etab.adresse = request.POST.get("adresse", "")
        etab.ville = request.POST.get("ville", "")
        etab.pays = request.POST.get("pays", "Mali")
        etab.save()
        messages.success(request, "Établissement mis à jour.")
        return redirect("etablissement_fiche")

    stats = {
        "apprenants": etab.apprenants.count(),
        "moniteurs": etab.moniteurs.count(),
        "membres": etab.membres.count(),
    }

    return render(request, "organisation/fiche.html", {
        "etablissement": etab,
        "stats": stats,
        "breadcrumbs": [{"label": "Établissement"}],
    })


@login_required
def utilisateurs_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    membres = MembreEtablissement.objects.filter(etablissement=etab).select_related("utilisateur").order_by("-actif", "utilisateur__email")

    q = request.GET.get("q", "")
    if q:
        membres = membres.filter(
            Q(utilisateur__email__icontains=q) |
            Q(utilisateur__get_full_name__icontains=q)
        )
    role = request.GET.get("role", "")
    if role:
        membres = membres.filter(role=role)

    return render(request, "organisation/utilisateurs/liste.html", {
        "membres": membres,
        "q": q,
        "role": role,
        "MembreEtablissement": MembreEtablissement,
        "breadcrumbs": [{"label": "Utilisateurs"}],
    })


@login_required
def utilisateur_ajouter(request):
    etab = getattr(request, "etablissement_actif", None)

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        role = request.POST.get("role")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Aucun utilisateur trouvé avec cet email.")
            return render(request, "organisation/utilisateurs/formulaire.html", {
                "roles": MembreEtablissement.Role.choices,
            })

        if MembreEtablissement.objects.filter(etablissement=etab, utilisateur=user).exists():
            messages.error(request, "Cet utilisateur est déjà membre de l'établissement.")
        else:
            MembreEtablissement.objects.create(
                etablissement=etab, utilisateur=user, role=role,
            )
            messages.success(request, f"Utilisateur {user.email} ajouté avec le rôle {role}.")
            return redirect("utilisateurs_liste")

    return render(request, "organisation/utilisateurs/formulaire.html", {
        "roles": MembreEtablissement.Role.choices,
        "breadcrumbs": [
            {"url": "/utilisateurs/", "label": "Utilisateurs"},
            {"label": "Ajouter"},
        ],
    })


@login_required
def utilisateur_modifier(request, id):
    etab = getattr(request, "etablissement_actif", None)
    membre = get_object_or_404(MembreEtablissement, id=id, etablissement=etab)

    if request.method == "POST":
        membre.role = request.POST.get("role", membre.role)
        membre.actif = request.POST.get("actif") == "on"
        membre.save(update_fields=["role", "actif", "updated_at"])
        messages.success(request, "Membre mis à jour.")
        return redirect("utilisateurs_liste")

    return render(request, "organisation/utilisateurs/formulaire.html", {
        "membre": membre,
        "roles": MembreEtablissement.Role.choices,
        "modifier": True,
        "breadcrumbs": [
            {"url": "/utilisateurs/", "label": "Utilisateurs"},
            {"label": f"Modifier {membre.utilisateur.email}"},
        ],
    })


@login_required
def configuration_view(request):
    etab = getattr(request, "etablissement_actif", None)
    config, created = ConfigurationAutoPilot.objects.get_or_create(etablissement=etab)

    if request.method == "POST":
        config.devise = request.POST.get("devise", "XOF")
        config.fuseau_horaire = request.POST.get("fuseau_horaire", "Africa/Bamako")
        config.duree_lecon_defaut_minutes = int(request.POST.get("duree_lecon_defaut_minutes", 60))
        config.verifier_expiration_documents = request.POST.get("verifier_expiration_documents") == "on"
        config.permettre_examen_sans_heures_minimum = request.POST.get("permettre_examen_sans_heures_minimum") == "on"
        config.prefixe_numero_dossier = request.POST.get("prefixe_numero_dossier", "AE")
        config.prefixe_matricule_moniteur = request.POST.get("prefixe_matricule_moniteur", "MON")
        config.score_maximum_evaluation = float(request.POST.get("score_maximum_evaluation", 20))
        config.delai_annulation_lecon_heures = int(request.POST.get("delai_annulation_lecon_heures", 24))
        config.apercu_disponibilite_jours = int(request.POST.get("apercu_disponibilite_jours", 30))
        config.save()
        messages.success(request, "Configuration mise à jour.")
        return redirect("configuration")

    return render(request, "configuration/configuration.html", {
        "config": config,
        "breadcrumbs": [{"label": "Configuration"}],
    })


@login_required
def audit_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    qs = JournalAuditAutoPilot.objects.filter(etablissement=etab).select_related("utilisateur")

    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(action__icontains=q)
    categorie = request.GET.get("categorie", "")
    if categorie:
        qs = qs.filter(categorie=categorie)
    action = request.GET.get("action", "")
    if action:
        qs = qs.filter(action=action)

    categories = JournalAuditAutoPilot.objects.filter(etablissement=etab).values_list("categorie", flat=True).distinct().order_by("categorie")
    actions = JournalAuditAutoPilot.objects.filter(etablissement=etab).values_list("action", flat=True).distinct().order_by("action")

    return render(request, "audit/liste.html", {
        "entries": qs[:100],
        "q": q,
        "categorie": categorie,
        "action": action,
        "categories": categories,
        "actions": actions,
        "breadcrumbs": [{"label": "Journal d'activité"}],
    })
