"""Casos de uso de cobrança. A view só traduz HTTP."""

from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.consultas.models import Consulta
from apps.payments.gateway import SplitItem, get_gateway
from apps.payments.models import Cobranca

PERCENTUAL_DEFAULT = Decimal("80.00")


def wallet_do_profissional(consulta: Consulta) -> str:
    wallet = consulta.profissional.asaas_wallet_id
    return wallet or f"wlt_{consulta.profissional_id}"


def criar_cobranca(
    consulta: Consulta,
    valor: Decimal,
    split_payload: list[dict] | None,
    idempotency_key: str,
) -> tuple[Cobranca, bool]:
    existente = Cobranca.objects.filter(idempotency_key=idempotency_key).first()
    if existente:
        return existente, False

    if split_payload:
        itens = [
            SplitItem(
                wallet_id=item["walletId"],
                percentual_value=item.get("percentualValue"),
            )
            for item in split_payload
        ]
        percentual = itens[0].percentual_value or PERCENTUAL_DEFAULT
    else:
        itens = [
            SplitItem(
                wallet_id=wallet_do_profissional(consulta), percentual_value=PERCENTUAL_DEFAULT
            )
        ]
        percentual = PERCENTUAL_DEFAULT

    resultado = get_gateway().create_payment(
        valor=valor,
        split=itens,
        external_reference=str(consulta.id),
        idempotency_key=idempotency_key,
    )
    try:
        with transaction.atomic():
            cobranca = Cobranca.objects.create(
                consulta=consulta,
                valor=valor,
                asaas_payment_id=resultado.payment_id,
                idempotency_key=idempotency_key,
                percentual_profissional=percentual,
                net_value=resultado.net_value,
            )
    except IntegrityError:
        existente = Cobranca.objects.filter(idempotency_key=idempotency_key).first()
        if existente:
            return existente, False
        raise
    return cobranca, True
