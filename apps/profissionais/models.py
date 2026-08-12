"""Profissional de saúde: só nome de tratamento, sem nome civil ou CPF (AD-010)."""

from django.db import models

from apps.core.models import UUIDBaseModel


class Profissional(UUIDBaseModel):
    nome_social = models.CharField("nome social", max_length=150)
    profissao = models.CharField("profissão", max_length=100)
    endereco = models.CharField("endereço", max_length=255)
    contato = models.CharField("contato", max_length=100)
    asaas_wallet_id = models.CharField("wallet Asaas", max_length=64, blank=True, default="")

    class Meta:
        ordering = ("nome_social",)
        verbose_name = "profissional"
        verbose_name_plural = "profissionais"

    def __str__(self) -> str:
        return f"{self.nome_social} ({self.profissao})"
