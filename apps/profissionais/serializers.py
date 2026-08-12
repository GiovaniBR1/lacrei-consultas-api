"""Contratos de profissional. Campos sempre explícitos, nunca `__all__` (R5–R6)."""

from rest_framework import serializers

from apps.profissionais.models import Profissional


class ProfissionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profissional
        fields = (
            "id",
            "nome_social",
            "profissao",
            "endereco",
            "contato",
            "asaas_wallet_id",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")


class ProfissionalListSerializer(serializers.ModelSerializer):
    """Listagem minimizada: sem contato nem dados de pagamento (AD-010)."""

    class Meta:
        model = Profissional
        fields = ("id", "nome_social", "profissao", "endereco", "criado_em", "atualizado_em")
        read_only_fields = fields
