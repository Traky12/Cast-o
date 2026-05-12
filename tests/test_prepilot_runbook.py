from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_prepilot_script_exists_and_is_bash() -> None:
    script_path = ROOT / "scripts" / "runbook-prepilot.sh"
    assert script_path.exists(), "Debe existir el script ejecutable del runbook pre-pilot"

    content = script_path.read_text(encoding="utf-8")
    assert content.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in content


def test_prepilot_script_covers_core_checks() -> None:
    script = (ROOT / "scripts" / "runbook-prepilot.sh").read_text(encoding="utf-8")

    assert "start_all_services.sh" in script
    assert "verify_operational_stack.sh" in script
    assert "docker ps" in script
    assert "/health" in script
    assert "mosquitto_pub" in script
    assert "mosquitto_sub" in script
    assert "redis-cli ping" in script
    assert "https://api.castuo-system.cloud/health" in script
    assert "/api/dashboards/db" in script
    assert "SHOW DATABASES" in script
    assert "SHOW TABLES" in script


def test_prepilot_runbook_doc_exists_with_go_no_go() -> None:
    doc_path = ROOT / "docs" / "ops" / "RUNBOOK-PRE-PILOT-INVERNADERO.md"
    assert doc_path.exists(), "Debe existir un runbook documentado para pre-pilot"

    doc = doc_path.read_text(encoding="utf-8")
    assert "Go/No-Go" in doc
    assert "Evidencias" in doc
    assert "scripts/runbook-prepilot.sh" in doc
    assert "connect_first_greenhouse.sh" in doc


def test_makefile_has_prepilot_target() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "runbook-prepilot" in makefile
    assert "scripts/runbook-prepilot.sh" in makefile


def test_connect_first_greenhouse_script_exists() -> None:
    script_path = ROOT / "scripts" / "connect_first_greenhouse.sh"
    assert script_path.exists(), "Debe existir script guiado para conectar el primer invernadero"

    script = script_path.read_text(encoding="utf-8")
    assert "farm_uid" in script
    assert "mosquitto_pub" in script
    assert "castuo/sensors" in script
