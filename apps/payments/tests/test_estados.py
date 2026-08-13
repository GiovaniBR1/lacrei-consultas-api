from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.consultas.models import Consulta
from apps.payments.models import Cobranca
from apps.payments.services import atualizar_split
from apps.profissionais.models import Profissional

TOKEN = "token-webhook-teste"
URL_WEBHOOK = "/webhooks/asaas/"


@override_settings(ASAAS_MODE="mock", ASAAS_WEBHOOK_TOKEN=TOKEN)
class EstadosCobrancaTests(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="operadora", password="senha")
        self.client.force_authenticate(user=self.user)
        self.profissional = Profissional.objects.create(
            nome_social="Dra. Ana",
            profissao="Psicóloga",
            endereco="Rua das Flores, 100 - São Paulo/SP",
            contato="ana@example.com",
        )
        self.consulta = Consulta.objects.create(
            profissional=self.profissional, data_hora=timezone.now() + timedelta(days=1)
        )
        self.cobranca = Cobranca.objects.create(
            consulta=self.consulta,
            valor=Decimal("150.00"),
            asaas_payment_id="pay_mock_estados",
            idempotency_key="key-estados",
            percentual_profissional=Decimal("80.00"),
            net_value=Decimal("142.50"),
        )

    def _evento(self, event_id: str, event: str):
        return self.client.post(
            URL_WEBHOOK,
            {
                "id": event_id,
                "event": event,
                "payment": {"id": self.cobranca.asaas_payment_id},
            },
            format="json",
            HTTP_ASAAS_ACCESS_TOKEN=TOKEN,
        )

    def test_divergencia_block_marca_split_bloqueado(self) -> None:
        response = self._evento("evt_div", "PAYMENT_SPLIT_DIVERGENCE_BLOCK")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cobranca.refresh_from_db()
        self.assertEqual(self.cobranca.split_status, Cobranca.SplitStatus.BLOQUEADO_DIVERGENCIA)

    def test_divergencia_finished_conclui_se_recebida(self) -> None:
        self._evento("evt_rec", "PAYMENT_RECEIVED")
        self._evento("evt_fin", "PAYMENT_SPLIT_DIVERGENCE_BLOCK_FINISHED")

        self.cobranca.refresh_from_db()
        self.assertEqual(self.cobranca.status, Cobranca.Status.RECEBIDA)
        self.assertEqual(self.cobranca.split_status, Cobranca.SplitStatus.CONCLUIDO)

    def test_divergencia_finished_cancela_se_nao_recebida(self) -> None:
        self._evento("evt_fin2", "PAYMENT_SPLIT_DIVERGENCE_BLOCK_FINISHED")

        self.cobranca.refresh_from_db()
        self.assertEqual(self.cobranca.status, Cobranca.Status.PENDENTE)
        self.assertEqual(self.cobranca.split_status, Cobranca.SplitStatus.CANCELADO)

    def test_omitir_split_nao_zera_configuracao(self) -> None:
        original = self.cobranca.split_status
        atualizar_split(self.cobranca, None)

        self.cobranca.refresh_from_db()
        self.assertTrue(self.cobranca.split_ativo)
        self.assertEqual(self.cobranca.split_status, original)
        self.assertEqual(self.cobranca.percentual_profissional, Decimal("80.00"))

    def test_split_vazio_desativa(self) -> None:
        atualizar_split(self.cobranca, [])

        self.cobranca.refresh_from_db()
        self.assertFalse(self.cobranca.split_ativo)
        self.assertEqual(self.cobranca.split_status, Cobranca.SplitStatus.CANCELADO)

    def test_pix_received_de_pendente_chega_em_recebida(self) -> None:
        self._evento("evt_pix", "PAYMENT_RECEIVED")

        self.cobranca.refresh_from_db()
        self.assertEqual(self.cobranca.status, Cobranca.Status.RECEBIDA)
        self.assertEqual(self.cobranca.split_status, Cobranca.SplitStatus.CONCLUIDO)

    def test_confirmed_tardio_nao_regride_recebida(self) -> None:
        self._evento("evt_pix2", "PAYMENT_RECEIVED")
        self._evento("evt_late", "PAYMENT_CONFIRMED")

        self.cobranca.refresh_from_db()
        self.assertEqual(self.cobranca.status, Cobranca.Status.RECEBIDA)
        self.assertNotEqual(self.cobranca.status, Cobranca.Status.CONFIRMADA)

    def test_payment_deleted_cancela_cobranca_e_split(self) -> None:
        self._evento("evt_del", "PAYMENT_DELETED")

        self.cobranca.refresh_from_db()
        self.assertEqual(self.cobranca.status, Cobranca.Status.CANCELADA)
        self.assertEqual(self.cobranca.split_status, Cobranca.SplitStatus.CANCELADO)

    def test_delete_consulta_com_cobranca_devolve_409(self) -> None:
        response = self.client.delete(f"/api/v1/consultas/{self.consulta.id}/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.json()["code"], "consulta_com_cobranca")
        self.assertTrue(Consulta.objects.filter(pk=self.consulta.pk).exists())
        self.assertTrue(Cobranca.objects.filter(pk=self.cobranca.pk).exists())

    def test_delete_profissional_com_cobranca_devolve_409(self) -> None:
        response = self.client.delete(f"/api/v1/profissionais/{self.profissional.id}/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.json()["code"], "profissional_com_cobranca")
        self.assertTrue(Profissional.objects.filter(pk=self.profissional.pk).exists())
        self.assertTrue(Cobranca.objects.filter(pk=self.cobranca.pk).exists())
