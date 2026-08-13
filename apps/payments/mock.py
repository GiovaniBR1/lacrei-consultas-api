"""Cliente Asaas fictício, fiel ao contrato (split percentual, netValue, sem wallet do emissor)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from django.conf import settings

from apps.payments.gateway import EmitterWalletError, PaymentResult, SplitInvalido, SplitItem

TAXA_FICTICIA = Decimal("0.05")


class MockAsaasClient:
    def create_payment(
        self,
        valor: Decimal,
        split: list[SplitItem],
        external_reference: str,
        idempotency_key: str,
    ) -> PaymentResult:
        if not split:
            raise SplitInvalido("split percentual é obrigatório")
        emissor = settings.ASAAS_WALLET_PLATFORM
        for item in split:
            if item.wallet_id == emissor:
                raise EmitterWalletError("wallet do emissor não pode entrar no split")
            if item.percentual_value is None:
                raise SplitInvalido("MVP aceita apenas percentualValue")
        liquido = (valor * (1 - TAXA_FICTICIA)).quantize(Decimal("0.01"))
        return PaymentResult(payment_id=f"pay_mock_{uuid4().hex[:12]}", net_value=liquido)
