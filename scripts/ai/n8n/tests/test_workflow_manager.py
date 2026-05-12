from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / "scripts" / "ai" / "n8n"))
import workflow_manager  # noqa: E402


def test_validate_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CASTUO_N8N_WORKFLOWS_DIR", str(tmp_path))
    r = workflow_manager.validate_workflow("no_existe")
    assert "error" in r


def test_validate_minimal_workflow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CASTUO_N8N_WORKFLOWS_DIR", str(tmp_path))
    p = tmp_path / "demo.json"
    p.write_text(json.dumps({"nodes": [{"name": "a"}], "connections": {}}), encoding="utf-8")
    r = workflow_manager.validate_workflow("demo")
    assert r.get("status") == "ok"
    assert r.get("nodes") == 1
