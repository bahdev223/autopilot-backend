from rest_framework.views import exception_handler
from rest_framework.response import Response
from django_formation.domain.exceptions.formation_exceptions import FormationDomainError


def formation_exception_handler(exc, context):
    if isinstance(exc, FormationDomainError):
        return Response(
            {
                "code": getattr(exc, "code", "FORMATION_ERROR"),
                "message": str(exc),
                "details": {},
            },
            status=getattr(exc, "status_code", 400),
        )
    return exception_handler(exc, context)
