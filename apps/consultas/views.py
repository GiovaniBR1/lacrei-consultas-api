"""Endpoints CRUD de consultas. O banco decide o conflito de agenda; aqui só traduzimos."""

from django.db import IntegrityError, transaction
from rest_framework import viewsets

from apps.consultas.models import Consulta
from apps.consultas.serializers import ConsultaSerializer
from apps.core.exceptions import ConsultaConflito


class ConsultaViewSet(viewsets.ModelViewSet):
    queryset = Consulta.objects.select_related("profissional")
    serializer_class = ConsultaSerializer

    def perform_create(self, serializer: ConsultaSerializer) -> None:
        self._salvar(serializer)

    def perform_update(self, serializer: ConsultaSerializer) -> None:
        self._salvar(serializer)

    def _salvar(self, serializer: ConsultaSerializer) -> None:
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError as exc:
            # O texto do IntegrityError não cita o nome da constraint em todos os bancos,
            # então classificamos o conflito relendo o slot depois do rollback.
            if not self._slot_ja_agendado(serializer):
                raise
            raise ConsultaConflito from exc

    @staticmethod
    def _slot_ja_agendado(serializer: ConsultaSerializer) -> bool:
        dados = serializer.validated_data
        instance = serializer.instance
        profissional = dados.get("profissional") or getattr(instance, "profissional", None)
        data_hora = dados.get("data_hora") or getattr(instance, "data_hora", None)
        status = dados.get("status") or getattr(instance, "status", Consulta.Status.AGENDADA)

        if status != Consulta.Status.AGENDADA or not profissional or not data_hora:
            return False
        return Consulta.objects.filter(
            profissional=profissional,
            data_hora=data_hora,
            status=Consulta.Status.AGENDADA,
        ).exists()
