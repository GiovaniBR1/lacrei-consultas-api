import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.consultas.models import Consulta
from apps.profissionais.models import Profissional

URL_LISTA = "/api/v1/profissionais/"

PAYLOAD_VALIDO = {
    "nome_social": "Dra. Ana",
    "profissao": "Psicóloga",
    "endereco": "Rua das Flores, 100 - São Paulo/SP",
    "contato": "ana@example.com",
}


class ProfissionalApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="operadora", password="senha-de-teste"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_retorna_201_com_id_uuid(self) -> None:
        response = self.client.post(URL_LISTA, PAYLOAD_VALIDO, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        corpo = response.json()
        self.assertEqual(uuid.UUID(corpo["id"]).version, 4)
        self.assertEqual(corpo["nome_social"], "Dra. Ana")
        self.assertEqual(Profissional.objects.count(), 1)

    def test_list_omite_contato(self) -> None:
        Profissional.objects.create(**PAYLOAD_VALIDO)

        response = self.client.get(URL_LISTA)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        corpo = response.json()
        self.assertEqual(corpo["count"], 1)
        self.assertNotIn("contato", corpo["results"][0])
        self.assertEqual(corpo["results"][0]["nome_social"], "Dra. Ana")

    def test_retrieve_inclui_contato(self) -> None:
        profissional = Profissional.objects.create(**PAYLOAD_VALIDO)

        response = self.client.get(f"{URL_LISTA}{profissional.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["contato"], "ana@example.com")

    def test_patch_atualiza_campo(self) -> None:
        profissional = Profissional.objects.create(**PAYLOAD_VALIDO)

        response = self.client.patch(
            f"{URL_LISTA}{profissional.id}/", {"profissao": "Psicanalista"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profissional.refresh_from_db()
        self.assertEqual(profissional.profissao, "Psicanalista")

    def test_delete_remove_profissional(self) -> None:
        profissional = Profissional.objects.create(**PAYLOAD_VALIDO)

        response = self.client.delete(f"{URL_LISTA}{profissional.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Profissional.objects.filter(pk=profissional.pk).exists())

    def test_delete_cascateia_consultas_do_profissional(self) -> None:
        profissional = Profissional.objects.create(**PAYLOAD_VALIDO)
        Consulta.objects.create(
            profissional=profissional, data_hora=timezone.now() + timedelta(days=1)
        )

        response = self.client.delete(f"{URL_LISTA}{profissional.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Consulta.objects.count(), 0)

    def test_create_sem_campo_obrigatorio_retorna_400_com_envelope(self) -> None:
        payload = {k: v for k, v in PAYLOAD_VALIDO.items() if k != "nome_social"}

        response = self.client.post(URL_LISTA, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        corpo = response.json()
        self.assertEqual(corpo["code"], "validation_error")
        self.assertIn("nome_social", corpo["errors"])
        self.assertEqual(set(corpo), {"code", "detail", "errors"})

    def test_retrieve_de_id_inexistente_retorna_404_com_envelope(self) -> None:
        response = self.client.get(f"{URL_LISTA}{uuid.uuid4()}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["code"], "not_found")
