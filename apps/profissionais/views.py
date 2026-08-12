"""Endpoints CRUD de profissionais."""

from rest_framework import viewsets

from apps.profissionais.models import Profissional
from apps.profissionais.serializers import ProfissionalListSerializer, ProfissionalSerializer


class ProfissionalViewSet(viewsets.ModelViewSet):
    queryset = Profissional.objects.all()
    serializer_class = ProfissionalSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return ProfissionalListSerializer
        return super().get_serializer_class()
