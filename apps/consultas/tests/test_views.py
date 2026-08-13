"""Ramos de tratamento de erro do ViewSet que a rota feliz não alcança."""

from datetime import timedelta
from unittest import mock

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.consultas.models import Consulta
from apps.consultas.serializers import ConsultaSerializer
from apps.consultas.views import ConsultaViewSet
from apps.profissionais.models import Profissional


class SalvarIntegrityErrorTests(TestCase):
    def setUp(self) -> None:
        self.profissional = Profissional.objects.create(
            nome_social="Dra. Ana",
            profissao="Psicóloga",
            endereco="Rua das Flores, 100 - São Paulo/SP",
            contato="ana@example.com",
        )
        self.slot = timezone.now() + timedelta(days=1)

    def _serializer(self, **extra) -> ConsultaSerializer:
        dados = {
            "profissional": str(self.profissional.id),
            "data_hora": self.slot.isoformat(),
            **extra,
        }
        serializer = ConsultaSerializer(data=dados)
        serializer.is_valid(raise_exception=True)
        return serializer

    def test_integrity_error_alheio_ao_slot_sobe_intacto(self) -> None:
        serializer = self._serializer()

        with mock.patch.object(
            ConsultaSerializer, "save", side_effect=IntegrityError("coluna x violada")
        ):
            with self.assertRaises(IntegrityError) as capturado:
                ConsultaViewSet()._salvar(serializer)

        self.assertIn("coluna x violada", str(capturado.exception))

    def test_slot_ocupado_vira_conflito(self) -> None:
        Consulta.objects.create(profissional=self.profissional, data_hora=self.slot)
        serializer = self._serializer()

        with mock.patch.object(
            ConsultaSerializer, "save", side_effect=IntegrityError("unique violada")
        ):
            with self.assertRaises(Exception) as capturado:
                ConsultaViewSet()._salvar(serializer)

        self.assertEqual(getattr(capturado.exception, "status_code", None), 409)

    def test_status_nao_agendado_nunca_e_tratado_como_conflito(self) -> None:
        Consulta.objects.create(profissional=self.profissional, data_hora=self.slot)
        serializer = self._serializer(status=Consulta.Status.CANCELADA)

        self.assertFalse(ConsultaViewSet._slot_ja_agendado(serializer))
