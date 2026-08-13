"""Contrato documental da entrega Tech Lead — derivado dos ACs da Fase 10."""

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "docs" / "adr"


class EntregaAdrTests(SimpleTestCase):
    def test_adrs_restantes_existem(self) -> None:
        for nome in (
            "0003-jwt-single-tenant.md",
            "0004-timezone-america-sao-paulo.md",
            "0005-exclusao-e-trilha-financeira.md",
            "0006-django-52-lts.md",
        ):
            with self.subTest(nome=nome):
                self.assertTrue((ADR / nome).is_file())

    def test_adr_auth_cita_jwt_e_single_tenant(self) -> None:
        texto = (ADR / "0003-jwt-single-tenant.md").read_text(encoding="utf-8")
        self.assertIn("JWT", texto)
        self.assertIn("single-tenant", texto.lower())

    def test_adr_timezone_sao_paulo(self) -> None:
        texto = (ADR / "0004-timezone-america-sao-paulo.md").read_text(encoding="utf-8")
        self.assertIn("America/Sao_Paulo", texto)
        self.assertIn("USE_TZ", texto)

    def test_adr_exclusao_protect_409(self) -> None:
        texto = (ADR / "0005-exclusao-e-trilha-financeira.md").read_text(encoding="utf-8")
        self.assertIn("PROTECT", texto)
        self.assertIn("409", texto)

    def test_adr_django_lts(self) -> None:
        texto = (ADR / "0006-django-52-lts.md").read_text(encoding="utf-8")
        self.assertIn("5.2", texto)
        self.assertIn("LTS", texto)
