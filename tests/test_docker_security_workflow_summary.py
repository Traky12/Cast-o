"""Regression guard for shell-safe rendering of Docker security summaries."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "docker-security.yml"


def test_security_summary_uses_a_quoted_heredoc_for_static_markdown() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    start = source.index("      - name: Generar reporte de seguridad\n")
    end = source.index("      - name: Subir artefactos de auditoría\n", start)
    report_step = source[start:end]

    # The Markdown contains backtick code spans. An unquoted heredoc executes
    # those backticks as shell command substitutions instead of writing them.
    assert "cat <<'EOF'" in report_step
    assert "<<EOF" not in report_step
    assert "`make docker-harden`" in report_step
    assert "`docker image inspect IMAGE:TAG`" in report_step


def test_security_summary_dynamic_fields_are_passed_as_environment_values() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    start = source.index("      - name: Generar reporte de seguridad\n")
    end = source.index("      - name: Subir artefactos de auditoría\n", start)
    report_step = source[start:end]

    for name in (
        "WORKFLOW_REF",
        "WORKFLOW_EVENT",
        "WORKFLOW_SHA",
        "AUDIT_STATUS",
        "AUDIT_EXIT_CODE",
        "COMPOSE_STATUS",
        "COMPOSE_VALID",
        "IMAGES_HAVE_LATEST",
        "DOCKERFILES_SCANNED",
    ):
        assert f"{name}:" in report_step

    assert 'printf -- \'- **Rama**: %s\\n\' "$WORKFLOW_REF"' in report_step
    assert 'printf -- \'- **Commit**: `%s`\\n\\n\' "$WORKFLOW_SHA"' in report_step
