import logging
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from rest_framework import status
from rest_framework.exceptions import APIException, Throttled, ValidationError
from rest_framework.test import APIRequestFactory, APITestCase

from apps.core.exceptions import ConsultaConflito, _normalize_errors, custom_exception_handler
from apps.core.logging import RequestIdFilter, get_request_id


class HealthReadyTests(APITestCase):
    def test_health_returns_200_without_db(self) -> None:
        with patch("apps.core.views.connection") as mock_conn:
            response = self.client.get("/health/")
            mock_conn.ensure_connection.assert_not_called()
            mock_conn.cursor.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "ok")

    def test_ready_returns_200_when_db_up(self) -> None:
        response = self.client.get("/ready/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "ready")

    def test_ready_returns_503_when_db_down(self) -> None:
        with patch("apps.core.views.connection") as mock_conn:
            mock_conn.ensure_connection.side_effect = RuntimeError(
                "connection to server at postgres://secret@db failed"
            )
            response = self.client.get("/ready/")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        body = response.json()
        self.assertEqual(body["code"], "db_unavailable")
        self.assertIn("detail", body)
        self.assertEqual(body["errors"], {})
        payload = str(body)
        self.assertNotIn("postgres://", payload)
        self.assertNotIn("secret@", payload)


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

    def test_discards_oversized_request_id(self) -> None:
        oversized = "a" * 129
        response = self.client.get("/health/", HTTP_X_REQUEST_ID=oversized)
        self.assertNotEqual(response.headers["X-Request-ID"], oversized)
        self.assertLessEqual(len(response.headers["X-Request-ID"]), 128)

    def test_request_id_available_to_structured_logs(self) -> None:
        rid = "log-correlation-id-42"
        response = self.client.get("/health/", HTTP_X_REQUEST_ID=rid)
        self.assertEqual(response.headers["X-Request-ID"], rid)
        self.assertEqual(get_request_id(), rid)

        record = MagicMock(spec=logging.LogRecord)
        RequestIdFilter().filter(record)
        self.assertEqual(record.request_id, rid)


class AccessLogTests(APITestCase):
    def test_uma_linha_por_request_com_campos_exigidos(self) -> None:
        rid = "trace-do-log-1"

        with self.assertLogs("apps.core.request", level="INFO") as capturado:
            self.client.get("/health/", HTTP_X_REQUEST_ID=rid)

        self.assertEqual(len(capturado.records), 1)
        registro = capturado.records[0]
        RequestIdFilter().filter(registro)
        self.assertEqual(registro.request_id, rid)
        mensagem = registro.getMessage()
        self.assertIn("method=GET", mensagem)
        self.assertIn("path=/health/", mensagem)
        self.assertIn("status=200", mensagem)

    def test_authorization_nao_aparece_no_log(self) -> None:
        token = "token-super-secreto-nao-logar"

        with self.assertLogs("apps.core.request", level="INFO") as capturado:
            self.client.get("/api/v1/profissionais/", HTTP_AUTHORIZATION=f"Bearer {token}")

        saida = "\n".join(capturado.output)
        self.assertNotIn(token, saida)
        self.assertNotIn("Bearer", saida)
        self.assertIn("status=401", saida)


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

    def test_excecao_fora_do_drf_nao_vira_envelope(self) -> None:
        factory = APIRequestFactory()
        request = factory.get("/health/")

        resposta = custom_exception_handler(RuntimeError("boom"), {"request": request})

        self.assertIsNone(resposta, "erro não-DRF deve virar 500 do Django, não 200 disfarçado")

    def test_detail_em_lista_vira_non_field_errors(self) -> None:
        factory = APIRequestFactory()
        request = factory.post("/api/v1/consultas/")

        resposta = custom_exception_handler(
            ValidationError(["Horário indisponível."]), {"request": request}
        )

        assert resposta is not None
        self.assertEqual(resposta.data["code"], "validation_error")
        self.assertEqual(resposta.data["errors"]["non_field_errors"], ["Horário indisponível."])

    def test_throttled_mantem_code_e_envelope(self) -> None:
        factory = APIRequestFactory()
        request = factory.post("/api/v1/auth/token/")

        resposta = custom_exception_handler(Throttled(wait=30), {"request": request})

        assert resposta is not None
        self.assertEqual(resposta.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(resposta.data["code"], "throttled")
        self.assertEqual(set(resposta.data), {"code", "detail", "errors"})

    def test_consulta_conflito_envelope_shape(self) -> None:
        factory = APIRequestFactory()
        request = factory.post("/api/v1/consultas/")
        response = custom_exception_handler(ConsultaConflito(), {"request": request})
        assert response is not None
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "consulta_conflito")
        self.assertEqual(
            response.data["detail"],
            "Já existe consulta agendada para este profissional neste horário.",
        )
        self.assertEqual(response.data["errors"], {})


class NormalizeErrorsTests(APITestCase):
    def test_detail_ausente_vira_dicionario_vazio(self) -> None:
        self.assertEqual(_normalize_errors(None), {})

    def test_detail_escalar_vira_non_field_errors(self) -> None:
        self.assertEqual(_normalize_errors("Falhou."), {"non_field_errors": ["Falhou."]})

    def test_code_em_bytes_e_decodificado(self) -> None:
        exc = APIException("Falhou.")
        exc.default_code = b"code_em_bytes"
        factory = APIRequestFactory()

        resposta = custom_exception_handler(exc, {"request": factory.get("/health/")})

        assert resposta is not None
        self.assertEqual(resposta.data["code"], "code_em_bytes")


class SeedCommandTests(APITestCase):
    def test_seed_roda_sem_erro_e_avisa_que_e_noop(self) -> None:
        saida = StringIO()

        call_command("seed", stdout=saida)

        self.assertIn("noop", saida.getvalue())
