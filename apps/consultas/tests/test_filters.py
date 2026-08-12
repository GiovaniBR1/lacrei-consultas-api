import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.consultas.models import Consulta
from apps.profissionais.models import Profissional

URL_LISTA = "/api/v1/consultas/"


class ConsultaFiltroTests(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="operadora", password="senha-de-teste"
        )
        self.client.force_authenticate(user=self.user)
        self.ana = Profissional.objects.create(
            nome_social="Dra. Ana",
            profissao="Psicóloga",
            endereco="Rua das Flores, 100 - São Paulo/SP",
            contato="ana@example.com",
        )
        self.be = Profissional.objects.create(
            nome_social="Dr. Bê",
            profissao="Clínico geral",
            endereco="Av. Paulista, 1000 - São Paulo/SP",
            contato="be@example.com",
        )
        agora = timezone.now()
        self.amanha = agora + timedelta(days=1)
        self.semana = agora + timedelta(days=7)
        self.consulta_amanha = Consulta.objects.create(profissional=self.ana, data_hora=self.amanha)
        self.consulta_semana = Consulta.objects.create(
            profissional=self.ana, data_hora=self.semana, status=Consulta.Status.CANCELADA
        )
        self.consulta_be = Consulta.objects.create(profissional=self.be, data_hora=self.amanha)

    def test_filtro_por_profissional_devolve_so_as_dele(self) -> None:
        response = self.client.get(URL_LISTA, {"profissional": str(self.ana.id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.json()}
        self.assertEqual(ids, {str(self.consulta_amanha.id), str(self.consulta_semana.id)})

    def test_filtro_por_profissional_inexistente_devolve_lista_vazia(self) -> None:
        response = self.client.get(URL_LISTA, {"profissional": str(uuid.uuid4())})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_filtro_por_profissional_malformado_devolve_400(self) -> None:
        response = self.client.get(URL_LISTA, {"profissional": "nao-e-uuid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["code"], "validation_error")

    def test_filtro_por_status(self) -> None:
        response = self.client.get(URL_LISTA, {"status": "cancelada"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        corpo = response.json()
        self.assertEqual([item["id"] for item in corpo], [str(self.consulta_semana.id)])

    def test_faixa_de_data_hora_recorta_o_resultado(self) -> None:
        corte_inicio = (self.amanha + timedelta(hours=1)).isoformat()

        response = self.client.get(URL_LISTA, {"data_hora_after": corte_inicio})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.json()], [str(self.consulta_semana.id)])

    def test_faixa_com_before_exclui_o_futuro_distante(self) -> None:
        corte_fim = (self.amanha + timedelta(hours=1)).isoformat()

        response = self.client.get(URL_LISTA, {"data_hora_before": corte_fim})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.json()}
        self.assertEqual(ids, {str(self.consulta_amanha.id), str(self.consulta_be.id)})

    def test_ordering_crescente_por_data_hora(self) -> None:
        response = self.client.get(
            URL_LISTA, {"profissional": str(self.ana.id), "ordering": "data_hora"}
        )

        self.assertEqual(
            [item["id"] for item in response.json()],
            [str(self.consulta_amanha.id), str(self.consulta_semana.id)],
        )

    def test_ordering_decrescente_por_data_hora(self) -> None:
        response = self.client.get(
            URL_LISTA, {"profissional": str(self.ana.id), "ordering": "-data_hora"}
        )

        self.assertEqual(
            [item["id"] for item in response.json()],
            [str(self.consulta_semana.id), str(self.consulta_amanha.id)],
        )
