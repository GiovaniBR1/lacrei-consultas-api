from django.test import TestCase

from apps.profissionais.models import Profissional


class ProfissionalModelTests(TestCase):
    def test_str_usa_nome_social_e_profissao(self) -> None:
        profissional = Profissional(nome_social="Dra. Ana", profissao="Psicóloga")

        self.assertEqual(str(profissional), "Dra. Ana (Psicóloga)")

    def test_str_nao_expoe_contato(self) -> None:
        profissional = Profissional(
            nome_social="Dra. Ana", profissao="Psicóloga", contato="ana@example.com"
        )

        self.assertNotIn("ana@example.com", str(profissional))
