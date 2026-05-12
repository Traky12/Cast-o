from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_anonymization import anonymize_dataset, anonymize_query

TEST_DATA = [
    {
        "name": "Juan Pérez",
        "email": "juan@example.com",
        "student_id": "12345",
        "question": "¿Cómo accedo al curso?",
        "ip_address": "192.168.1.1",
    }
]


def test_anonymize_query() -> None:
    result = anonymize_query(TEST_DATA[0], salt="testsalt", synthetic_names=False)
    assert result["name"] != TEST_DATA[0]["name"]
    assert result["email"] != TEST_DATA[0]["email"]
    assert "ip_address" not in result
    assert result["question"] == TEST_DATA[0]["question"]


def test_anonymize_dataset(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(TEST_DATA), encoding="utf-8")
    anonymize_dataset(input_file, output_file, salt="x")
    result = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(result) == 1
    assert result[0]["name"] != TEST_DATA[0]["name"]
    assert "ip_address" not in result[0]
