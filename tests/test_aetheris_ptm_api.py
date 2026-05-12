from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.aetheris.ptm_api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_ptm_session():
    r = client.post(
        "/v1/aetheris/ptm/session",
        json={
            "source_node_id": "A",
            "target_node_id": "B",
            "energy_kwh": 10.0,
            "laser_frequency_thz": 194.0,
        },
    )
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "confirmed"
    assert d["credits_transferred_kwh_equiv"] == 8.5
    assert len(d["tx_hash"]) == 66
