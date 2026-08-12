import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.consultas.models import Consulta
from apps.consultas.serializers import ConsultaSerializer
from apps.profissionais.models import Profissional


class ConsultaSerializerTests(TestCase):
    def setUp(self) -> None:
        self.profissional = Profissional.objects.create(
            nome_social="Dra. Ana",
            profissao="Psicóloga",
            endereco="Rua das Flores, 100 - São Paulo/SP",
            contato="ana@example.com",
        )
        self.futuro = timezone.now() + timedelta(days=1)
        self.passado = timezone.now() - timedelta(hours=1)

    def test_agendada_no_futuro_e_valida(self) -> None:
        serializer = ConsultaSerializer(
            data={"profissional": str(self.profissional.id), "data_hora": self.futuro.isoformat()}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        consulta = serializer.save()
        self.assertEqual(consulta.status, Consulta.Status.AGENDADA)

    def test_agendada_no_passado_e_invalida(self) -> None:
        serializer = ConsultaSerializer(
            data={
                "profissional": str(self.profissional.id),
                "data_hora": self.passado.isoformat(),
                "status": Consulta.Status.AGENDADA,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("data_hora", serializer.errors)

    def test_cancelada_no_passado_e_valida(self) -> None:
        serializer = ConsultaSerializer(
            data={
                "profissional": str(self.profissional.id),
                "data_hora": self.passado.isoformat(),
                "status": Consulta.Status.CANCELADA,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_profissional_inexistente_e_invalido(self) -> None:
        serializer = ConsultaSerializer(
            data={"profissional": str(uuid.uuid4()), "data_hora": self.futuro.isoformat()}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("profissional", serializer.errors)

    def test_mover_consulta_agendada_para_o_passado_e_invalido(self) -> None:
        consulta = Consulta.objects.create(profissional=self.profissional, data_hora=self.futuro)

        serializer = ConsultaSerializer(
            consulta, data={"data_hora": self.passado.isoformat()}, partial=True
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("data_hora", serializer.errors)
