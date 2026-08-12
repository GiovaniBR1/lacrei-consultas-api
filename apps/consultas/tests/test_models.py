from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.consultas.models import Consulta
from apps.profissionais.models import Profissional


class ConsultaSlotConstraintTests(TestCase):
    def setUp(self) -> None:
        self.profissional = Profissional.objects.create(
            nome_social="Dra. Ana",
            profissao="Psicóloga",
            endereco="Rua das Flores, 100 - São Paulo/SP",
            contato="ana@example.com",
        )
        self.slot = timezone.now() + timedelta(days=1)

    def test_segunda_agendada_no_mesmo_slot_viola_constraint(self) -> None:
        Consulta.objects.create(profissional=self.profissional, data_hora=self.slot)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Consulta.objects.create(profissional=self.profissional, data_hora=self.slot)
        self.assertEqual(Consulta.objects.filter(data_hora=self.slot).count(), 1)

    def test_mesmo_slot_com_status_cancelada_e_permitido(self) -> None:
        Consulta.objects.create(profissional=self.profissional, data_hora=self.slot)
        Consulta.objects.create(
            profissional=self.profissional,
            data_hora=self.slot,
            status=Consulta.Status.CANCELADA,
        )
        self.assertEqual(Consulta.objects.filter(data_hora=self.slot).count(), 2)

    def test_cancelar_libera_o_slot_para_nova_agendada(self) -> None:
        primeira = Consulta.objects.create(profissional=self.profissional, data_hora=self.slot)
        primeira.status = Consulta.Status.CANCELADA
        primeira.save(update_fields=["status"])

        nova = Consulta.objects.create(profissional=self.profissional, data_hora=self.slot)

        self.assertEqual(nova.status, Consulta.Status.AGENDADA)
        self.assertEqual(
            Consulta.objects.filter(data_hora=self.slot, status=Consulta.Status.AGENDADA).count(),
            1,
        )

    def test_mesmo_slot_para_outro_profissional_e_permitido(self) -> None:
        outro = Profissional.objects.create(
            nome_social="Dr. Bê",
            profissao="Clínico geral",
            endereco="Av. Paulista, 1000 - São Paulo/SP",
            contato="be@example.com",
        )
        Consulta.objects.create(profissional=self.profissional, data_hora=self.slot)
        Consulta.objects.create(profissional=outro, data_hora=self.slot)

        self.assertEqual(
            Consulta.objects.filter(data_hora=self.slot, status=Consulta.Status.AGENDADA).count(),
            2,
        )
