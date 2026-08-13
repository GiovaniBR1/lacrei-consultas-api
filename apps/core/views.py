"""Health (liveness), Ready (readiness) e as rotas de documentação da API."""

from __future__ import annotations

from django.conf import settings
from django.db import connection
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


@extend_schema(responses={200: OpenApiTypes.OBJECT})
class HealthView(APIView):
    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes: list = []

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


@extend_schema(responses={200: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT})
class ReadyView(APIView):
    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes: list = []

    def get(self, request: Request) -> Response:
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return Response(
                {
                    "code": "db_unavailable",
                    "detail": "Banco de dados indisponível.",
                    "errors": {},
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"status": "ready"}, status=status.HTTP_200_OK)


class DocsDesligavelMixin:
    """Documentação é inventário de API: desligável por ambiente (AD-025)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def initial(self, request: Request, *args, **kwargs) -> None:
        if not settings.SPECTACULAR_ENABLED:
            raise NotFound()
        super().initial(request, *args, **kwargs)


class SchemaView(DocsDesligavelMixin, SpectacularAPIView):
    pass


class SwaggerView(DocsDesligavelMixin, SpectacularSwaggerView):
    pass
