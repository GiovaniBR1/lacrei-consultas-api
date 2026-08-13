"""Comando seed: dado de avaliação, idempotência e guardas de ambiente."""

import os
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.consultas.models import Consulta
from apps.payments.models import Cobranca
from apps.profissionais.models import Profissional


@override_settings(DEBUG=True)  # o runner força DEBUG=False; aqui emulamos o ambiente local
class SeedTests(TestCase):
    def _rodar(self) -> str:
        saida = StringIO()
        call_command("seed", stdout=saida)
        return saida.getvalue()

    def test_cria_usuario_profissionais_e_consultas(self) -> None:
        saida = self._rodar()

        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(Profissional.objects.count(), 2)
        self.assertEqual(Consulta.objects.count(), 3)
        self.assertEqual(Cobranca.objects.count(), 1)
        self.assertIn("operadora", saida)

    def test_profissionais_usam_nome_social(self) -> None:
        self._rodar()

        nomes = set(Profissional.objects.values_list("nome_social", flat=True))
        self.assertEqual(nomes, {"Dra. Ana Ribeiro", "Dr. Bê Nascimento"})

    def test_cobre_os_tres_status_de_consulta(self) -> None:
        self._rodar()

        self.assertEqual(
            set(Consulta.objects.values_list("status", flat=True)),
            {"agendada", "cancelada", "concluida"},
        )

    def test_rodar_duas_vezes_nao_duplica_nem_estoura_constraint(self) -> None:
        self._rodar()
        self._rodar()

        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(Profissional.objects.count(), 2)
        self.assertEqual(Consulta.objects.count(), 3)
        self.assertEqual(Cobranca.objects.count(), 1)

    def test_cobranca_pendente_na_consulta_agendada(self) -> None:
        self._rodar()

        cobranca = Cobranca.objects.get()
        self.assertEqual(cobranca.status, Cobranca.Status.PENDENTE)
        self.assertEqual(cobranca.consulta.status, Consulta.Status.AGENDADA)
        self.assertEqual(cobranca.idempotency_key, "seed-cobranca-agendada")
        wallets = set(Profissional.objects.values_list("asaas_wallet_id", flat=True))
        self.assertEqual(wallets, {"wlt_seed_ana", "wlt_seed_be"})

    def test_usuario_criado_consegue_autenticar_com_a_senha_informada(self) -> None:
        self._rodar()

        usuario = get_user_model().objects.get(username="operadora")
        self.assertTrue(usuario.check_password("lacrei-local-123"))


@override_settings(DEBUG=False)
class SeedGuardaDeAmbienteTests(TestCase):
    @mock.patch.dict(os.environ, {"ALLOW_SEED": "", "SEED_PASSWORD": ""}, clear=False)
    def test_recusa_rodar_fora_de_desenvolvimento(self) -> None:
        with self.assertRaises(CommandError) as capturado:
            call_command("seed")

        self.assertIn("ALLOW_SEED", str(capturado.exception))
        self.assertEqual(Profissional.objects.count(), 0)

    @mock.patch.dict(os.environ, {"ALLOW_SEED": "true", "SEED_PASSWORD": ""}, clear=False)
    def test_exige_senha_explicita_fora_de_desenvolvimento(self) -> None:
        with self.assertRaises(CommandError) as capturado:
            call_command("seed")

        self.assertIn("SEED_PASSWORD", str(capturado.exception))

    @mock.patch.dict(
        os.environ, {"ALLOW_SEED": "true", "SEED_PASSWORD": "senha-de-staging"}, clear=False
    )
    def test_com_guardas_satisfeitas_roda_e_usa_a_senha_do_ambiente(self) -> None:
        call_command("seed", stdout=StringIO())

        usuario = get_user_model().objects.get(username="operadora")
        self.assertTrue(usuario.check_password("senha-de-staging"))
