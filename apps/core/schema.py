"""Documentação dos caminhos de erro no OpenAPI.

Serializer e exemplos existem só para o schema: o runtime do envelope continua em
`apps/core/exceptions.py`, sem acoplamento.
"""

from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import serializers


class ErroSerializer(serializers.Serializer):
    code = serializers.CharField(help_text="Código estável do erro.")
    detail = serializers.CharField(help_text="Mensagem legível.")
    errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text="Mapa campo -> mensagens; vazio fora de erros de validação.",
    )


def _resposta(descricao: str, exemplo: OpenApiExample) -> OpenApiResponse:
    return OpenApiResponse(response=ErroSerializer, description=descricao, examples=[exemplo])


RESPOSTA_400 = _resposta(
    "Payload inválido.",
    OpenApiExample(
        "Campo obrigatório ausente",
        value={
            "code": "validation_error",
            "detail": "Dados inválidos.",
            "errors": {"nome_social": ["Este campo é obrigatório."]},
        },
        response_only=True,
    ),
)

RESPOSTA_401 = _resposta(
    "Token ausente, expirado ou inválido.",
    OpenApiExample(
        "Sem credenciais",
        value={
            "code": "not_authenticated",
            "detail": "As credenciais de autenticação não foram fornecidas.",
            "errors": {},
        },
        response_only=True,
    ),
)

RESPOSTA_404 = _resposta(
    "Recurso inexistente.",
    OpenApiExample(
        "Id desconhecido",
        value={"code": "not_found", "detail": "Não encontrado.", "errors": {}},
        response_only=True,
    ),
)

RESPOSTA_409 = _resposta(
    "Slot de agenda já ocupado por outra consulta agendada.",
    OpenApiExample(
        "Conflito de agenda",
        value={
            "code": "consulta_conflito",
            "detail": "Já existe consulta agendada para este profissional neste horário.",
            "errors": {},
        },
        response_only=True,
    ),
)

ERROS_ESCRITA = {400: RESPOSTA_400, 401: RESPOSTA_401}
ERROS_ESCRITA_COM_CONFLITO = {**ERROS_ESCRITA, 409: RESPOSTA_409}
ERROS_LEITURA = {401: RESPOSTA_401, 404: RESPOSTA_404}
