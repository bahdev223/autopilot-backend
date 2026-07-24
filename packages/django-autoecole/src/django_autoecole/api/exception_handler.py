from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from django_autoecole.exceptions import AutoEcoleDomainError


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if isinstance(exc, AutoEcoleDomainError):
        return Response(
            {"code": type(exc).__name__, "message": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return response
