"""Consulta agendada. A regra anti–double booking mora no banco (AD-007)."""

from django.db import models

from apps.core.models import UUIDBaseModel

SLOT_CONSTRAINT = "uniq_consulta_agendada_slot"


class Consulta(UUIDBaseModel):
    class Status(models.TextChoices):
        AGENDADA = "agendada", "Agendada"
        CANCELADA = "cancelada", "Cancelada"
        CONCLUIDA = "concluida", "Concluída"

    profissional = models.ForeignKey(
        "profissionais.Profissional",
        on_delete=models.CASCADE,
        related_name="consultas",
        verbose_name="profissional",
    )
    data_hora = models.DateTimeField("data e hora")
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.AGENDADA
    )

    class Meta:
        ordering = ("-data_hora",)
        verbose_name = "consulta"
        verbose_name_plural = "consultas"
        constraints = [
            models.UniqueConstraint(
                fields=("profissional", "data_hora"),
                condition=models.Q(status="agendada"),
                name=SLOT_CONSTRAINT,
            )
        ]
        indexes = [
            models.Index(fields=("profissional", "data_hora"), name="idx_consulta_prof_data")
        ]

    def __str__(self) -> str:
        return f"{self.profissional_id} @ {self.data_hora:%Y-%m-%d %H:%M} ({self.status})"
