"""Endpoints CRUD de profissionais."""

from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.core.schema import ERROS_ESCRITA, ERROS_LEITURA
from apps.payments.exceptions import ProfissionalComCobranca
from apps.profissionais.models import Profissional
from apps.profissionais.serializers import ProfissionalListSerializer, ProfissionalSerializer


@extend_schema_view(
    list=extend_schema(responses={200: ProfissionalListSerializer(many=True), **ERROS_LEITURA}),
    retrieve=extend_schema(responses={200: ProfissionalSerializer, **ERROS_LEITURA}),
    create=extend_schema(responses={201: ProfissionalSerializer, **ERROS_ESCRITA}),
    update=extend_schema(responses={200: ProfissionalSerializer, **ERROS_ESCRITA, **ERROS_LEITURA}),
    partial_update=extend_schema(
        responses={200: ProfissionalSerializer, **ERROS_ESCRITA, **ERROS_LEITURA}
    ),
    destroy=extend_schema(responses={204: None, **ERROS_LEITURA}),
)
class ProfissionalViewSet(viewsets.ModelViewSet):
    queryset = Profissional.objects.all()
    serializer_class = ProfissionalSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return ProfissionalListSerializer
        return super().get_serializer_class()

    def perform_destroy(self, instance: Profissional) -> None:
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ProfissionalComCobranca from exc
