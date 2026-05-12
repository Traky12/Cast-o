from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / "scripts" / "ai" / "robotics"))
import robot_controller  # noqa: E402


def test_mock_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CASTUO_ROBOT_SERIAL_MOCK", "1")
    c = robot_controller.RobotController(port="COM99")
    assert c.connect()
    r = c.send_command("MOVE X 1")
    assert r.get("status") == "ok"
    c.disconnect()


def test_save_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CASTUO_ROBOT_SERIAL_MOCK", "1")
    c = robot_controller.RobotController()
    c.connect()
    c.send_command("PING")
    p = tmp_path / "l.json"
    c.save_logs(str(p))
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, list)
