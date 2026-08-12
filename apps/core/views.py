"""Health (liveness) e Ready (readiness)."""

from __future__ import annotations

from django.db import connection
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class ReadyView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

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
