from django.urls import path
from django.views.generic import TemplateView
from apps.core.views_html import (
    AutopilotLoginView, deconnexion, dashboard_view, profil_view,
    changer_mot_de_passe,
    AutopilotPasswordResetView, AutopilotPasswordResetDoneView,
)
from apps.core.views_rh import (
    employes_liste, employe_creer,
)
from apps.core.views_formation import (
    apprenants_liste, apprenant_creer, apprenant_fiche, apprenant_modifier,
    formations_liste, formation_creer, formation_fiche,
    sessions_liste, session_creer, session_fiche,
    inscriptions_liste, inscription_creer, inscription_fiche,
)
from apps.core.views_autoecole import (
    categories_liste, categorie_creer, categorie_activer, categorie_desactiver,
    dossiers_liste, dossier_fiche, dossier_ouvrir, dossier_demarrer_formation, dossier_declarer_pret,
    moniteurs_liste, moniteur_creer, moniteur_fiche, moniteur_activer, moniteur_indisponible,
    vehicules_liste, vehicule_creer, vehicule_fiche,
)
from apps.core.views_progression import (
    evaluations_liste, evaluation_fiche, progression_apprenant,
)
from apps.core.views_administration import (
    etablissement_fiche, utilisateurs_liste, utilisateur_ajouter, utilisateur_modifier,
    configuration_view, audit_liste,
)
from apps.core.views_examens import (
    examens_liste, examen_creer, examen_fiche,
    examen_confirmer, examen_presenter, examen_absent, examen_annuler,
    examen_resultat,
)
from apps.core.views_expenses import (
    expenses_liste, expense_creer, expense_fiche,
    expense_modifier, expense_supprimer,
    expense_soumettre, expense_approuver, expense_rejeter,
    expense_payer, expense_annuler,
)
from apps.core.views_comptes import (
    comptes_dashboard,
    comptes_liste as comptes_bancaires_liste_view, compte_creer, compte_detail, compte_modifier, compte_cloturer,
    compte_journal,
    mouvements_liste, mouvement_encaisser, mouvement_decaisser,
    transfert_effectuer, transferts_liste,
    rapprochement_liste as rapprochement_bancaire_liste_view, rapprochement_detail, rapprochement_initialiser,
)
from apps.core.views_comptabilite import (
    comptabilite_dashboard,
    ecritures_liste, ecriture_creer, ecriture_fiche, ecriture_modifier, ecriture_supprimer, ecriture_valider,
    comptes_liste, compte_fiche,
    journaux_liste, journal_fiche,
    balance, grand_livre, bilan, compte_resultat,
    exercices_liste, exercice_creer, exercice_fiche, exercice_cloturer, exercice_rouvrir,
    immobilisations_liste, immobilisation_fiche,
    rapprochement_liste, rapprochement_fiche,
)
from apps.core.views_planning import (
    planning_view,
    lecons_liste, lecon_creer, lecon_fiche,
    lecon_confirmer, lecon_demarrer, lecon_terminer,
    lecon_annuler, lecon_reporter,
    lecon_absence_candidat, lecon_absence_moniteur,
    lecon_evaluer,
    indisponibilites_moniteur_liste, indisponibilite_moniteur_creer, indisponibilite_moniteur_annuler,
    indisponibilites_vehicule_liste, indisponibilite_vehicule_creer, indisponibilite_vehicule_annuler,
)

