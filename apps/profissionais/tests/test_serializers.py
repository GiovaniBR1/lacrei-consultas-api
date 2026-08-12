import uuid

from django.test import TestCase

from apps.profissionais.models import Profissional
from apps.profissionais.serializers import ProfissionalListSerializer, ProfissionalSerializer

PAYLOAD_VALIDO = {
    "nome_social": "Dra. Ana",
    "profissao": "Psicóloga",
    "endereco": "Rua das Flores, 100 - São Paulo/SP",
    "contato": "ana@example.com",
}


class ProfissionalSerializerTests(TestCase):
    def test_payload_valido_cria_profissional_com_uuid(self) -> None:
        serializer = ProfissionalSerializer(data=PAYLOAD_VALIDO)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        profissional = serializer.save()

        self.assertIsInstance(profissional.id, uuid.UUID)
        self.assertEqual(profissional.nome_social, "Dra. Ana")
        self.assertEqual(profissional.contato, "ana@example.com")

    def test_campo_obrigatorio_ausente_e_invalido(self) -> None:
        payload = {k: v for k, v in PAYLOAD_VALIDO.items() if k != "nome_social"}

        serializer = ProfissionalSerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn("nome_social", serializer.errors)

    def test_nome_social_em_branco_e_invalido(self) -> None:
        serializer = ProfissionalSerializer(data={**PAYLOAD_VALIDO, "nome_social": ""})

        self.assertFalse(serializer.is_valid())
        self.assertIn("nome_social", serializer.errors)

    def test_campos_sensiveis_nao_sao_aceitos_nem_persistidos(self) -> None:
        payload = {
            **PAYLOAD_VALIDO,
            "nome_civil": "Nome Registrado",
            "cpf": "000.000.000-00",
            "orientacao_sexual": "bissexual",
            "identidade_genero": "mulher trans",
        }

        serializer = ProfissionalSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        profissional = serializer.save()

        for campo in ("nome_civil", "cpf", "orientacao_sexual", "identidade_genero"):
            self.assertNotIn(campo, serializer.fields)
            self.assertFalse(hasattr(profissional, campo))
        self.assertNotIn("nome_civil", ProfissionalSerializer(profissional).data)

    def test_serializer_de_lista_omite_contato_e_wallet(self) -> None:
        profissional = Profissional.objects.create(**PAYLOAD_VALIDO)

        dados = ProfissionalListSerializer(profissional).data

        self.assertNotIn("contato", dados)
        self.assertNotIn("asaas_wallet_id", dados)
        self.assertEqual(dados["nome_social"], "Dra. Ana")
