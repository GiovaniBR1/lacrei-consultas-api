"""Schema OpenAPI e UI: existem, descrevem auth e podem ser desligados por ambiente."""

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

URL_SCHEMA = "/api/schema/"
URL_DOCS = "/api/docs/"


class SchemaTests(APITestCase):
    def _schema_json(self) -> dict:
        resposta = self.client.get(URL_SCHEMA, {"format": "json"})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        return resposta.json()

    def test_schema_responde_sem_token(self) -> None:
        resposta = self.client.get(URL_SCHEMA)

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_schema_e_openapi_3(self) -> None:
        self.assertTrue(self._schema_json()["openapi"].startswith("3."))

    def test_schema_cobre_rotas_de_dominio_e_de_auth(self) -> None:
        caminhos = self._schema_json()["paths"]

        self.assertIn("/api/v1/profissionais/", caminhos)
        self.assertIn("/api/v1/consultas/", caminhos)
        self.assertIn("/api/v1/auth/token/", caminhos)

    def test_schema_declara_security_scheme_bearer(self) -> None:
        esquemas = self._schema_json()["components"]["securitySchemes"]

        tipos = {nome: dados.get("scheme") for nome, dados in esquemas.items()}
        self.assertIn("bearer", tipos.values(), esquemas)

    def test_listagem_no_schema_e_paginada(self) -> None:
        lista = self._schema_json()["paths"]["/api/v1/profissionais/"]["get"]
        parametros = {p["name"] for p in lista.get("parameters", [])}

        self.assertIn("page", parametros)

    def test_docs_ui_responde_html(self) -> None:
        resposta = self.client.get(URL_DOCS)

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertIn("text/html", resposta["Content-Type"])

    def test_post_de_consulta_documenta_400_401_e_409(self) -> None:
        respostas = self._schema_json()["paths"]["/api/v1/consultas/"]["post"]["responses"]

        for codigo in ("400", "401", "409"):
            self.assertIn(codigo, respostas, respostas.keys())

    def test_exemplo_de_409_traz_o_code_do_conflito(self) -> None:
        respostas = self._schema_json()["paths"]["/api/v1/consultas/"]["post"]["responses"]

        exemplos = respostas["409"]["content"]["application/json"]["examples"]
        valores = [exemplo["value"] for exemplo in exemplos.values()]
        self.assertIn("consulta_conflito", [valor["code"] for valor in valores])

    def test_exemplo_de_401_esta_no_crud_de_profissionais(self) -> None:
        respostas = self._schema_json()["paths"]["/api/v1/profissionais/"]["get"]["responses"]

        exemplos = respostas["401"]["content"]["application/json"]["examples"]
        valores = [exemplo["value"] for exemplo in exemplos.values()]
        self.assertIn("not_authenticated", [valor["code"] for valor in valores])

    @override_settings(SPECTACULAR_ENABLED=False)
    def test_documentacao_desligada_devolve_404(self) -> None:
        for url in (URL_SCHEMA, URL_DOCS):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
