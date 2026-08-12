from unittest.mock import patch

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, APITestCase

from apps.core.exceptions import custom_exception_handler


class HealthReadyTests(APITestCase):
    def test_health_returns_200_without_db(self) -> None:
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "ok")

    def test_ready_returns_200_when_db_up(self) -> None:
        response = self.client.get("/ready/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "ready")

    def test_ready_returns_503_when_db_down(self) -> None:
        with patch("apps.core.views.connection") as mock_conn:
            mock_conn.ensure_connection.side_effect = RuntimeError("db down")
            response = self.client.get("/ready/")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        body = response.json()
        self.assertEqual(body["code"], "db_unavailable")
        self.assertIn("detail", body)
        self.assertEqual(body["errors"], {})


class RequestIdTests(APITestCase):
    def test_generates_request_id_when_absent(self) -> None:
        response = self.client.get("/health/")
        self.assertIn("X-Request-ID", response.headers)
        self.assertTrue(len(response.headers["X-Request-ID"]) >= 8)

    def test_echoes_valid_request_id(self) -> None:
        rid = "client-trace-abc-123"
        response = self.client.get("/health/", HTTP_X_REQUEST_ID=rid)
        self.assertEqual(response.headers["X-Request-ID"], rid)

    def test_discards_invalid_request_id(self) -> None:
        response = self.client.get("/health/", HTTP_X_REQUEST_ID="bad id with spaces")
        self.assertNotEqual(response.headers["X-Request-ID"], "bad id with spaces")
        self.assertTrue(len(response.headers["X-Request-ID"]) >= 8)


class ExceptionEnvelopeTests(APITestCase):
    def test_validation_error_envelope_shape(self) -> None:
        factory = APIRequestFactory()
        request = factory.get("/health/")
        exc = ValidationError({"nome_social": ["Este campo é obrigatório."]})
        response = custom_exception_handler(exc, {"request": request})
        assert response is not None
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "validation_error")
        self.assertIn("detail", response.data)
        self.assertIn("nome_social", response.data["errors"])
