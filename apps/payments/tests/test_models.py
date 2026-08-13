from datetime import timedelta
from decimal import Decimal

from apps.consultas.models import Consulta
from apps.payments.models import Cobranca, WebhookEvent
from apps.profissionais.models import Profissional
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone


class CobrancaModelTests(TestCase):
    def setUp(self) -> None:
        profissional = Profissional.objects.create(
            nome_social="Dra. Ana",
            profissao="Psicóloga",
            endereco="Rua das Flores, 100 - São Paulo/SP",
            contato="ana@example.com",
        )
        self.consulta = Consulta.objects.create(
            profissional=profissional, data_hora=timezone.now() + timedelta(days=1)
        )

    def _cobranca(self, **overrides: object) -> Cobranca:
        dados = {
            "consulta": self.consulta,
            "valor": Decimal("150.00"),
            "asaas_payment_id": "pay_mock_1",
            "idempotency_key": "key-1",
            "percentual_profissional": Decimal("80.00"),
            "net_value": Decimal("142.50"),
        }
        dados.update(overrides)
        return Cobranca.objects.create(**dados)

    def test_apagar_consulta_com_cobranca_levanta_protected_error(self) -> None:
        self._cobranca()

        with self.assertRaises(ProtectedError):
            self.consulta.delete()

        self.assertEqual(Cobranca.objects.count(), 1)
        self.assertTrue(Consulta.objects.filter(pk=self.consulta.pk).exists())

    def test_idempotency_key_duplicada_viola_unique(self) -> None:
        self._cobranca()

        with self.assertRaises(IntegrityError), transaction.atomic():
            self._cobranca(asaas_payment_id="pay_mock_2")

        self.assertEqual(Cobranca.objects.count(), 1)

    def test_asaas_payment_id_duplicado_viola_unique(self) -> None:
        self._cobranca()

        with self.assertRaises(IntegrityError), transaction.atomic():
            self._cobranca(asaas_payment_id="pay_mock_1", idempotency_key="key-2")

        self.assertEqual(Cobranca.objects.count(), 1)

    def test_str_traz_payment_id_e_status(self) -> None:
        cobranca = self._cobranca()

        self.assertIn("pay_mock_1", str(cobranca))
        self.assertIn("pendente", str(cobranca))


class WebhookEventModelTests(TestCase):
    def test_mesmo_asaas_event_id_viola_unique(self) -> None:
        WebhookEvent.objects.create(asaas_event_id="evt_1", tipo="PAYMENT_CONFIRMED")

        with self.assertRaises(IntegrityError), transaction.atomic():
            WebhookEvent.objects.create(asaas_event_id="evt_1", tipo="PAYMENT_RECEIVED")

        self.assertEqual(WebhookEvent.objects.count(), 1)

    def test_modelo_nao_tem_campo_de_payload(self) -> None:
        nomes = {campo.name for campo in WebhookEvent._meta.get_fields() if campo.concrete}

        self.assertNotIn("payload", nomes)
        self.assertNotIn("body", nomes)
        self.assertNotIn("raw", nomes)
