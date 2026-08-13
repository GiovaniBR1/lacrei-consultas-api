"""Cobrança e evento de webhook. A trilha financeira trava o delete da consulta (AD-026)."""

from django.db import models

from apps.core.models import UUIDBaseModel


class Cobranca(UUIDBaseModel):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONFIRMADA = "confirmada", "Confirmada"
        RECEBIDA = "recebida", "Recebida"
        CANCELADA = "cancelada", "Cancelada"
        FALHA = "falha", "Falha"
        VENCIDA = "vencida", "Vencida"
        ESTORNADA = "estornada", "Estornada"

    class SplitStatus(models.TextChoices):
        CONFIGURADO = "configurado", "Configurado"
        CONCLUIDO = "concluido", "Concluído"
        CANCELADO = "cancelado", "Cancelado"
        BLOQUEADO_DIVERGENCIA = "bloqueado_divergencia", "Bloqueado por divergência"

    consulta = models.ForeignKey(
        "consultas.Consulta",
        on_delete=models.PROTECT,
        related_name="cobrancas",
        verbose_name="consulta",
    )
    valor = models.DecimalField("valor", max_digits=10, decimal_places=2)
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.PENDENTE
    )
    split_status = models.CharField(
        "status do split",
        max_length=32,
        choices=SplitStatus.choices,
        default=SplitStatus.CONFIGURADO,
    )
    asaas_payment_id = models.CharField("id Asaas", max_length=64, unique=True)
    idempotency_key = models.CharField("idempotency key", max_length=128, unique=True)
    percentual_profissional = models.DecimalField(
        "percentual do profissional", max_digits=5, decimal_places=2
    )
    net_value = models.DecimalField("valor líquido", max_digits=10, decimal_places=2)
    split_ativo = models.BooleanField("split ativo", default=True)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "cobrança"
        verbose_name_plural = "cobranças"

    def __str__(self) -> str:
        return f"{self.asaas_payment_id} ({self.status})"


class WebhookEvent(UUIDBaseModel):
    asaas_event_id = models.CharField("id do evento Asaas", max_length=128, unique=True)
    tipo = models.CharField("tipo", max_length=80)
    asaas_payment_id = models.CharField(
        "id Asaas da cobrança", max_length=64, blank=True, default=""
    )

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "evento de webhook"
        verbose_name_plural = "eventos de webhook"

    def __str__(self) -> str:
        return f"{self.tipo} {self.asaas_event_id}"
