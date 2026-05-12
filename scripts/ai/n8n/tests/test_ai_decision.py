from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / "scripts" / "ai" / "n8n"))
import ai_decision  # noqa: E402


def test_decide_numpy_high_triggers_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CASTUO_N8N_ALERT_THRESHOLD", "0.5")
    alert, score = ai_decision.decide_numpy({"humedad": 0.9, "temperatura": 0.9, "ph": 0.9, "ec": 0.9, "co2": 0.9})
    assert alert is True
    assert score > 0.5


def test_decide_numpy_low(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CASTUO_N8N_ALERT_THRESHOLD", "0.99")
    alert, score = ai_decision.decide_numpy({"humedad": 0.1, "temperatura": 0.1})
    assert alert is False
