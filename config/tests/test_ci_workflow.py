"""Contrato do workflow GitHub Actions — derivado dos ACs da Fase 7, não do YAML."""

import subprocess
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
GITLEAKS = ROOT / ".gitleaks.toml"
GITIGNORE = ROOT / ".gitignore"


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


class CiWorkflowPostgresTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = WORKFLOW.read_text(encoding="utf-8")

    def test_service_container_e_postgres_16(self) -> None:
        self.assertRegex(self.texto, r"image:\s*postgres:16")

    def test_job_test_usa_database_url_e_suite_django(self) -> None:
        self.assertIn("test:", self.texto)
        self.assertIn("DATABASE_URL:", self.texto)
        self.assertIn("postgres://", self.texto)
        self.assertIn("manage.py test", self.texto)


class CiWorkflowSecurityTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = WORKFLOW.read_text(encoding="utf-8")
        cls.allowlist = GITLEAKS.read_text(encoding="utf-8")

    def test_check_deploy_com_production_e_env_dummy(self) -> None:
        self.assertIn("check --deploy", self.texto)
        self.assertIn("config.settings.production", self.texto)
        self.assertIn("SECRET_KEY: check-deploy-dummy-", self.texto)
        self.assertIn("ALLOWED_HOSTS: example.com", self.texto)

    def test_gitleaks_detect_com_redact(self) -> None:
        self.assertIn("gitleaks detect", self.texto)
        self.assertIn("--redact", self.texto)
        self.assertIn("--config .gitleaks.toml", self.texto)

    def test_allowlist_gitleaks_so_env_example(self) -> None:
        self.assertTrue(GITLEAKS.is_file())
        self.assertIn(r"\.env\.example$", self.allowlist)
        self.assertNotIn(r"\.env$", self.allowlist.replace(r"\.env\.example$", ""))

    def test_pip_audit_falha_em_advisory(self) -> None:
        self.assertIn("pip-audit", self.texto)

    def test_workflow_nao_imprime_secrets(self) -> None:
        self.assertNotRegex(self.texto, r"echo\s+.*\$\{\{\s*secrets\.")
        self.assertNotIn("echo $RENDER_DEPLOY_HOOK", self.texto)

    def test_env_ignorado_e_nao_versionado(self) -> None:
        gitignore = GITIGNORE.read_text(encoding="utf-8")
        self.assertRegex(gitignore, r"(?m)^\.env$")
        listados = subprocess.run(
            ["git", "ls-files", ".env"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(listados.stdout.strip(), "")


class CiWorkflowBuildTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = WORKFLOW.read_text(encoding="utf-8")

    def test_job_build_depende_de_test(self) -> None:
        self.assertIn("build:", self.texto)
        self.assertIn("needs: [test]", self.texto)

    def test_docker_build_com_tag_sha(self) -> None:
        self.assertIn("docker build -t consultas-api:${{ github.sha }} .", self.texto)


class CiWorkflowDeployTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.texto = WORKFLOW.read_text(encoding="utf-8")

    def test_deploy_so_no_workflow_dispatch(self) -> None:
        self.assertIn("deploy:", self.texto)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", self.texto)

    def test_deploy_skip_quando_hook_ausente(self) -> None:
        self.assertIn("RENDER_DEPLOY_HOOK: ${{ secrets.RENDER_DEPLOY_HOOK }}", self.texto)
        self.assertIn('if [ -z "$RENDER_DEPLOY_HOOK" ]', self.texto)
        self.assertIn("exit 0", self.texto)

    def test_sem_smoke_ready_remoto(self) -> None:
        self.assertNotIn("/ready/", self.texto)
        self.assertNotIn("onrender.com", self.texto)
