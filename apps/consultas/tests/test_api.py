import uuid
from datetime import UTC, datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.consultas.models import Consulta
from apps.profissionais.models import Profissional

URL_LISTA = "/api/v1/consultas/"


class ConsultaApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="operadora", password="senha-de-teste"
        )
        self.client.force_authenticate(user=self.user)
        self.profissional = Profissional.objects.create(
            nome_social="Dra. Ana",
            profissao="Psicóloga",
            endereco="Rua das Flores, 100 - São Paulo/SP",
            contato="ana@example.com",
        )
        self.slot = (timezone.now() + timedelta(days=1)).isoformat()

    def _payload(self, **overrides: object) -> dict:
        return {"profissional": str(self.profissional.id), "data_hora": self.slot, **overrides}

    def test_create_retorna_201(self) -> None:
        response = self.client.post(URL_LISTA, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["status"], "agendada")
        self.assertEqual(Consulta.objects.count(), 1)

    def test_slot_ocupado_retorna_409_consulta_conflito(self) -> None:
        self.client.post(URL_LISTA, self._payload(), format="json")

        response = self.client.post(URL_LISTA, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        corpo = response.json()
        self.assertEqual(corpo["code"], "consulta_conflito")
        self.assertEqual(corpo["errors"], {})
        self.assertEqual(Consulta.objects.count(), 1)

    def test_cancelar_libera_o_slot(self) -> None:
        primeira = self.client.post(URL_LISTA, self._payload(), format="json").json()

        cancelamento = self.client.patch(
            f"{URL_LISTA}{primeira['id']}/", {"status": "cancelada"}, format="json"
        )
        recriada = self.client.post(URL_LISTA, self._payload(), format="json")

        self.assertEqual(cancelamento.status_code, status.HTTP_200_OK)
        self.assertEqual(cancelamento.json()["status"], "cancelada")
        self.assertEqual(recriada.status_code, status.HTTP_201_CREATED)

    def test_data_hora_no_passado_retorna_400(self) -> None:
        passado = (timezone.now() - timedelta(hours=1)).isoformat()

        response = self.client.post(URL_LISTA, self._payload(data_hora=passado), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        corpo = response.json()
        self.assertEqual(corpo["code"], "validation_error")
        self.assertIn("data_hora", corpo["errors"])

    def test_profissional_inexistente_retorna_400_e_nao_500(self) -> None:
        response = self.client.post(
            URL_LISTA, self._payload(profissional=str(uuid.uuid4())), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profissional", response.json()["errors"])

    def test_retrieve_de_id_inexistente_retorna_404(self) -> None:
        response = self.client.get(f"{URL_LISTA}{uuid.uuid4()}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["code"], "not_found")

    def test_delete_remove_consulta(self) -> None:
        consulta = Consulta.objects.create(
            profissional=self.profissional, data_hora=timezone.now() + timedelta(days=2)
        )

        response = self.client.delete(f"{URL_LISTA}{consulta.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Consulta.objects.filter(pk=consulta.pk).exists())

    def test_data_hora_e_devolvida_no_fuso_de_sao_paulo(self) -> None:
        instante = datetime(2099, 1, 15, 15, 0, tzinfo=UTC)

        response = self.client.post(
            URL_LISTA, self._payload(data_hora=instante.isoformat()), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        devolvido = response.json()["data_hora"]
        self.assertTrue(devolvido.endswith("-03:00"), devolvido)
        self.assertEqual(devolvido[:16], "2099-01-15T12:00")
