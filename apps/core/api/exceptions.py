from rest_framework.views import exception_handler
from rest_framework.response import Response
from django_formation.domain.exceptions.formation_exceptions import FormationDomainError
from django_autoecole.exceptions import AutoEcoleDomainError


def autopilot_exception_handler(exc, context):
    if isinstance(exc, FormationDomainError):
        return Response(
            {
                "code": getattr(exc, "code", "DOMAIN_ERROR"),
                "message": str(exc),
                "details": {},
            },
            status=getattr(exc, "status_code", 400),
        )
    if isinstance(exc, AutoEcoleDomainError):
        return Response(
            {
                "code": type(exc).__name__,
                "message": str(exc),
                "details": {},
            },
            status=400,
        )
    return exception_handler(exc, context)
