from rest_framework.permissions import BasePermission


def _is_member_with_role(user, etablissement_id, roles):
    if not user or not user.is_authenticated:
        return False
    from django_formation.models.membre import MembreEtablissement
    return MembreEtablissement.objects.filter(
        utilisateur=user, etablissement_id=etablissement_id,
        actif=True, role__in=roles,
    ).exists()


class IsAuthenticatedMember(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsProprietaireOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return _is_member_with_role(
            request.user, obj.etablissement_id,
            ["PROPRIETAIRE", "ADMINISTRATEUR"],
        )


class CanManageLearners(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return _is_member_with_role(
            request.user, obj.etablissement_id,
            ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE", "AGENT_INSCRIPTION"],
        )


class CanManageEnrollments(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return _is_member_with_role(
            request.user, obj.etablissement_id,
            ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE", "AGENT_INSCRIPTION"],
        )


class CanManageTrainings(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return _is_member_with_role(
            request.user, obj.etablissement_id,
            ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"],
        )


class CanManageSessions(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return _is_member_with_role(
            request.user, obj.etablissement_id,
            ["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE"],
        )
