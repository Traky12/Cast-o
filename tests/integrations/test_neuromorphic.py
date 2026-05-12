import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.trl6

os.environ.setdefault("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "test-bearer-secret")
os.environ.setdefault("TRL_LEVEL", "TRL-6-staging")


def test_memristor_stdp():
    from backend.integrations.robotics.neuromorphic_edge import MemristorSynapse

    synapse = MemristorSynapse()
    w0 = synapse.weight
    synapse.update_stdp(True, True, 5.0)
    assert synapse.weight > w0
    assert synapse.eco_alloy


def test_hydro_snn():
    from backend.integrations.robotics.neuromorphic_edge import HydroponicsSNN

    snn = HydroponicsSNN(neurons=32)
    decision = snn.process_sensors({"humedad": 40.0, "ph": 6.2, "ec": 1.8})
    assert 0 <= decision["riego_ml"] <= 1000
    assert decision["memristor_power_uW"] < 1e-3


def test_neuro_infer_endpoint():
    from backend.integrations.robotics.lab_stub_app import app

    token = os.environ.get("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "test-bearer-secret")
    c = TestClient(app)
    r = c.post(
        "/api/robotics/lab/neuromorphic/hydroponics/infer",
        json={"humedad": 42.5, "ph": 6.2, "ec": 1.8},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "chain_seal" in data
    assert data["eco_alloy"]
    assert 0 <= data["riego_ml"] <= 1000
    tr = data["inference"].get("traceability") or {}
    assert tr.get("no_medical_advice") is True
    assert tr.get("no_regulatory_compliance_claim") is True
    assert tr.get("processing_purpose") == "agronomic_research_TRL6"
    assert tr.get("validation_checks")
    td = tr.get("tier_disclosure") or {}
    assert td.get("neuromorphic_simulation") == "TRL-4-lab-sim"
    assert td.get("integration_gate") == "TRL-6-staging"
    assert tr.get("model_tier") == "TRL-6-staging"


def test_neuro_infer_endpoint_accepts_target_terpene():
    from backend.integrations.robotics.lab_stub_app import app

    token = os.environ.get("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "test-bearer-secret")
    c = TestClient(app)
    r = c.post(
        "/api/robotics/lab/neuromorphic/hydroponics/infer",
        json={"humedad": 60, "ph": 5.9, "ec": 1.3, "luz_umol": 950, "target_terpene": "mirceno"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["inference"]["target_terpene"] == "mirceno"
    assert data["inference"]["traceability"]["target_terpene_requested"] == "mirceno"


def test_neuro_infer_endpoint_accepts_uvb_ratio():
    from backend.integrations.robotics.lab_stub_app import app

    token = os.environ.get("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "test-bearer-secret")
    c = TestClient(app)
    r = c.post(
        "/api/robotics/lab/neuromorphic/hydroponics/infer",
        json={"humedad": 55, "ph": 6.0, "ec": 1.2, "luz_umol": 1000, "uvb_ratio": 0.05},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["inference"]["uvb_ratio"] == 0.05


def test_signal_log_neuro_when_env(monkeypatch):
    monkeypatch.setenv("CASTUO_ROBOTICS_LAB", "1")
    monkeypatch.setenv("CASTUO_NEUROMORPHIC_LAB", "1")
    from backend.integrations.robotics.signal_manager import SignalManager

    m = SignalManager("N1")
    snap = m.snapshot_from_pcm(
        "test",
        100.0,
        b"\x00\x01",
        humedad=50.0,
        ph=6.0,
        ec=1.2,
    )
    m.log_snapshot(snap)
    assert m.history()
    assert "neuromorphic_inference" in m.history()[0]["metadata"]
