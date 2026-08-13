from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.throttling import SimpleRateThrottle

URL_TOKEN = "/api/v1/auth/token/"
URL_PROFISSIONAIS = "/api/v1/profissionais/"
SENHA = "senha-de-teste-123"


class TaxasConfiguradasTests(SimpleTestCase):
    def test_settings_definem_user_anon_e_auth_token(self) -> None:
        taxas = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]

        self.assertEqual(set(taxas), {"user", "anon", "auth_token"})
        self.assertEqual(taxas["auth_token"], "5/min")
        self.assertEqual(taxas["user"], "120/min")
        self.assertEqual(taxas["anon"], "20/min")


class ThrottleTokenTests(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        # O DRF congela DEFAULT_THROTTLE_RATES em SimpleRateThrottle.THROTTLE_RATES no import,
        # então override_settings não alcança as taxas: é preciso trocar o dicionário.
        patch = mock.patch.dict(
            SimpleRateThrottle.THROTTLE_RATES, {"auth_token": "2/min", "anon": "2/min"}
        )
        patch.start()
        self.addCleanup(patch.stop)
        get_user_model().objects.create_user(username="operadora", password=SENHA)

    def _post_token(self):
        return self.client.post(
            URL_TOKEN, {"username": "operadora", "password": SENHA}, format="json"
        )

    def test_excesso_no_endpoint_de_token_devolve_429_com_envelope(self) -> None:
        self.assertEqual(self._post_token().status_code, status.HTTP_200_OK)
        self.assertEqual(self._post_token().status_code, status.HTTP_200_OK)

        bloqueada = self._post_token()

        self.assertEqual(bloqueada.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        corpo = bloqueada.json()
        self.assertEqual(corpo["code"], "throttled")
        self.assertEqual(set(corpo), {"code", "detail", "errors"})

    def test_crud_autenticado_nao_entra_na_contagem_do_token(self) -> None:
        access = self._post_token().json()["access"]
        self._post_token()
        self.assertEqual(self._post_token().status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        for _ in range(5):
            resposta = self.client.get(URL_PROFISSIONAIS, HTTP_AUTHORIZATION=f"Bearer {access}")
            self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_probes_de_infra_ficam_fora_do_throttle_anonimo(self) -> None:
        for _ in range(5):
            self.assertEqual(self.client.get("/health/").status_code, status.HTTP_200_OK)
