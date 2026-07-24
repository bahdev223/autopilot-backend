from django.contrib import admin
from django_formation.models.etablissement import Etablissement
from django_formation.models.membre import MembreEtablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_formation.models.historique import HistoriqueStatutInscription


class MembreInline(admin.TabularInline):
    model = MembreEtablissement
    extra = 1


@admin.register(Etablissement)
class EtablissementAdmin(admin.ModelAdmin):
    list_display = ["nom", "code", "ville", "pays", "actif", "created_at"]
    list_filter = ["actif", "pays", "ville"]
    search_fields = ["nom", "code", "email"]
    inlines = [MembreInline]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(MembreEtablissement)
class MembreEtablissementAdmin(admin.ModelAdmin):
    list_display = ["utilisateur", "etablissement", "role", "actif"]
    list_filter = ["role", "actif"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Apprenant)
class ApprenantAdmin(admin.ModelAdmin):
    list_display = ["matricule", "nom", "prenom", "telephone", "etablissement", "statut"]
    list_filter = ["statut", "etablissement"]
    search_fields = ["matricule", "nom", "prenom", "telephone", "email"]
    readonly_fields = ["id", "matricule", "statut", "created_at", "updated_at"]


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ["code", "nom", "etablissement", "duree_heures", "tarif_indicatif", "statut"]
    list_filter = ["statut", "etablissement"]
    search_fields = ["code", "nom"]
    readonly_fields = ["id", "statut", "created_at", "updated_at"]
    actions = ["publier_formation", "archiver_formation"]

    def publier_formation(self, request, queryset):
        from django_formation.services.formations import FormationService
        svc = FormationService()
        for f in queryset:
            try:
                svc.publier_formation(f)
            except Exception:
                pass
        self.message_user(request, f"{queryset.count()} formation(s) publiée(s)")
    publier_formation.short_description = "Publier les formations sélectionnées"

    def archiver_formation(self, request, queryset):
        from django_formation.services.formations import FormationService
        svc = FormationService()
        for f in queryset:
            try:
                svc.archiver_formation(f)
            except Exception:
                pass
        self.message_user(request, f"{queryset.count()} formation(s) archivée(s)")
    archiver_formation.short_description = "Archiver les formations sélectionnées"


@admin.register(SessionFormation)
class SessionFormationAdmin(admin.ModelAdmin):
    list_display = ["code", "nom", "formation", "date_debut", "date_fin", "capacite", "statut"]
    list_filter = ["statut", "etablissement"]
    search_fields = ["code", "nom"]
    readonly_fields = ["id", "statut", "created_at", "updated_at"]
    actions = ["ouvrir_inscriptions", "fermer_inscriptions", "demarrer_session", "terminer_session", "annuler_session"]

    def ouvrir_inscriptions(self, request, queryset):
        from django_formation.services.sessions import SessionService
        svc = SessionService()
        for s in queryset:
            try:
                svc.ouvrir_inscriptions(s)
            except Exception:
                pass
        self.message_user(request, "Inscriptions ouvertes")
    ouvrir_inscriptions.short_description = "Ouvrir les inscriptions"

    def fermer_inscriptions(self, request, queryset):
        from django_formation.services.sessions import SessionService
        svc = SessionService()
        for s in queryset:
            try:
                svc.fermer_inscriptions(s)
            except Exception:
                pass
        self.message_user(request, "Inscriptions fermées")
    fermer_inscriptions.short_description = "Fermer les inscriptions"

    def demarrer_session(self, request, queryset):
        from django_formation.services.sessions import SessionService
        svc = SessionService()
        for s in queryset:
            try:
                svc.demarrer_session(s, modifie_par=request.user)
            except Exception:
                pass
        self.message_user(request, "Session(s) démarrée(s)")
    demarrer_session.short_description = "Démarrer la session"

    def terminer_session(self, request, queryset):
        from django_formation.services.sessions import SessionService
        svc = SessionService()
        for s in queryset:
            try:
                svc.terminer_session(s, modifie_par=request.user)
            except Exception:
                pass
        self.message_user(request, "Session(s) terminée(s)")
    terminer_session.short_description = "Terminer la session"

    def annuler_session(self, request, queryset):
        from django_formation.services.sessions import SessionService
        svc = SessionService()
        for s in queryset:
            try:
                svc.annuler_session(s, modifie_par=request.user)
            except Exception:
                pass
        self.message_user(request, "Session(s) annulée(s)")
    annuler_session.short_description = "Annuler la session"


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ["numero", "apprenant", "session", "date_inscription", "statut"]
    list_filter = ["statut"]
    search_fields = ["numero"]
    readonly_fields = ["id", "numero", "statut", "date_inscription", "date_confirmation", "date_fin", "etablissement", "created_at", "updated_at"]
    actions = ["confirmer_inscription", "refuser_inscription", "annuler_inscription"]

    def confirmer_inscription(self, request, queryset):
        from django_formation.services.inscriptions import InscriptionService
        svc = InscriptionService()
        for ins in queryset:
            try:
                svc.confirmer_inscription(ins, modifie_par=request.user)
            except Exception:
                pass
        self.message_user(request, "Inscription(s) confirmée(s)")
    confirmer_inscription.short_description = "Confirmer les inscriptions"

    def refuser_inscription(self, request, queryset):
        from django_formation.services.inscriptions import InscriptionService
        svc = InscriptionService()
        for ins in queryset:
            try:
                svc.refuser_inscription(ins, motif="Refusé depuis l'admin", modifie_par=request.user)
            except Exception:
                pass
        self.message_user(request, "Inscription(s) refusée(s)")
    refuser_inscription.short_description = "Refuser les inscriptions"

    def annuler_inscription(self, request, queryset):
        from django_formation.services.inscriptions import InscriptionService
        svc = InscriptionService()
        for ins in queryset:
            try:
                svc.annuler_inscription(ins, motif="Annulé depuis l'admin", modifie_par=request.user)
            except Exception:
                pass
        self.message_user(request, "Inscription(s) annulée(s)")
    annuler_inscription.short_description = "Annuler les inscriptions"


@admin.register(HistoriqueStatutInscription)
class HistoriqueStatutInscriptionAdmin(admin.ModelAdmin):
    list_display = ["inscription", "ancien_statut", "nouveau_statut", "created_at"]
    readonly_fields = ["inscription", "ancien_statut", "nouveau_statut", "commentaire", "modifie_par"]
