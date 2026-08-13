from decimal import Decimal

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from apps.payments.gateway import EmitterWalletError, SplitInvalido, SplitItem, get_gateway
from apps.payments.mock import MockAsaasClient

WALLET_PROF = "wlt_profissional"
WALLET_PLATAFORMA = "wlt_platform_mock"


@override_settings(ASAAS_MODE="mock", ASAAS_WALLET_PLATFORM=WALLET_PLATAFORMA)
class MockAsaasClientTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = MockAsaasClient()

    def test_rejeita_wallet_do_emissor(self) -> None:
        with self.assertRaises(EmitterWalletError):
            self.client.create_payment(
                Decimal("100.00"),
                [SplitItem(wallet_id=WALLET_PLATAFORMA, percentual_value=Decimal("80"))],
                external_reference="consulta-1",
                idempotency_key="k1",
            )

    def test_net_value_e_menor_que_o_bruto(self) -> None:
        resultado = self.client.create_payment(
            Decimal("100.00"),
            [SplitItem(wallet_id=WALLET_PROF, percentual_value=Decimal("80"))],
            external_reference="consulta-1",
            idempotency_key="k1",
        )

        self.assertEqual(resultado.net_value, Decimal("95.00"))
        self.assertNotEqual(resultado.net_value, Decimal("100.00"))
        self.assertTrue(resultado.payment_id.startswith("pay_mock_"))

    def test_recusa_split_sem_percentual(self) -> None:
        with self.assertRaises(SplitInvalido):
            self.client.create_payment(
                Decimal("100.00"),
                [SplitItem(wallet_id=WALLET_PROF, percentual_value=None)],
                external_reference="consulta-1",
                idempotency_key="k1",
            )

    def test_recusa_split_vazio(self) -> None:
        with self.assertRaises(SplitInvalido):
            self.client.create_payment(
                Decimal("100.00"),
                [],
                external_reference="consulta-1",
                idempotency_key="k1",
            )


class FactoryTests(SimpleTestCase):
    @override_settings(ASAAS_MODE="mock")
    def test_modo_mock_devolve_mock(self) -> None:
        self.assertIsInstance(get_gateway(), MockAsaasClient)

    @override_settings(ASAAS_MODE="sandbox")
    def test_sandbox_nao_implementado(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            get_gateway()

    @override_settings(ASAAS_MODE="prod")
    def test_prod_nao_implementado(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            get_gateway()
