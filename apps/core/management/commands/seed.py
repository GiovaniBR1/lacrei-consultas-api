"""Popula o banco com dados sintéticos para avaliar a API em um comando."""

from __future__ import annotations

import os
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.consultas.models import Consulta
from apps.payments.models import Cobranca
from apps.profissionais.models import Profissional

SENHA_PADRAO_LOCAL = "lacrei-local-123"
IDEMPOTENCY_SEED = "seed-cobranca-agendada"

PROFISSIONAIS = (
    {
        "nome_social": "Dra. Ana Ribeiro",
        "profissao": "Psicóloga",
        "endereco": "Rua das Flores, 100 - São Paulo/SP",
        "contato": "ana@example.com",
        "asaas_wallet_id": "wlt_seed_ana",
    },
    {
        "nome_social": "Dr. Bê Nascimento",
        "profissao": "Clínico geral",
        "endereco": "Av. Paulista, 1000 - São Paulo/SP",
        "contato": "be@example.com",
        "asaas_wallet_id": "wlt_seed_be",
    },
)


class Command(BaseCommand):
    help = "Cria usuário operacional, profissionais e consultas de exemplo (idempotente)."

    def handle(self, *args, **options) -> None:
        self._checar_ambiente()

        usuario, senha = self._criar_usuario()
        profissionais = self._criar_profissionais()
        consultas = self._criar_consultas(profissionais)
        cobrancas = self._criar_cobranca(profissionais)

        self.stdout.write(self.style.SUCCESS(f"usuário: {usuario.username} / senha: {senha}"))
        self.stdout.write(self.style.SUCCESS(f"profissionais: {len(profissionais)}"))
        self.stdout.write(self.style.SUCCESS(f"consultas: {consultas}"))
        self.stdout.write(self.style.SUCCESS(f"cobranças: {cobrancas}"))
        self.stdout.write("token: POST /api/v1/auth/token/ com as credenciais acima")

    def _checar_ambiente(self) -> None:
        if settings.DEBUG:
            return
        if os.environ.get("ALLOW_SEED", "").lower() != "true":
            raise CommandError(
                "seed bloqueado fora de desenvolvimento: exporte ALLOW_SEED=true para liberar."
            )
        if not os.environ.get("SEED_PASSWORD"):
            raise CommandError("SEED_PASSWORD é obrigatório fora de desenvolvimento.")

    def _criar_usuario(self):
        username = os.environ.get("SEED_USERNAME", "operadora")
        senha = os.environ.get("SEED_PASSWORD") or SENHA_PADRAO_LOCAL

        usuario, criado = get_user_model().objects.get_or_create(username=username)
        if criado:
            usuario.set_password(senha)
            usuario.save(update_fields=["password"])
        return usuario, senha if criado else "(inalterada)"

    def _criar_profissionais(self) -> list[Profissional]:
        criados = []
        for dados in PROFISSIONAIS:
            profissional, _ = Profissional.objects.get_or_create(
                nome_social=dados["nome_social"], defaults=dados
            )
            if not profissional.asaas_wallet_id:
                profissional.asaas_wallet_id = dados["asaas_wallet_id"]
                profissional.save(update_fields=["asaas_wallet_id"])
            criados.append(profissional)
        return criados

    def _criar_consultas(self, profissionais: list[Profissional]) -> int:
        ana, be = profissionais
        base = timezone.now().replace(minute=0, second=0, microsecond=0)

        agenda = (
            (ana, base + timedelta(days=1), Consulta.Status.AGENDADA),
            (ana, base + timedelta(days=2), Consulta.Status.CANCELADA),
            (be, base - timedelta(days=3), Consulta.Status.CONCLUIDA),
        )
        for profissional, quando, status in agenda:
            Consulta.objects.get_or_create(
                profissional=profissional, data_hora=quando, status=status
            )
        return len(agenda)

    def _criar_cobranca(self, profissionais: list[Profissional]) -> int:
        ana = profissionais[0]
        consulta = Consulta.objects.filter(
            profissional=ana, status=Consulta.Status.AGENDADA
        ).earliest("data_hora")
        Cobranca.objects.get_or_create(
            idempotency_key=IDEMPOTENCY_SEED,
            defaults={
                "consulta": consulta,
                "valor": Decimal("150.00"),
                "asaas_payment_id": "pay_mock_seed",
                "percentual_profissional": Decimal("80.00"),
                "net_value": Decimal("142.50"),
            },
        )
        return 1
