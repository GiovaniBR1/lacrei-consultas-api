"""Filtros de consulta: profissional, faixa de data/hora e status."""

import django_filters

from apps.consultas.models import Consulta


class ConsultaFilter(django_filters.FilterSet):
    profissional = django_filters.UUIDFilter(field_name="profissional_id")
    data_hora = django_filters.IsoDateTimeFromToRangeFilter()

    class Meta:
        model = Consulta
        fields = ("profissional", "status", "data_hora")
