import json
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

import pytest


def run_reconcile(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "reconcile.sh"
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )


def test_reconcile_supports_output_dir_and_summary_json(tmp_path: Path) -> None:
    summary_file = tmp_path / "summary.json"

    result = run_reconcile(
        [
            "--source-branch",
            "HEAD",
            "--target-branch",
            "HEAD",
            "--dry-run",
            "--output-dir",
            str(tmp_path),
            "--summary-json",
            str(summary_file),
        ]
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert summary_file.exists()

    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    assert summary["source_branch"] == "HEAD"
    assert summary["target_branch"] == "HEAD"
    assert summary["dry_run"] is True
    assert summary["drift_detected"] is False

    report_file = Path(summary["report"])
    patch_file = Path(summary["patch_file"])
    assert report_file.exists()
    assert patch_file.exists()


def test_reconcile_rejects_unknown_params() -> None:
    result = run_reconcile(["--unknown-flag"])

    assert result.returncode == 2
    assert "Parametro no reconocido" in result.stderr


def test_drift_detected(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if shutil.which("git") is None:
        pytest.skip("git no esta disponible")

    has_previous = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD~1"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if has_previous.returncode != 0:
        pytest.skip("No hay commit anterior para simular drift real")

    summary_file = tmp_path / "summary.json"
    result = run_reconcile(
        [
            "--source-branch",
            "HEAD",
            "--target-branch",
            "HEAD~1",
            "--dry-run",
            "--output-dir",
            str(tmp_path),
            "--summary-json",
            str(summary_file),
        ]
    )

    assert summary_file.exists(), result.stderr + result.stdout
    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    assert summary["drift_detected"] is True
    assert summary["status"]["code"] == 1
    assert "Drift detectado" in summary["status"]["message"]

    drift_report = tmp_path / "drift_report.log"
    assert drift_report.exists()
