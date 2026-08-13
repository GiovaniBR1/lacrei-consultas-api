"""Porta hexagonal do Asaas: contrato estável, implementação escolhida por ASAAS_MODE."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class EmitterWalletError(Exception):
    """Split inclui a wallet da conta emissora — o Asaas rejeita."""


class SplitInvalido(Exception):
    """Split ausente, vazio ou sem percentualValue (MVP só aceita percentual)."""


@dataclass(frozen=True)
class SplitItem:
    wallet_id: str
    percentual_value: Decimal | None = None


@dataclass(frozen=True)
class PaymentResult:
    payment_id: str
    net_value: Decimal


class PaymentGateway(Protocol):
    def create_payment(
        self,
        valor: Decimal,
        split: list[SplitItem],
        external_reference: str,
        idempotency_key: str,
    ) -> PaymentResult: ...


def get_gateway() -> PaymentGateway:
    modo = getattr(settings, "ASAAS_MODE", "mock")
    if modo == "mock":
        from apps.payments.mock import MockAsaasClient

        return MockAsaasClient()
    raise ImproperlyConfigured(
        f"ASAAS_MODE={modo} não implementado nesta entrega (mock-first, AD-004)."
    )
