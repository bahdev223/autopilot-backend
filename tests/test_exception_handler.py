import pytest
from unittest.mock import Mock
from rest_framework.test import APIRequestFactory
from rest_framework import status
from apps.core.api.exceptions import autopilot_exception_handler
from django_formation.domain.exceptions.formation_exceptions import FormationDomainError
from django_autoecole.exceptions import AutoEcoleDomainError, InvalidStatusTransitionError, CrossEstablishmentOperationError


class TestFormationDomainErrors:
    def test_formation_domain_error_formats_response(self):
        exc = FormationDomainError("Test error")
        exc.status_code = 400
        context = {"view": Mock(), "request": Mock()}
        response = autopilot_exception_handler(exc, context)
        assert response.status_code == 400
        data = response.data
        assert "code" in data
        assert "message" in data
        assert data["message"] == "Test error"

    def test_formation_domain_error_custom_code(self):
        exc = FormationDomainError("Permission denied")
        exc.code = "PERMISSION_DENIED"
        exc.status_code = 403
        context = {"view": Mock(), "request": Mock()}
        response = autopilot_exception_handler(exc, context)
        assert response.data["code"] == "PERMISSION_DENIED"
        assert response.status_code == 403


class TestAutoEcoleDomainErrors:
    def test_autoecole_domain_error_formats_response(self):
        exc = InvalidStatusTransitionError("Transition invalide")
        context = {"view": Mock(), "request": Mock()}
        response = autopilot_exception_handler(exc, context)
        assert response.status_code == 400
        data = response.data
        assert data["code"] == "InvalidStatusTransitionError"
        assert data["message"] == "Transition invalide"

    def test_cross_establishment_error(self):
        exc = CrossEstablishmentOperationError("Etablissement different")
        context = {"view": Mock(), "request": Mock()}
        response = autopilot_exception_handler(exc, context)
        assert response.status_code == 400
        assert response.data["code"] == "CrossEstablishmentOperationError"

    def test_autoecole_domain_base_error(self):
        exc = AutoEcoleDomainError("Erreur domaine")
        context = {"view": Mock(), "request": Mock()}
        response = autopilot_exception_handler(exc, context)
        assert response.status_code == 400
        assert "code" in response.data


class TestOtherExceptions:
    def test_drf_exceptions_passthrough(self):
        from rest_framework.exceptions import NotFound
        exc = NotFound("Ressource non trouvee")
        context = {"view": Mock(), "request": Mock()}
        response = autopilot_exception_handler(exc, context)
        assert response.status_code == 404

    def test_permission_denied_passthrough(self):
        from rest_framework.exceptions import PermissionDenied
        exc = PermissionDenied("Acces refuse")
        context = {"view": Mock(), "request": Mock()}
        response = autopilot_exception_handler(exc, context)
        assert response.status_code == 403
