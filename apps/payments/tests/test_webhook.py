from datetime import timedelta
from decimal import Decimal

from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.consultas.models import Consulta
from apps.payments.models import Cobranca, WebhookEvent
from apps.profissionais.models import Profissional

TOKEN = "token-webhook-teste"
URL = "/webhooks/asaas/"


@override_settings(ASAAS_MODE="mock", ASAAS_WEBHOOK_TOKEN=TOKEN)
class WebhookAsaasTests(APITestCase):
    def setUp(self) -> None:
        profissional = Profissional.objects.create(
            nome_social="Dra. Ana",
            profissao="Psicóloga",
            endereco="Rua das Flores, 100 - São Paulo/SP",
            contato="ana@example.com",
        )
        consulta = Consulta.objects.create(
            profissional=profissional, data_hora=timezone.now() + timedelta(days=1)
        )
        self.cobranca = Cobranca.objects.create(
            consulta=consulta,
            valor=Decimal("150.00"),
            asaas_payment_id="pay_mock_abc",
            idempotency_key="key-wh-1",
            percentual_profissional=Decimal("80.00"),
            net_value=Decimal("142.50"),
        )

    def _post(self, payload: dict, token: str | None = TOKEN):
        headers = {}
        if token is not None:
            headers["HTTP_ASAAS_ACCESS_TOKEN"] = token
        return self.client.post(URL, payload, format="json", **headers)

    def _payload(self, event_id: str, event: str, extra: dict | None = None) -> dict:
        corpo = {
            "id": event_id,
            "event": event,
            "payment": {"id": self.cobranca.asaas_payment_id},
        }
        if extra:
            corpo.update(extra)
        return corpo

    def test_token_valido_persiste_e_devolve_200_sem_jwt(self) -> None:
        response = self._post(self._payload("evt_1", "PAYMENT_CONFIRMED"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(WebhookEvent.objects.count(), 1)
        evento = WebhookEvent.objects.get()
        self.assertEqual(evento.asaas_event_id, "evt_1")
        self.assertEqual(evento.tipo, "PAYMENT_CONFIRMED")

    def test_token_invalido_devolve_401_sem_persistir(self) -> None:
        response = self._post(self._payload("evt_2", "PAYMENT_CONFIRMED"), token="errado")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["code"], "not_authenticated")
        self.assertEqual(WebhookEvent.objects.count(), 0)

    def test_token_ausente_devolve_401_sem_persistir(self) -> None:
        response = self._post(self._payload("evt_3", "PAYMENT_CONFIRMED"), token=None)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(WebhookEvent.objects.count(), 0)

    def test_replay_do_mesmo_id_nao_reaplica_transicao(self) -> None:
        self._post(self._payload("evt_replay", "PAYMENT_CONFIRMED"))
        response = self._post(self._payload("evt_replay", "PAYMENT_RECEIVED"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(WebhookEvent.objects.count(), 1)
        self.cobranca.refresh_from_db()
        self.assertEqual(self.cobranca.status, Cobranca.Status.CONFIRMADA)
        self.assertNotEqual(self.cobranca.status, Cobranca.Status.RECEBIDA)

    def test_payment_confirmed_nao_implica_recebida(self) -> None:
        self._post(self._payload("evt_conf", "PAYMENT_CONFIRMED"))

        self.cobranca.refresh_from_db()
        self.assertEqual(self.cobranca.status, Cobranca.Status.CONFIRMADA)
        self.assertEqual(self.cobranca.split_status, Cobranca.SplitStatus.CONFIGURADO)

    def test_payment_received_marca_recebida_e_split_concluido(self) -> None:
        self._post(self._payload("evt_rec", "PAYMENT_RECEIVED"))

        self.cobranca.refresh_from_db()
        self.assertEqual(self.cobranca.status, Cobranca.Status.RECEBIDA)
        self.assertEqual(self.cobranca.split_status, Cobranca.SplitStatus.CONCLUIDO)

    def test_json_com_campos_extras_nao_gera_5xx(self) -> None:
        extra = {"creditCard": {"number": "411111"}, "foo": "bar", "nested": {"x": 1}}
        response = self._post(self._payload("evt_extra", "PAYMENT_CONFIRMED", extra=extra))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response.status_code, 500)
        self.assertEqual(WebhookEvent.objects.count(), 1)
        evento = WebhookEvent.objects.get()
        self.assertFalse(hasattr(evento, "payload"))
        self.assertNotIn("creditCard", evento.__dict__)

    def test_log_registra_tipo_e_ids_sem_o_body(self) -> None:
        extra = {"creditCard": {"number": "411111"}}
        with self.assertLogs("apps.payments.webhook", level="INFO") as captured:
            self._post(self._payload("evt_log", "PAYMENT_CONFIRMED", extra=extra))

        texto = " ".join(captured.output)
        self.assertIn("PAYMENT_CONFIRMED", texto)
        self.assertIn("evt_log", texto)
        self.assertIn("pay_mock_abc", texto)
        self.assertNotIn("411111", texto)
        self.assertNotIn("creditCard", texto)
