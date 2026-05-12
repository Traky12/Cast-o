"""
End-to-end smoke test for greenhouse + blockchain trazabilidad flow.
Validates: sensor ingest → alert → actuator control → cosecha registration → blockchain proof.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routers.invernadero import CultivoHidroponico, SistemaCultivo
from services.blockchain.evidence_register import EvidenceRegistrar


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def registrar() -> EvidenceRegistrar:
    return EvidenceRegistrar()


def test_e2e_full_harvest_to_blockchain(client: TestClient, registrar: EvidenceRegistrar) -> None:
    """
    Flujo completo:
    1. Abrir lote
    2. Registrar solución nutritiva
    3. Registrar clima
    4. Registrar cosecha (closed-loop) → blockchain registration
    5. Verificar blockchain txid en respuesta
    """
    # Step 1: Open lot
    apertura_payload = {
        "explotacion_rea": "EXP-HETZNER-001",
        "operador_nif": "12345678Z",
        "cultivo": CultivoHidroponico.TOMATE.value,
        "variedad": "Raf",
        "sistema": SistemaCultivo.NFT.value,
        "zona": "modulo-1-panel-solar",
        "superficie_m2": 250.0,
        "fecha_siembra": date.today().isoformat(),
        "semilla_origen": "ISI Sementi Italia",
        "semilla_certificada": True,
        "sustrato": "NFT sin sustrato",
        "eco_certificado": False,
        "sigpac_ref": "5012401TF2345A",
    }
    resp_apertura = client.post("/api/v1/invernadero/lote/apertura", json=apertura_payload)
    assert resp_apertura.status_code == 200, f"Failed to open lot: {resp_apertura.json()}"
    lote_id = resp_apertura.json()["lote_id"]
    assert lote_id.startswith("INVH-")

    # Step 2: Register nutrition
    solucion_payload = {
        "lote_id": lote_id,
        "zona": "modulo-1-panel-solar",
        "cultivo": CultivoHidroponico.TOMATE.value,
        "sistema": SistemaCultivo.NFT.value,
        "ph": 6.0,  # Optimal for tomato
        "ec_ms_cm": 2.5,  # Optimal for tomato
        "temp_solucion_c": 22.0,
        "o2_disuelto_mg_l": 8.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    resp_solucion = client.post("/api/v1/invernadero/solucion-nutritiva", json=solucion_payload)
    assert resp_solucion.status_code == 200
    data = resp_solucion.json()
    assert data["estado"] == "OPTIMO"
    assert len(data["alertas"]) == 0

    # Step 3: Register climate
    clima_payload = {
        "lote_id": lote_id,
        "zona": "modulo-1-panel-solar",
        "cultivo": CultivoHidroponico.TOMATE.value,
        "etapa": "floracion",
        "co2_ppm": 950,  # Optimal
        "vpd_kpa": 0.8,
        "temp_aire_c": 24.0,
        "humedad_relativa_pct": 65.0,
        "dli_mol_m2_dia": 18.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    resp_clima = client.post("/api/v1/invernadero/clima", json=clima_payload)
    assert resp_clima.status_code == 200
    data = resp_clima.json()
    assert data["estado"] == "OPTIMO"

    # Step 4: Register harvest (closed-loop) → blockchain
    cosecha_payload = {
        "lote_id": lote_id,
        "fecha_cosecha": date.today().isoformat(),
        "kg_cosechados": 3500.0,
        "calibre": "Extra",
        "brix": 5.2,
        "destino": "mercado_local",
        "operador_nif": "12345678Z",
        "notas": "Cosecha de cierre sin incidencias",
    }
    resp_cosecha = client.post("/api/v1/invernadero/cosecha", json=cosecha_payload)
    assert resp_cosecha.status_code == 200
    data = resp_cosecha.json()
    assert data["estado"] == "LOTE_CERRADO"
    assert data["accion"] == "cierre_cosecha"

    # Step 5: Verify blockchain registration
    payload = data.get("payload", {})
    assert "blockchain" in payload, "Blockchain field missing in harvest response"
    
    blockchain_info = payload["blockchain"]
    assert blockchain_info.get("registered") is True, "Blockchain registration failed"
    assert "txid" in blockchain_info, "txid missing from blockchain response"
    assert blockchain_info["txid"].startswith(("local-", "0x")), f"Invalid txid format: {blockchain_info['txid']}"
    assert "network" in blockchain_info
    assert "timestamp" in blockchain_info


def test_harvest_blockchain_failure_fallback(client: TestClient) -> None:
    """Verify that harvest works even if blockchain registration fails (graceful degradation)."""
    # Step 1: Open lot
    apertura_payload = {
        "explotacion_rea": "EXP-FALLBACK-001",
        "operador_nif": "87654321A",
        "cultivo": CultivoHidroponico.LECHUGA.value,
        "variedad": "Batavia",
        "sistema": SistemaCultivo.DWC.value,
        "zona": "modulo-2",
        "superficie_m2": 100.0,
        "fecha_siembra": date.today().isoformat(),
        "semilla_origen": "Semillas Fitó",
        "semilla_certificada": True,
        "eco_certificado": True,
    }
    resp = client.post("/api/v1/invernadero/lote/apertura", json=apertura_payload)
    assert resp.status_code == 200, f"Failed to open lot: {resp.json()}"
    lote_id = resp.json()["lote_id"]

    # Step 2: Harvest (blockchain may fail due to network, but endpoint should succeed)
    cosecha_payload = {
        "lote_id": lote_id,
        "fecha_cosecha": date.today().isoformat(),
        "kg_cosechados": 500.0,
        "calibre": "Cat.I",
        "destino": "distribuidor",
        "operador_nif": "87654321A",
    }
    resp_cosecha = client.post("/api/v1/invernadero/cosecha", json=cosecha_payload)
    assert resp_cosecha.status_code == 200  # Success despite potential blockchain failure
    
    payload = resp_cosecha.json().get("payload", {})
    blockchain_info = payload.get("blockchain", {})
    
    # Either success or graceful fallback
    assert "registered" in blockchain_info, "blockchain field should exist"
    # If registered=False, must have fallback explanation
    if not blockchain_info.get("registered"):
        assert "error" in blockchain_info or "fallback" in blockchain_info


def test_sensor_data_triggers_alert_flow(client: TestClient) -> None:
    """Verify sensor ingest → alert generation flow."""
    # Valid data within range
    sensor_payload = {
        "temperatura": 25.0,
        "humedad": 65.0,
        "co2": 950,
        "luz": 500,
        "ph": 6.0,
        "ec": 2.1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    resp = client.post("/api/v1/invernadero/datos-sensores", json=sensor_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert len(data.get("alerts", [])) == 0

    # Out of range → alert
    sensor_payload["ec"] = 3.5  # Above optimal
    resp = client.post("/api/v1/invernadero/datos-sensores", json=sensor_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data.get("alerts", [])) > 0, "Expected alert for EC out of range"


def test_actuator_control_valid_types(client: TestClient) -> None:
    """Verify all 6 actuator types are controllable."""
    valid_types = ["ventilacion", "riego", "iluminacion", "sombra", "nutrientes", "calefaccion"]
    
    for actuador_tipo in valid_types:
        command_payload = {"reason": f"test_{actuador_tipo}"}
        resp = client.post(
            f"/api/v1/invernadero/actuadores/{actuador_tipo}/encender",
            json=command_payload
        )
        assert resp.status_code == 200, f"Actuator {actuador_tipo} control failed"
        data = resp.json()
        assert data["status"] == "ok"
        assert data["tipo"] == actuador_tipo


def test_actuator_control_invalid_type_rejected(client: TestClient) -> None:
    """Verify unsupported actuator types are rejected."""
    command_payload = {"reason": "test_invalid"}
    resp = client.post(
        "/api/v1/invernadero/actuadores/laser/encender",
        json=command_payload
    )
    assert resp.status_code == 400
    assert "no soportado" in resp.json()["detail"].lower() or "unsupported" in resp.json()["detail"].lower()


def test_blockchain_proof_immutable(tmp_path: Path, registrar: EvidenceRegistrar) -> None:
    """
    Verify blockchain proof is stable (same input → same hash).
    This ensures QR codes remain valid across system restarts.
    """
    # Create a temporary file with consistent content
    test_file = tmp_path / "lote_immutability_test"
    test_file.write_bytes(b"INVH-TEST-001-harvest-data")
    
    metadata_1 = {
        "lote_id": "INVH-TEST-001",
        "fecha_cosecha": "2026-04-02",
        "kg_cosechados": 1000,
        "timestamp": "2026-04-02T10:00:00Z",
    }
    
    # Register with same metadata and file
    result_1 = registrar.register_asset(asset_path=str(test_file), metadata=metadata_1)
    hash_1 = result_1["hash"]
    
    # Verify hash can be recomputed (hashes from same file content should be identical)
    import hashlib
    expected_hash = hashlib.sha256(b"INVH-TEST-001-harvest-data").hexdigest()
    assert hash_1 == expected_hash, "Hash calculation is not deterministic"
    
    # Verify blockchain result structure
    assert "hash" in result_1
    assert "txid" in result_1
    assert result_1["txid"].startswith(("local-", "0x")), f"Invalid txid format: {result_1['txid']}"
