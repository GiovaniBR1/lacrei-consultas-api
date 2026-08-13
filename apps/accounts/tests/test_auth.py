from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

URL_TOKEN = "/api/v1/auth/token/"
URL_REFRESH = "/api/v1/auth/token/refresh/"
URL_PROFISSIONAIS = "/api/v1/profissionais/"
SENHA = "senha-de-teste-123"


class TokenEndpointTests(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="operadora", password=SENHA)

    def test_credenciais_validas_devolvem_access_e_refresh(self) -> None:
        response = self.client.post(
            URL_TOKEN, {"username": "operadora", "password": SENHA}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        corpo = response.json()
        self.assertIn("access", corpo)
        self.assertIn("refresh", corpo)
        self.assertTrue(corpo["access"].count(".") == 2, corpo["access"])

    def test_credenciais_invalidas_devolvem_401_com_envelope(self) -> None:
        response = self.client.post(
            URL_TOKEN, {"username": "operadora", "password": "errada"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(set(response.json()), {"code", "detail", "errors"})

    def test_refresh_valido_devolve_novo_access(self) -> None:
        refresh = self.client.post(
            URL_TOKEN, {"username": "operadora", "password": SENHA}, format="json"
        ).json()["refresh"]

        response = self.client.post(URL_REFRESH, {"refresh": refresh}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())

    def test_refresh_reusado_apos_rotacao_e_rejeitado(self) -> None:
        primeiro_refresh = self.client.post(
            URL_TOKEN, {"username": "operadora", "password": SENHA}, format="json"
        ).json()["refresh"]
        self.client.post(URL_REFRESH, {"refresh": primeiro_refresh}, format="json")

        reuso = self.client.post(URL_REFRESH, {"refresh": primeiro_refresh}, format="json")

        self.assertEqual(reuso.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(set(reuso.json()), {"code", "detail", "errors"})


class PermissaoDefaultTests(APITestCase):
    def setUp(self) -> None:
        get_user_model().objects.create_user(username="operadora", password=SENHA)

    def _access_token(self) -> str:
        resposta = self.client.post(
            URL_TOKEN, {"username": "operadora", "password": SENHA}, format="json"
        )
        return resposta.json()["access"]

    def test_crud_sem_token_devolve_401_com_envelope(self) -> None:
        response = self.client.get(URL_PROFISSIONAIS)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        corpo = response.json()
        self.assertEqual(corpo["code"], "not_authenticated")
        self.assertEqual(set(corpo), {"code", "detail", "errors"})

    def test_consultas_sem_token_devolve_401(self) -> None:
        response = self.client.get("/api/v1/consultas/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crud_com_bearer_token_devolve_200(self) -> None:
        token = self._access_token()

        response = self.client.get(URL_PROFISSIONAIS, HTTP_AUTHORIZATION=f"Bearer {token}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_invalido_devolve_401(self) -> None:
        response = self.client.get(URL_PROFISSIONAIS, HTTP_AUTHORIZATION="Bearer token-invalido")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_probes_continuam_abertas_sem_token(self) -> None:
        for url in ("/health/", "/ready/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
