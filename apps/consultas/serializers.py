"""Contrato de consulta. Campos explícitos e agenda sempre no futuro."""

from django.utils import timezone
from rest_framework import serializers

from apps.consultas.models import Consulta


class ConsultaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consulta
        fields = ("id", "profissional", "data_hora", "status", "criado_em", "atualizado_em")
        read_only_fields = ("id", "criado_em", "atualizado_em")

    def validate(self, attrs: dict) -> dict:
        status = attrs.get("status") or getattr(self.instance, "status", Consulta.Status.AGENDADA)
        data_hora = attrs.get("data_hora") or getattr(self.instance, "data_hora", None)

        if status == Consulta.Status.AGENDADA and data_hora and data_hora < timezone.now():
            raise serializers.ValidationError(
                {"data_hora": ["Não é possível agendar consulta em horário passado."]}
            )
        return attrs
