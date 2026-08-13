"""Serializers de cobrança. Campos explícitos; split no formato OpenAPI Asaas (`walletId`)."""

from decimal import Decimal

from rest_framework import serializers

from apps.payments.models import Cobranca


class SplitItemSerializer(serializers.Serializer):
    walletId = serializers.CharField()
    percentualValue = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )


class CobrancaCreateSerializer(serializers.Serializer):
    valor = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    split = SplitItemSerializer(many=True, required=False)


class CobrancaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cobranca
        fields = (
            "id",
            "consulta",
            "valor",
            "status",
            "split_status",
            "asaas_payment_id",
            "percentual_profissional",
            "net_value",
            "split_ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = fields