urlpatterns = [
    # Authentification
    path("connexion/", AutopilotLoginView.as_view(), name="connexion"),
    path("deconnexion/", deconnexion, name="deconnexion"),
    path("mot-de-passe-oublie/", AutopilotPasswordResetView.as_view(), name="mot_de_passe_oublie"),
    path("mot-de-passe-oublie/envoye/", AutopilotPasswordResetDoneView.as_view(), name="mot_de_passe_oublie_done"),

    # Dashboard & Profil
    path("", dashboard_view, name="dashboard"),
    path("tableau-de-bord/", dashboard_view, name="dashboard_alt"),
    path("profil/", profil_view, name="profil"),
    path("profil/mot-de-passe/", changer_mot_de_passe, name="changer_mot_de_passe"),

    # ── Lot 2 : Formation ────────────────────────────────────
    # Apprenants
    path("apprenants/", apprenants_liste, name="apprenants_liste"),
    path("apprenants/creer/", apprenant_creer, name="apprenant_creer"),
    path("apprenants/<uuid:id>/", apprenant_fiche, name="apprenant_fiche"),
    path("apprenants/<uuid:id>/modifier/", apprenant_modifier, name="apprenant_modifier"),
    # Formations
    path("formations/", formations_liste, name="formations_liste"),
    path("formations/creer/", formation_creer, name="formation_creer"),
    path("formations/<uuid:id>/", formation_fiche, name="formation_fiche"),
    # Sessions
    path("sessions/", sessions_liste, name="sessions_liste"),
    path("sessions/creer/", session_creer, name="session_creer"),
    path("sessions/<uuid:id>/", session_fiche, name="session_fiche"),
    # Inscriptions
    path("inscriptions/", inscriptions_liste, name="inscriptions_liste"),
    path("inscriptions/creer/", inscription_creer, name="inscription_creer"),
    path("inscriptions/creer/apprenant/<uuid:apprenant_id>/", inscription_creer, name="inscription_creer_pour_apprenant"),
    path("inscriptions/<uuid:id>/", inscription_fiche, name="inscription_fiche"),

    # ── Lot 3 : Auto-école ────────────────────────────────────
    # Catégories de permis
    path("autoecole/categories/", categories_liste, name="categories_liste"),
    path("autoecole/categories/creer/", categorie_creer, name="categorie_creer"),
    path("autoecole/categories/<uuid:id>/activer/", categorie_activer, name="categorie_activer"),
    path("autoecole/categories/<uuid:id>/desactiver/", categorie_desactiver, name="categorie_desactiver"),
    # Dossiers
    path("autoecole/dossiers/", dossiers_liste, name="dossiers_liste"),
    path("autoecole/dossiers/<uuid:id>/", dossier_fiche, name="dossier_fiche"),
    path("autoecole/dossiers/<uuid:id>/ouvrir/", dossier_ouvrir, name="dossier_ouvrir"),
    path("autoecole/dossiers/<uuid:id>/demarrer-formation/", dossier_demarrer_formation, name="dossier_demarrer_formation"),
    path("autoecole/dossiers/<uuid:id>/declarer-pret/", dossier_declarer_pret, name="dossier_declarer_pret"),
    # Moniteurs
    path("autoecole/moniteurs/", moniteurs_liste, name="moniteurs_liste"),
    path("autoecole/moniteurs/ajouter/", moniteur_creer, name="moniteur_creer"),
    path("autoecole/moniteurs/<uuid:id>/", moniteur_fiche, name="moniteur_fiche"),
    path("autoecole/moniteurs/<uuid:id>/activer/", moniteur_activer, name="moniteur_activer"),
    path("autoecole/moniteurs/<uuid:id>/indisponible/", moniteur_indisponible, name="moniteur_indisponible"),
    # Véhicules
    path("autoecole/vehicules/", vehicules_liste, name="vehicules_liste"),
    path("autoecole/vehicules/ajouter/", vehicule_creer, name="vehicule_creer"),
    path("autoecole/vehicules/<uuid:id>/", vehicule_fiche, name="vehicule_fiche"),

    # ── Lot 4 : Planning & Leçons ────────────────────────────
    path("planning/", planning_view, name="planning"),
    path("lecons/", lecons_liste, name="lecons_liste"),
    path("lecons/creer/", lecon_creer, name="lecon_creer"),
    path("lecons/<uuid:id>/", lecon_fiche, name="lecon_fiche"),
    path("lecons/<uuid:id>/confirmer/", lecon_confirmer, name="lecon_confirmer"),
    path("lecons/<uuid:id>/demarrer/", lecon_demarrer, name="lecon_demarrer"),
    path("lecons/<uuid:id>/terminer/", lecon_terminer, name="lecon_terminer"),
    path("lecons/<uuid:id>/annuler/", lecon_annuler, name="lecon_annuler"),
    path("lecons/<uuid:id>/reporter/", lecon_reporter, name="lecon_reporter"),
    path("lecons/<uuid:id>/absence-candidat/", lecon_absence_candidat, name="lecon_absence_candidat"),
    path("lecons/<uuid:id>/absence-moniteur/", lecon_absence_moniteur, name="lecon_absence_moniteur"),
    path("lecons/<uuid:id>/evaluer/", lecon_evaluer, name="lecon_evaluer"),
    # Disponibilités moniteurs
    path("planning/indisponibilites/moniteurs/", indisponibilites_moniteur_liste, name="indisponibilites_moniteur_liste"),
    path("planning/indisponibilites/moniteurs/creer/", indisponibilite_moniteur_creer, name="indisponibilite_moniteur_creer"),
    path("planning/indisponibilites/moniteurs/<uuid:id>/annuler/", indisponibilite_moniteur_annuler, name="indisponibilite_moniteur_annuler"),
    # Disponibilités véhicules
    path("planning/indisponibilites/vehicules/", indisponibilites_vehicule_liste, name="indisponibilites_vehicule_liste"),
    path("planning/indisponibilites/vehicules/creer/", indisponibilite_vehicule_creer, name="indisponibilite_vehicule_creer"),
    path("planning/indisponibilites/vehicules/<uuid:id>/annuler/", indisponibilite_vehicule_annuler, name="indisponibilite_vehicule_annuler"),

    # ── Lot 5 : Évaluations & Progression ───────────────────
    path("evaluations/", evaluations_liste, name="evaluations_liste"),
    path("evaluations/<uuid:id>/", evaluation_fiche, name="evaluation_fiche"),
    path("progression/<uuid:id>/", progression_apprenant, name="progression_apprenant"),
    path("examens/", examens_liste, name="examens_liste"),
    path("examens/planifier/", examen_creer, name="examen_creer"),
    path("examens/<uuid:id>/", examen_fiche, name="examen_fiche"),
    path("examens/<uuid:id>/confirmer/", examen_confirmer, name="examen_confirmer"),
    path("examens/<uuid:id>/presenter/", examen_presenter, name="examen_presenter"),
    path("examens/<uuid:id>/absent/", examen_absent, name="examen_absent"),
    path("examens/<uuid:id>/annuler/", examen_annuler, name="examen_annuler"),
    path("examens/<uuid:id>/resultat/", examen_resultat, name="examen_resultat"),

    # ── Lot 7 : Administration ───────────────────────────────
    path("organisation/", etablissement_fiche, name="etablissement_fiche"),
    path("utilisateurs/", utilisateurs_liste, name="utilisateurs_liste"),
    path("utilisateurs/ajouter/", utilisateur_ajouter, name="utilisateur_ajouter"),
    path("utilisateurs/<uuid:id>/modifier/", utilisateur_modifier, name="utilisateur_modifier"),
    path("configuration/", configuration_view, name="configuration"),
    path("audit/", audit_liste, name="audit_liste"),

    # ── RH ─────────────────────────────────────────────────────
    path("rh/", employes_liste, name="employes_liste"),
    path("rh/ajouter/", employe_creer, name="employe_creer"),

    # ── Module Dépenses ───────────────────────────────────────
    path("depenses/", expenses_liste, name="expenses_liste"),
    path("depenses/creer/", expense_creer, name="expense_creer"),
    path("depenses/<int:id>/", expense_fiche, name="expense_fiche"),
    path("depenses/<int:id>/modifier/", expense_modifier, name="expense_modifier"),
    path("depenses/<int:id>/supprimer/", expense_supprimer, name="expense_supprimer"),
    path("depenses/<int:id>/soumettre/", expense_soumettre, name="expense_soumettre"),
    path("depenses/<int:id>/approuver/", expense_approuver, name="expense_approuver"),
    path("depenses/<int:id>/rejeter/", expense_rejeter, name="expense_rejeter"),
    path("depenses/<int:id>/payer/", expense_payer, name="expense_payer"),
    path("depenses/<int:id>/annuler/", expense_annuler, name="expense_annuler"),

    # ── Module Comptabilité OHADA ──────────────────────────────
    path("comptabilite/", comptabilite_dashboard, name="comptabilite_dashboard"),
    path("comptabilite/ecritures/", ecritures_liste, name="ecritures_liste"),
    path("comptabilite/ecritures/creer/", ecriture_creer, name="ecriture_creer"),
    path("comptabilite/ecritures/<int:id>/", ecriture_fiche, name="ecriture_fiche"),
    path("comptabilite/ecritures/<int:id>/modifier/", ecriture_modifier, name="ecriture_modifier"),
    path("comptabilite/ecritures/<int:id>/supprimer/", ecriture_supprimer, name="ecriture_supprimer"),
    path("comptabilite/ecritures/<int:id>/valider/", ecriture_valider, name="ecriture_valider"),
    path("comptabilite/comptes/", comptes_liste, name="comptes_liste"),
    path("comptabilite/comptes/<int:id>/", compte_fiche, name="compte_fiche"),
    path("comptabilite/journaux/", journaux_liste, name="journaux_liste"),
    path("comptabilite/journaux/<int:id>/", journal_fiche, name="journal_fiche"),
    path("comptabilite/balance/", balance, name="balance"),
    path("comptabilite/grand-livre/", grand_livre, name="grand_livre"),
    path("comptabilite/bilan/", bilan, name="bilan"),
    path("comptabilite/compte-resultat/", compte_resultat, name="compte_resultat"),
    path("comptabilite/exercices/", exercices_liste, name="exercices_liste"),
    path("comptabilite/exercices/creer/", exercice_creer, name="exercice_creer"),
    path("comptabilite/exercices/<int:id>/", exercice_fiche, name="exercice_fiche"),
    path("comptabilite/exercices/<int:id>/cloturer/", exercice_cloturer, name="exercice_cloturer"),
    path("comptabilite/exercices/<int:id>/rouvrir/", exercice_rouvrir, name="exercice_rouvrir"),
    path("comptabilite/immobilisations/", immobilisations_liste, name="immobilisations_liste"),
    path("comptabilite/immobilisations/<int:id>/", immobilisation_fiche, name="immobilisation_fiche"),
    path("comptabilite/rapprochement/", rapprochement_liste, name="rapprochement_liste"),
    path("comptabilite/rapprochement/<int:id>/", rapprochement_fiche, name="rapprochement_fiche"),

    # ── Module Comptes Financiers ─────────────────────────────
    path("comptes/", comptes_dashboard, name="comptes_dashboard"),
    path("comptes/comptes/", comptes_bancaires_liste_view, name="comptes_bancaires_liste"),
    path("comptes/comptes/ajouter/", compte_creer, name="compte_creer"),
    path("comptes/comptes/<int:compte_id>/", compte_detail, name="compte_detail"),
    path("comptes/comptes/<int:compte_id>/modifier/", compte_modifier, name="compte_modifier"),
    path("comptes/comptes/<int:compte_id>/cloturer/", compte_cloturer, name="compte_cloturer"),
    path("comptes/comptes/<int:compte_id>/journal/", compte_journal, name="compte_journal"),
    path("comptes/mouvements/", mouvements_liste, name="mouvements_liste"),
    path("comptes/transferts/", transfert_effectuer, name="transfert_effectuer"),
    path("comptes/transferts/liste/", transferts_liste, name="transferts_liste"),
    path("comptes/rapprochement/", rapprochement_bancaire_liste_view, name="rapprochement_bancaire_liste"),
    path("comptes/rapprochement/<int:rapprochement_id>/", rapprochement_detail, name="rapprochement_detail"),
    path("comptes/rapprochement/initialiser/", rapprochement_initialiser, name="rapprochement_initialiser"),

    # Erreurs
    path("403/", TemplateView.as_view(template_name="errors/403.html"), name="erreur_403"),
    path("404/", TemplateView.as_view(template_name="errors/404.html"), name="erreur_404"),
    path("500/", TemplateView.as_view(template_name="errors/500.html"), name="erreur_500"),
    path("maintenance/", TemplateView.as_view(template_name="errors/maintenance.html"), name="maintenance"),
]
