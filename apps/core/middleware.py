"""Middleware X-Request-ID e log de acesso."""

from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from apps.core.logging import set_request_id

_REQUEST_ID_RE = re.compile(r"^[!-~]{1,128}$")
HEADER = "X-Request-ID"

# Só método, rota e status: headers, corpo e query string ficam de fora para não vazar PII.
access_logger = logging.getLogger("apps.core.request")


class RequestIdMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming = request.headers.get(HEADER, "")
        if incoming and _REQUEST_ID_RE.fullmatch(incoming):
            request_id = incoming
        else:
            request_id = str(uuid.uuid4())

        request.request_id = request_id  # type: ignore[attr-defined]
        set_request_id(request_id)
        inicio = time.monotonic()
        response = self.get_response(request)
        duracao_ms = int((time.monotonic() - inicio) * 1000)
        response[HEADER] = request_id

        access_logger.info(
            "method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.path,
            response.status_code,
            duracao_ms,
        )
        return response
