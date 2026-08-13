"""HTTP de cobrança e (depois) webhook. JWT nas cobranças; webhook é público."""

from __future__ import annotations

from uuid import UUID

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.consultas.models import Consulta
from apps.core.schema import ERROS_ESCRITA, RESPOSTA_404
from apps.payments.exceptions import IdempotencyKeyRequired, SplitWalletEmissor
from apps.payments.gateway import EmitterWalletError, SplitInvalido
from apps.payments.serializers import CobrancaCreateSerializer, CobrancaSerializer
from apps.payments.services import criar_cobranca


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
