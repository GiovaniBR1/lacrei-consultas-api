"""Envelope de erro JSON estável: {code, detail, errors}."""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ConsultaConflito(APIException):
    """Slot de agenda já ocupado por outra consulta agendada."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Já existe consulta agendada para este profissional neste horário."
    default_code = "consulta_conflito"


def _normalize_errors(detail: Any) -> dict[str, Any]:
    if detail is None:
        return {}
    if isinstance(detail, dict):
        return detail
    if isinstance(detail, list):
        return {"non_field_errors": detail}
    return {"non_field_errors": [str(detail)]}


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None

    code = getattr(exc, "default_code", None) or getattr(exc, "code", None) or "error"
    if isinstance(code, bytes):
        code = code.decode()

    detail = response.data
    errors: dict[str, Any] = {}
    message = "Erro na requisição."

    if isinstance(detail, dict):
        if "detail" in detail and len(detail) == 1:
            message = str(detail["detail"])
        else:
            errors = _normalize_errors(detail)
            message = "Dados inválidos." if response.status_code == 400 else message
            if "detail" in detail and isinstance(detail["detail"], str):
                message = detail["detail"]
                errors = {k: v for k, v in detail.items() if k != "detail"}
    elif isinstance(detail, list):
        errors = _normalize_errors(detail)
        message = "Dados inválidos."
    else:
        message = str(detail)

    if response.status_code == status.HTTP_400_BAD_REQUEST and code in {"invalid", "error"}:
        code = "validation_error"
    if response.status_code == status.HTTP_401_UNAUTHORIZED and code == "not_authenticated":
        code = "not_authenticated"
    if response.status_code == status.HTTP_404_NOT_FOUND:
        code = "not_found"

    response.data = {
        "code": str(code),
        "detail": message,
        "errors": errors if isinstance(errors, dict) else {},
    }
    return response
