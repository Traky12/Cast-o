from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_faq_json_structure() -> None:
    path = DATA_DIR / "educanova_faq.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list), "El dataset debe ser una lista"
    assert len(data) > 0, "El dataset no puede estar vacío"
    for item in data:
        assert "question" in item, "Cada entrada debe tener 'question'"
        assert "answer" in item, "Cada entrada debe tener 'answer'"
        assert isinstance(item["question"], str)
        assert isinstance(item["answer"], str)
