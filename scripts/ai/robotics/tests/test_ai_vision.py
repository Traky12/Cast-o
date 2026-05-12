from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / "scripts" / "ai" / "robotics"))
import ai_vision  # noqa: E402


def test_detect_mock() -> None:
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    d = ai_vision.detect(frame, use_torch=False)
    assert "confidence" in d
    assert "label" in d


def test_detect_torch_tiny(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("torch")
    monkeypatch.delenv("CASTUO_VISION_MOCK", raising=False)
    frame = np.random.randint(0, 255, (24, 24, 3), dtype=np.uint8)
    d = ai_vision.detect(frame, use_torch=True)
    assert d["class_id"] in (0, 1, 2)
