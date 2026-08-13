"""HTTP de cobrança (JWT) e webhook Asaas (token próprio, sem JWT)."""

from __future__ import annotations

import hmac
import logging
from uuid import UUID

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.consultas.models import Consulta
from apps.core.schema import ERROS_ESCRITA, RESPOSTA_401, RESPOSTA_404
from apps.payments.exceptions import (
    IdempotencyKeyRequired,
    SplitWalletEmissor,
    WebhookTokenInvalido,
)
from apps.payments.gateway import EmitterWalletError, SplitInvalido
from apps.payments.serializers import CobrancaCreateSerializer, CobrancaSerializer
from apps.payments.services import aplicar_evento, criar_cobranca, registrar_webhook

logger = logging.getLogger("apps.payments.webhook")


@extend_schema(
    request=CobrancaCreateSerializer,
    responses={
        201: CobrancaSerializer,
        200: CobrancaSerializer,
        **ERROS_ESCRITA,
        404: RESPOSTA_404,
    },
)
class CobrancaCreateView(APIView):
    serializer_class = CobrancaCreateSerializer

    def post(self, request: Request, consulta_id: UUID) -> Response:
        chave = request.headers.get("Idempotency-Key")
        if not chave:
            raise IdempotencyKeyRequired()

        consulta = get_object_or_404(Consulta, pk=consulta_id)
        serializer = CobrancaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cobranca, criada = criar_cobranca(
                consulta=consulta,
                valor=serializer.validated_data["valor"],
                split_payload=serializer.validated_data.get("split"),
                idempotency_key=chave,
            )
        except EmitterWalletError as exc:
            raise SplitWalletEmissor from exc
        except SplitInvalido as exc:
            raise ValidationError({"split": [str(exc)]}) from exc

        corpo = CobrancaSerializer(cobranca).data
        return Response(corpo, status=status.HTTP_201_CREATED if criada else status.HTTP_200_OK)


@extend_schema(
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT, 401: RESPOSTA_401},
)
class WebhookAsaasView(APIView):
    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "asaas_webhook"

    def post(self, request: Request) -> Response:
        esperado = str(getattr(settings, "ASAAS_WEBHOOK_TOKEN", "") or "")
        recebido = request.headers.get("asaas-access-token") or ""
        if not esperado or not hmac.compare_digest(esperado, recebido):
            raise WebhookTokenInvalido()

        event_id = str(request.data.get("id") or "")
        tipo = str(request.data.get("event") or "")
        payment = request.data.get("payment")
        payment_id = str(payment.get("id") or "") if isinstance(payment, dict) else ""

        logger.info("tipo=%s event_id=%s payment_id=%s", tipo, event_id, payment_id)

        if event_id and registrar_webhook(event_id, tipo, payment_id):
            aplicar_evento(tipo, payment_id)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)
