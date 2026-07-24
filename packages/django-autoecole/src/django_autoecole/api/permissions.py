from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


ROLE_HIERARCHY = {
    "PROPRIETAIRE": 100,
    "ADMINISTRATEUR": 90,
    "RESPONSABLE": 80,
    "AGENT_INSCRIPTION": 50,
    "LECTEUR": 10,
}

# Minimum role level required for each action category
ACTION_LEVELS = {
    "create": 50,
    "update": 50,
    "partial_update": 50,
    "destroy": 80,
    "list": 10,
    "retrieve": 10,
    # Custom actions
    "activer": 80,
    "desactiver": 80,
    "ouvrir": 50,
    "demarrer_formation": 50,
    "suspendre": 80,
    "reprendre": 80,
    "declarer_pret_examen": 50,
    "annuler": 80,
    "cloturer": 80,
    "affecter_moniteur": 80,
    "confirmer": 50,
    "evaluer": 50,
    "reporter": 50,
    "absence_candidat": 50,
    "absence_moniteur": 50,
    "mettre_en_entretien": 50,
    "declarer_en_panne": 50,
    "rendre_disponible": 50,
    "mettre_hors_service": 80,
    "archiver": 80,
    "mettre_a_jour_kilometrage": 50,
    "marquer_presente": 50,
    "marquer_absent": 50,
    "enregistrer_resultat": 80,
    "indisponible": 50,
    "reactiver": 80,
    # Read-only custom actions
    "planning": 10,
    "progression": 10,
    "historique": 10,
    "lecons": 10,
    "examens": 10,
    "indisponibilites": 10,
}


class IsAuthenticatedFormationMember(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.adhesions_formation.filter(actif=True).exists()

    def has_object_permission(self, request, view, obj):
        etablissement_id = getattr(obj, "etablissement_id", None)
        if etablissement_id is None and hasattr(obj, "moniteur"):
            etablissement_id = obj.moniteur.etablissement_id
        if etablissement_id is None and hasattr(obj, "vehicule"):
            etablissement_id = obj.vehicule.etablissement_id
        return request.user.adhesions_formation.filter(
            actif=True,
            etablissement_id=etablissement_id,
        ).exists()


class HasRoleLevel(BasePermission):
    def has_permission(self, request, view):
        action = getattr(view, "action", None)
        required = ACTION_LEVELS.get(action, 10)
        membership = request.user.adhesions_formation.filter(actif=True).first()
        if not membership:
            return False
        user_level = ROLE_HIERARCHY.get(membership.role, 0)
        if user_level < required:
            raise PermissionDenied(
                f"Votre rôle ({membership.get_role_display()}) ne permet pas cette action"
            )
        return True

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
