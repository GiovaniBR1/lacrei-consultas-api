"""Contrato documental do deploy Render — derivado dos ACs da Fase 8, não do markdown."""

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs" / "deploy-render.md"


class DeployRenderRunbookTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = RUNBOOK.read_text(encoding="utf-8")

    def test_runbook_existe(self) -> None:
        self.assertTrue(RUNBOOK.is_file())

    def test_passos_postgres_e_dois_web_services(self) -> None:
        self.assertIn("Postgres", self.texto)
        self.assertIn("api-staging", self.texto)
        self.assertIn("api-prod", self.texto)

    def test_env_vars_distintas_por_servico(self) -> None:
        for chave in (
            "SECRET_KEY",
            "DJANGO_SETTINGS_MODULE",
            "DATABASE_URL",
            "CORS_ALLOWED_ORIGINS",
        ):
            with self.subTest(chave=chave):
                self.assertIn(chave, self.texto)

    def test_migrate_no_release(self) -> None:
        self.assertIn("migrate", self.texto)
        self.assertIn("collectstatic", self.texto)

    def test_health_e_smoke_ready_bloqueado(self) -> None:
        self.assertIn("/health/", self.texto)
        self.assertIn("/ready/", self.texto)
        self.assertIn("AD-003", self.texto)

    def test_nao_ha_blueprint_aplicavel_na_raiz(self) -> None:
        self.assertFalse((ROOT / "render.yaml").exists())
        self.assertFalse((ROOT / "render.yml").exists())
