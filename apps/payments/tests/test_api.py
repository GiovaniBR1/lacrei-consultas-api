from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.consultas.models import Consulta
from apps.payments.models import Cobranca
from apps.profissionais.models import Profissional

WALLET_PLATAFORMA = "wlt_platform_mock"
WALLET_PROF = "wlt_ana"


@override_settings(ASAAS_MODE="mock", ASAAS_WALLET_PLATFORM=WALLET_PLATAFORMA)
class CobrancaApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="operadora", password="senha")
        self.client.force_authenticate(user=self.user)
        self.profissional = Profissional.objects.create(
            nome_social="Dra. Ana",
            profissao="Psicóloga",
            endereco="Rua das Flores, 100 - São Paulo/SP",
            contato="ana@example.com",
            asaas_wallet_id=WALLET_PROF,
        )
        self.consulta = Consulta.objects.create(
            profissional=self.profissional, data_hora=timezone.now() + timedelta(days=1)
        )
        self.url = f"/api/v1/consultas/{self.consulta.id}/cobrancas/"

    def _post(self, **headers):
        extra = {"HTTP_IDEMPOTENCY_KEY": "key-1", **headers}
        return self.client.post(self.url, {"valor": "150.00"}, format="json", **extra)

    def test_create_retorna_201_pendente(self) -> None:
        response = self._post()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        corpo = response.json()
        self.assertEqual(corpo["status"], "pendente")
        self.assertTrue(corpo["asaas_payment_id"].startswith("pay_mock_"))
        self.assertEqual(Cobranca.objects.count(), 1)

    def test_replay_da_mesma_key_devolve_200_sem_duplicar(self) -> None:
        primeira = self._post().json()
        segunda = self._post()

        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.assertEqual(segunda.json()["asaas_payment_id"], primeira["asaas_payment_id"])
        self.assertEqual(Cobranca.objects.count(), 1)

    def test_sem_idempotency_key_devolve_400(self) -> None:
        response = self.client.post(self.url, {"valor": "150.00"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["code"], "idempotency_key_required")
        self.assertEqual(Cobranca.objects.count(), 0)

    def test_consulta_inexistente_devolve_404(self) -> None:
        url = "/api/v1/consultas/00000000-0000-0000-0000-000000000000/cobrancas/"
        response = self.client.post(
            url, {"valor": "150.00"}, format="json", HTTP_IDEMPOTENCY_KEY="key-x"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["code"], "not_found")

    def test_wallet_do_emissor_devolve_400(self) -> None:
        response = self.client.post(
            self.url,
            {
                "valor": "150.00",
                "split": [{"walletId": WALLET_PLATAFORMA, "percentualValue": "80.00"}],
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="key-emissor",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["code"], "split_wallet_emissor")
        self.assertEqual(Cobranca.objects.count(), 0)

    def test_sem_jwt_devolve_401(self) -> None:
        self.client.force_authenticate(user=None)
        response = self._post()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
