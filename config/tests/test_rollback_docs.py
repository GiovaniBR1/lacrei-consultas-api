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
