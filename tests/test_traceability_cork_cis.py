from __future__ import annotations

import importlib.util
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.traceability.cis_calculator import calculate_cis_impact
from backend.traceability import cork_store

_root = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "_tg", _root / "backend" / "routers" / "traceability_governance.py"
)
_tg = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(_tg)

_app = FastAPI()
_app.include_router(_tg.router)
client = TestClient(_app)

_H128 = "0x" + "a" * 128


@pytest.fixture(autouse=True)
def clear_cork_store(monkeypatch):
    with cork_store._lock:
        cork_store._events.clear()
    yield
    with cork_store._lock:
        cork_store._events.clear()


def test_calculate_cis_impact():
    assert calculate_cis_impact(100, 0) == 1
    assert calculate_cis_impact(0, 1) == 1
    assert calculate_cis_impact(250, 2) == int(2.5 + 2) == 4


def test_calculate_cis_negative_raises():
    with pytest.raises(ValueError):
        calculate_cis_impact(-1, 0)


def test_post_cork_event_gaichain_alias():
    tid = str(uuid4())
    r = client.post(
        "/traceability/cork-extraction-events",
        json={
            "tree_uuid": tid,
            "operator_id": "eIDAS:ES:SUP-001",
            "laser_energy_mj": 8.5,
            "cambium_integrity_score": 0.995,
            "pqc_signature": "MLDSA65_HEX_" + 64 * "1",
            "gaichain_hash": _H128,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["tree_uuid"] == tid
    assert "event_id" in data
    assert data["cambium_integrity_score"] == 0.995


def test_cork_cambium_too_low_422():
    r = client.post(
        "/traceability/cork-extraction-events",
        json={
            "tree_uuid": str(uuid4()),
            "operator_id": "x",
            "laser_energy_mj": 1,
            "cambium_integrity_score": 0.5,
            "pqc_signature": "sig",
            "gaia_chain_hash": _H128,
        },
    )
    assert r.status_code == 422


def test_cis_api():
    r = client.post(
        "/traceability/cis/calculate",
        json={"water_saved_liters": 500, "carbon_avoided_kg": 3.2, "edge_node_id": "EDGE-EXT-01"},
    )
    assert r.status_code == 200
    assert r.json()["cis_credits"] == int(5 + 3.2) == 8
