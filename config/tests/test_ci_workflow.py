"""Contrato do workflow GitHub Actions — derivado dos ACs da Fase 7, não do YAML."""

from pathlib import Path

from django.test import SimpleTestCase

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


class CiWorkflowLintTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = WORKFLOW.read_text(encoding="utf-8")

    def test_arquivo_do_workflow_existe(self) -> None:
        self.assertTrue(WORKFLOW.is_file())

    def test_dispara_em_push_e_pull_request_na_main(self) -> None:
        self.assertIn("push:", self.texto)
        self.assertIn("pull_request:", self.texto)
        self.assertRegex(self.texto, r"branches:\s*\n\s*-\s*main")

    def test_job_lint_falha_com_ruff_check_e_format(self) -> None:
        self.assertIn("lint:", self.texto)
        self.assertIn("ruff check .", self.texto)
        self.assertIn("ruff format --check .", self.texto)
