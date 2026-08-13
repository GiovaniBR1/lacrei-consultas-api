"""Trava o schema de `Profissional`: nada de dado sensível novo sem revisão de privacidade."""

from django.test import SimpleTestCase

from apps.profissionais.models import Profissional

CAMPOS_PERMITIDOS = {
    "id",
    "criado_em",
    "atualizado_em",
    "nome_social",
    "profissao",
    "endereco",
    "contato",
    "asaas_wallet_id",
}


class SchemaDePrivacidadeTests(SimpleTestCase):
    def test_modelo_so_tem_os_campos_aprovados(self) -> None:
        campos = {campo.name for campo in Profissional._meta.get_fields() if campo.concrete}

        self.assertEqual(
            campos,
            CAMPOS_PERMITIDOS,
            "Campo novo em Profissional exige revisão de privacidade (SEC-08): "
            f"inesperados={sorted(campos - CAMPOS_PERMITIDOS)} "
            f"faltando={sorted(CAMPOS_PERMITIDOS - campos)}",
        )

    def test_sem_campos_de_identificacao_civil_ou_saude(self) -> None:
        proibidos = {"cpf", "rg", "nome_civil", "nome_registro", "data_nascimento", "genero"}
        campos = {campo.name for campo in Profissional._meta.get_fields() if campo.concrete}

        self.assertEqual(campos & proibidos, set())
