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


class EntregaDecisionLogTests(SimpleTestCase):
    LOG = ROOT / "docs" / "decision-log.md"

    def test_decision_log_tem_pelo_menos_cinco_datas(self) -> None:
        self.assertTrue(self.LOG.is_file())
        texto = self.LOG.read_text(encoding="utf-8")
        datas = texto.count("2026-")
        self.assertGreaterEqual(datas, 5)


class EntregaChecklistDiagramasTests(SimpleTestCase):
    SEC = ROOT / "docs" / "seguranca.md"
    ARQ = ROOT / "docs" / "arquitetura.md"

    def test_checklist_mistura_feito_e_nao_feito(self) -> None:
        texto = self.SEC.read_text(encoding="utf-8")
        self.assertIn("✅", texto)
        self.assertIn("❌", texto)

    def test_checklist_cita_postgres_compartilhado(self) -> None:
        texto = self.SEC.read_text(encoding="utf-8")
        self.assertIn("Postgres", texto)
        self.assertIn("compartilhado", texto.lower())

    def test_arquitetura_tem_dois_mermaid(self) -> None:
        texto = self.ARQ.read_text(encoding="utf-8")
        self.assertGreaterEqual(texto.count("```mermaid"), 2)
        self.assertIn("split", texto.lower())
        self.assertIn("webhook", texto.lower())
        self.assertIn("ruff", texto.lower())


class EntregaTechLeadTests(SimpleTestCase):
    DOC = ROOT / "docs" / "entrega-tech-lead.md"
    README = ROOT / "README.md"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = cls.DOC.read_text(encoding="utf-8")
        cls.readme = cls.README.read_text(encoding="utf-8")

    def test_seis_perguntas_do_template(self) -> None:
        for n in range(1, 7):
            with self.subTest(n=n):
                self.assertIn(f"## {n}.", self.texto)
        self.assertIn("LGBTQIAPN+", self.texto)
        self.assertIn("missão", self.texto.lower())

    def test_rascunho_nao_enviar_urls_pendentes(self) -> None:
        self.assertIn("não enviar", self.texto.lower())
        self.assertIn("pendente (AD-003)", self.texto)
        self.assertIn("desenvolvimento.humano@lacreisaude.com.br", self.texto)
        self.assertNotRegex(self.texto, r"https://[a-z0-9-]+\.onrender\.com")

    def test_readme_liga_entrega_decision_log_e_arquitetura(self) -> None:
        self.assertIn("docs/entrega-tech-lead.md", self.readme)
        self.assertIn("docs/decision-log.md", self.readme)
        self.assertIn("docs/arquitetura.md", self.readme)
