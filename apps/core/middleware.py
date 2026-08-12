"""Middleware X-Request-ID."""

from __future__ import annotations

import re
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from apps.core.logging import set_request_id

_REQUEST_ID_RE = re.compile(r"^[!-~]{1,128}$")
HEADER = "X-Request-ID"


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
        response = self.get_response(request)
        response[HEADER] = request_id
        return response
