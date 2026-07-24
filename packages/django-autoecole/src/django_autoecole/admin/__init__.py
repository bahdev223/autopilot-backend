from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_autoecole.models import (
    CategoriePermis, Moniteur, Vehicule, DossierAutoEcole,
    LeconConduite, EvaluationLecon, ExamenAutoEcole,
    IndisponibiliteMoniteur, IndisponibiliteVehicule, HistoriqueStatutDossier,
)


@admin.register(CategoriePermis)
class CategoriePermisAdmin(admin.ModelAdmin):
    list_display = ["code", "nom", "etablissement", "heures_conduite_minimum", "actif"]
    list_filter = ["actif", "etablissement"]
    search_fields = ["code", "nom"]


@admin.register(Moniteur)
class MoniteurAdmin(admin.ModelAdmin):
    list_display = ["matricule", "nom", "prenom", "etablissement", "statut", "date_embauche"]
    list_filter = ["statut", "etablissement", "categories_permis"]
    search_fields = ["matricule", "nom", "prenom", "numero_agrement"]
    filter_horizontal = ["categories_permis"]


@admin.register(Vehicule)
class VehiculeAdmin(admin.ModelAdmin):
    list_display = ["immatriculation", "marque", "modele", "etablissement", "categorie_permis", "kilometrage_actuel", "statut"]
    list_filter = ["statut", "etablissement", "categorie_permis", "type_boite"]
    search_fields = ["immatriculation", "marque", "modele"]


@admin.register(DossierAutoEcole)
class DossierAutoEcoleAdmin(admin.ModelAdmin):
    list_display = ["numero_dossier", "apprenant_nom", "categorie_permis", "statut", "date_ouverture", "progression_conduite"]
    list_filter = ["statut", "categorie_permis", "etablissement"]
    search_fields = ["numero_dossier"]
    readonly_fields = ["heures_theorie_validees", "heures_conduite_validees", "pret_examen_le", "cloture_le"]

    def apprenant_nom(self, obj):
        return str(obj.inscription.apprenant)
    apprenant_nom.short_description = _("Apprenant")


@admin.register(LeconConduite)
class LeconConduiteAdmin(admin.ModelAdmin):
    list_display = ["date_debut", "dossier", "moniteur", "vehicule", "type_lecon", "duree_minutes", "statut"]
    list_filter = ["statut", "type_lecon", "etablissement"]
    search_fields = ["dossier__numero_dossier", "moniteur__nom"]
    readonly_fields = ["statut"]


@admin.register(EvaluationLecon)
class EvaluationLeconAdmin(admin.ModelAdmin):
    list_display = ["lecon", "moniteur", "note_globale", "niveau", "recommande_examen"]
    list_filter = ["niveau", "recommande_examen"]


@admin.register(ExamenAutoEcole)
class ExamenAutoEcoleAdmin(admin.ModelAdmin):
    list_display = ["dossier", "type_examen", "date_examen", "statut", "resultat"]
    list_filter = ["type_examen", "statut", "resultat", "etablissement"]
    readonly_fields = ["statut", "resultat"]


@admin.register(IndisponibiliteMoniteur)
class IndisponibiliteMoniteurAdmin(admin.ModelAdmin):
    list_display = ["moniteur", "date_debut", "date_fin", "motif", "statut"]
    list_filter = ["statut"]


@admin.register(IndisponibiliteVehicule)
class IndisponibiliteVehiculeAdmin(admin.ModelAdmin):
    list_display = ["vehicule", "date_debut", "date_fin", "motif", "statut"]
    list_filter = ["statut"]


@admin.register(HistoriqueStatutDossier)
class HistoriqueStatutDossierAdmin(admin.ModelAdmin):
    list_display = ["dossier", "ancien_statut", "nouveau_statut", "modifie_par", "created_at"]
    list_filter = ["nouveau_statut"]
    readonly_fields = ["dossier", "ancien_statut", "nouveau_statut", "modifie_par", "created_at"]
