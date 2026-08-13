"""Exceções de pagamento com código estável no envelope."""

from rest_framework import status
from rest_framework.exceptions import APIException


class IdempotencyKeyRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "O header Idempotency-Key é obrigatório."
    default_code = "idempotency_key_required"


class SplitWalletEmissor(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A wallet da conta emissora não pode entrar no split."
    default_code = "split_wallet_emissor"


class WebhookTokenInvalido(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Token de webhook inválido ou ausente."
    default_code = "not_authenticated"


class ProfissionalComCobranca(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Não é possível excluir profissional com cobrança vinculada."
    default_code = "profissional_com_cobranca"


class ConsultaComCobranca(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Não é possível excluir consulta com cobrança vinculada."
    default_code = "consulta_com_cobranca"
