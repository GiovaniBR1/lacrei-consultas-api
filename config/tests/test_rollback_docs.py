"""Contrato documental do rollback Render — derivado dos ACs da Fase 9."""

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs" / "rollback.md"


class RollbackRunbookTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = RUNBOOK.read_text(encoding="utf-8")

    def test_runbook_existe(self) -> None:
        self.assertTrue(RUNBOOK.is_file())

    def test_redeploy_commit_ou_release_anterior(self) -> None:
        self.assertIn("Rollback", self.texto)
        self.assertIn("api-staging", self.texto)
        self.assertTrue("SHA" in self.texto or "commit" in self.texto.lower())

    def test_exige_sha_ou_deploy_id(self) -> None:
        self.assertIn("SHA", self.texto)
        self.assertIn("deploy id", self.texto.lower())

    def test_latest_proibida_como_unico_id(self) -> None:
        self.assertIn("latest", self.texto)
        self.assertIn("proibida", self.texto.lower())
        self.assertIn("AD-029", self.texto)


class RollbackExpandContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = RUNBOOK.read_text(encoding="utf-8")

    def test_explica_expand_antes_de_contract(self) -> None:
        self.assertIn("Expand", self.texto)
        self.assertIn("Contract", self.texto)

    def test_liga_dominio_md(self) -> None:
        self.assertIn("docs/dominio.md", self.texto)

    def test_rollback_exige_schema_legivel(self) -> None:
        self.assertIn("release anterior", self.texto.lower())
        self.assertIn("schema", self.texto.lower())


class RollbackEvidenceAndSentryTests(SimpleTestCase):
    README = ROOT / "README.md"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = RUNBOOK.read_text(encoding="utf-8")
        cls.readme = cls.README.read_text(encoding="utf-8")

    def test_slot_evidencia_campos_pendentes(self) -> None:
        for campo in ("timestamp", "URL", "SHA before", "SHA after"):
            with self.subTest(campo=campo):
                self.assertIn(campo, self.texto)
        self.assertIn("pendente", self.texto.lower())
        self.assertIn("AD-003", self.texto)

    def test_sem_host_nem_sha_fabricados(self) -> None:
        self.assertNotRegex(self.texto, r"https://[a-z0-9-]+\.onrender\.com")
        self.assertNotRegex(self.texto, r"\b[0-9a-f]{40}\b")

    def test_sentry_opcional_pula_se_dsn_ausente(self) -> None:
        self.assertIn("SENTRY_DSN", self.texto)
        self.assertIn("pule", self.texto.lower())

    def test_readme_aponta_para_rollback(self) -> None:
        self.assertIn("docs/rollback.md", self.readme)
