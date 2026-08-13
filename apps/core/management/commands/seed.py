"""Popula o banco com dados sintéticos para avaliar a API em um comando."""

from __future__ import annotations

import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.consultas.models import Consulta
from apps.profissionais.models import Profissional

SENHA_PADRAO_LOCAL = "lacrei-local-123"

PROFISSIONAIS = (
    {
        "nome_social": "Dra. Ana Ribeiro",
        "profissao": "Psicóloga",
        "endereco": "Rua das Flores, 100 - São Paulo/SP",
        "contato": "ana@example.com",
    },
    {
        "nome_social": "Dr. Bê Nascimento",
        "profissao": "Clínico geral",
        "endereco": "Av. Paulista, 1000 - São Paulo/SP",
        "contato": "be@example.com",
    },
)


class Command(BaseCommand):
    help = "Cria usuário operacional, profissionais e consultas de exemplo (idempotente)."

    def handle(self, *args, **options) -> None:
        self._checar_ambiente()

        usuario, senha = self._criar_usuario()
        profissionais = self._criar_profissionais()
        consultas = self._criar_consultas(profissionais)

        self.stdout.write(self.style.SUCCESS(f"usuário: {usuario.username} / senha: {senha}"))
        self.stdout.write(self.style.SUCCESS(f"profissionais: {len(profissionais)}"))
        self.stdout.write(self.style.SUCCESS(f"consultas: {consultas}"))
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
        return [
            Profissional.objects.get_or_create(nome_social=dados["nome_social"], defaults=dados)[0]
            for dados in PROFISSIONAIS
        ]

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
