"""Contrato de paginação: shape, navegação e teto de página."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.profissionais.models import Profissional

URL_LISTA = "/api/v1/profissionais/"
TOTAL = 25


class PaginacaoTests(APITestCase):
    def setUp(self) -> None:
        self.client.force_authenticate(
            user=get_user_model().objects.create_user(username="operadora", password="senha")
        )
        Profissional.objects.bulk_create(
            Profissional(
                nome_social=f"Profissional {indice:02d}",
                profissao="Psicóloga",
                endereco="Rua das Flores, 100 - São Paulo/SP",
                contato=f"p{indice}@example.com",
            )
            for indice in range(TOTAL)
        )

    def test_shape_paginado(self) -> None:
        corpo = self.client.get(URL_LISTA).json()

        self.assertEqual(set(corpo), {"count", "next", "previous", "results"})
        self.assertEqual(corpo["count"], TOTAL)

    def test_primeira_pagina_tem_vinte_itens_e_proxima(self) -> None:
        corpo = self.client.get(URL_LISTA).json()

        self.assertEqual(len(corpo["results"]), 20)
        self.assertIsNotNone(corpo["next"])
        self.assertIsNone(corpo["previous"])

    def test_segunda_pagina_tem_o_resto_e_anterior(self) -> None:
        corpo = self.client.get(URL_LISTA, {"page": 2}).json()

        self.assertEqual(len(corpo["results"]), TOTAL - 20)
        self.assertIsNone(corpo["next"])
        self.assertIsNotNone(corpo["previous"])

    def test_page_size_customizado_e_respeitado(self) -> None:
        corpo = self.client.get(URL_LISTA, {"page_size": 5}).json()

        self.assertEqual(len(corpo["results"]), 5)

    def test_pagina_fora_do_intervalo_devolve_404_com_envelope(self) -> None:
        response = self.client.get(URL_LISTA, {"page": 99})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        corpo = response.json()
        self.assertEqual(corpo["code"], "not_found")
        self.assertEqual(set(corpo), {"code", "detail", "errors"})

    def test_consultas_tambem_sao_paginadas(self) -> None:
        corpo = self.client.get("/api/v1/consultas/").json()

        self.assertEqual(set(corpo), {"count", "next", "previous", "results"})


class TetoDePaginaTests(APITestCase):
    """Precisa de mais registros que o teto, senão o teste não distingue teto de 'tudo'."""

    ACIMA_DO_TETO = 105

    def setUp(self) -> None:
        self.client.force_authenticate(
            user=get_user_model().objects.create_user(username="operadora", password="senha")
        )
        Profissional.objects.bulk_create(
            Profissional(
                nome_social=f"Profissional {indice:03d}",
                profissao="Psicóloga",
                endereco="Rua das Flores, 100 - São Paulo/SP",
                contato=f"p{indice}@example.com",
            )
            for indice in range(self.ACIMA_DO_TETO)
        )

    def test_page_size_acima_do_teto_e_limitado_a_cem(self) -> None:
        corpo = self.client.get(URL_LISTA, {"page_size": 5000}).json()

        self.assertEqual(corpo["count"], self.ACIMA_DO_TETO)
        self.assertEqual(len(corpo["results"]), 100)
        self.assertIsNotNone(corpo["next"])
