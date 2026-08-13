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


class DeployRenderTradeoffTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = RUNBOOK.read_text(encoding="utf-8")

    def test_postgres_compartilhado_entre_staging_e_producao(self) -> None:
        self.assertIn("compartilham o mesmo Postgres free", self.texto)

    def test_expiry_cerca_de_30_dias_e_upgrade(self) -> None:
        self.assertIn("30 dias", self.texto)
        self.assertIn("upgrade", self.texto)

    def test_cold_start_apos_idle(self) -> None:
        self.assertIn("15 min", self.texto)
        self.assertIn("cold start", self.texto.lower())


class DeployAwsBlueprintAdrTests(SimpleTestCase):
    ADR = ROOT / "docs" / "adr" / "0002-render-e-blueprint-aws.md"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = cls.ADR.read_text(encoding="utf-8")

    def test_adr_existe(self) -> None:
        self.assertTrue(self.ADR.is_file())

    def test_blueprint_app_runner_ecr_rds(self) -> None:
        self.assertIn("App Runner", self.texto)
        self.assertIn("ECR", self.texto)
        self.assertIn("RDS", self.texto)

    def test_rds_por_ambiente_sem_provisionar(self) -> None:
        self.assertIn("por ambiente", self.texto)
        self.assertIn("não provisiona", self.texto.lower())

    def test_expiry_postgres_free_e_upgrade(self) -> None:
        self.assertIn("30 dias", self.texto)
        self.assertIn("upgrade", self.texto)


class DeployReadmeSectionTests(SimpleTestCase):
    README = ROOT / "README.md"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = cls.README.read_text(encoding="utf-8")

    def test_secao_por_que_render_e_blueprint_aws(self) -> None:
        self.assertIn("Por que Render + blueprint AWS", self.texto)

    def test_links_runbook_e_adr(self) -> None:
        self.assertIn("docs/deploy-render.md", self.texto)
        self.assertIn("docs/adr/0002-render-e-blueprint-aws.md", self.texto)

    def test_urls_pendentes_sem_host_fabricado(self) -> None:
        self.assertIn("AD-003", self.texto)
        self.assertIn("pendente", self.texto.lower())
        self.assertNotRegex(self.texto, r"https://[a-z0-9-]+\.onrender\.com")
