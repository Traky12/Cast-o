"""
Tests for SABIONDA API endpoints and SIEX schema validation.
Validates:
  - SIEX JSON payloads against the JSON schema
  - pendiente_firma: true in all endpoint responses
  - Endpoint response structure
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pytest
from fastapi.testclient import TestClient

# Adjust path so api/main.py can be imported
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from main import app

client = TestClient(app)

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "config" / "schemas"


# --- Fixtures ---


@pytest.fixture
def siex_schema():
    with open(SCHEMAS_DIR / "siex.schema.json") as f:
        return json.load(f)


@pytest.fixture
def siex_request_body():
    return {
        "explotacion": {
            "rea": "EX123456",
            "titular": "Finca Dehesa Test",
            "nif": "12345678A",
        },
        "parcelas": [
            {
                "sigpac_ref": "10:20:0:0:1:1:1",
                "superficie_ha": 50.0,
                "cultivo": "trigo",
                "tipo_riego": "secano",
                "eco_esquema": True,
            }
        ],
        "tratamientos": [
            {
                "fecha": "2026-03-15",
                "producto": "Clorpirifos 48%",
                "materia_activa": "Clorpirifos",
                "dosis": "2.5 L/ha",
                "parcela_ref": "10:20:0:0:1:1:1",
                "plazo_seguridad_dias": 21,
                "justificacion": "Pulgón cereal",
            }
        ],
    }


@pytest.fixture
def traces_request_body():
    return {
        "explotacion_rega": "ES100600000001",
        "nombre_explotacion": "Finca Dehesa Test",
        "animales": {"especie": "porcino", "raza": "Ibérico", "cantidad": 200},
        "destino_pais": "PT",
        "destino_explotacion": "PT500100000042",
    }


@pytest.fixture
def pac_request_body():
    return {
        "nif": "12345678A",
        "nombre": "Finca Dehesa Test",
        "rea": "EX123456",
        "campana": "2026",
        "parcelas": [
            {
                "sigpac_ref": "10:20:0:0:1:1:1",
                "superficie_ha": 50.0,
                "cultivo": "trigo",
                "tipo_riego": "secano",
                "eco_esquema": True,
            }
        ],
        "eco_esquemas": [
            {
                "codigo": "ECO1",
                "descripcion": "Rotación cultivos con leguminosas",
                "parcelas_aplicadas": ["10:20:0:0:1:1:1"],
            }
        ],
    }


# --- SIEX Schema Validation Tests ---


class TestSIEXSchemaValidation:
    """Validate real SIEX JSON payloads against the official schema."""

    def test_valid_siex_payload_passes_schema(self, siex_schema):
        """A complete SIEX payload must validate against the schema."""
        payload = {
            "explotacion": {
                "rea": "EX123456",
                "titular": "Finca Dehesa Test",
                "nif": "12345678A",
                "comunidad_autonoma": "Extremadura",
            },
            "parcelas": [
                {
                    "sigpac_ref": "10:20:0:0:1:1:1",
                    "superficie_ha": 50.0,
                    "cultivo": "trigo",
                    "tipo_riego": "secano",
                    "eco_esquema": True,
                }
            ],
            "tratamientos": [
                {
                    "fecha": "2026-03-15",
                    "producto": "Clorpirifos 48%",
                    "dosis": "2.5 L/ha",
                    "parcela_ref": "10:20:0:0:1:1:1",
                    "plazo_seguridad_dias": 21,
                }
            ],
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            "estado_cumplimiento": {
                "pac_compliant": True,
                "siex_interoperable": True,
                "porcentaje_cumplimiento": 98.5,
            },
            "firma": {
                "pendiente_firma": True,
                "aviso": "Documento generado para REVISIÓN y FIRMA del productor",
            },
        }
        jsonschema.validate(instance=payload, schema=siex_schema)

    def test_siex_missing_explotacion_fails(self, siex_schema):
        """SIEX payload without explotacion must fail validation."""
        payload = {
            "parcelas": [],
            "tratamientos": [],
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=payload, schema=siex_schema)

    def test_siex_missing_parcelas_fails(self, siex_schema):
        """SIEX payload without parcelas must fail validation."""
        payload = {
            "explotacion": {"rea": "EX123456", "titular": "Test", "nif": "12345678A"},
            "tratamientos": [],
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=payload, schema=siex_schema)

    def test_siex_firma_pendiente_in_schema(self, siex_schema):
        """The SIEX schema must define pendiente_firma with default true."""
        firma_props = siex_schema["properties"]["firma"]["properties"]
        assert "pendiente_firma" in firma_props
        assert firma_props["pendiente_firma"]["default"] is True

    def test_siex_invalid_riego_type_fails(self, siex_schema):
        """SIEX parcela with invalid tipo_riego must fail validation."""
        payload = {
            "explotacion": {"rea": "EX123456", "titular": "Test", "nif": "12345678A"},
            "parcelas": [
                {
                    "sigpac_ref": "10:20:0:0:1:1:1",
                    "superficie_ha": 50.0,
                    "cultivo": "trigo",
                    "tipo_riego": "invalido",
                }
            ],
            "tratamientos": [],
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=payload, schema=siex_schema)


# --- Endpoint Tests ---


class TestSIEXEndpoint:
    """Test SIEX cuaderno-campo endpoint responses."""

    def test_siex_returns_200(self, siex_request_body):
        response = client.post("/api/v1/siex/cuaderno-campo", json=siex_request_body)
        assert response.status_code == 200

    def test_siex_pendiente_firma_true(self, siex_request_body):
        """SIEX response payload must have pendiente_firma: true."""
        response = client.post("/api/v1/siex/cuaderno-campo", json=siex_request_body)
        data = response.json()
        assert data["payload"]["firma"]["pendiente_firma"] is True

    def test_siex_aviso_legal(self, siex_request_body):
        """SIEX response must include the mandatory legal notice."""
        response = client.post("/api/v1/siex/cuaderno-campo", json=siex_request_body)
        data = response.json()
        assert data["aviso"] == "Documento generado para REVISIÓN y FIRMA del productor"
        assert (
            data["payload"]["firma"]["aviso"]
            == "Documento generado para REVISIÓN y FIRMA del productor"
        )

    def test_siex_payload_matches_schema(self, siex_request_body, siex_schema):
        """The SIEX endpoint payload must validate against the SIEX schema."""
        response = client.post("/api/v1/siex/cuaderno-campo", json=siex_request_body)
        payload = response.json()["payload"]
        jsonschema.validate(instance=payload, schema=siex_schema)

    def test_siex_estado_cumplimiento(self, siex_request_body):
        """SIEX response must include compliance status."""
        response = client.post("/api/v1/siex/cuaderno-campo", json=siex_request_body)
        estado = response.json()["payload"]["estado_cumplimiento"]
        assert estado["pac_compliant"] is True
        assert estado["siex_interoperable"] is True


class TestTRACESEndpoint:
    """Test TRACES certificate endpoint responses."""

    def test_traces_returns_200(self, traces_request_body):
        response = client.post("/api/v1/traces/certificado", json=traces_request_body)
        assert response.status_code == 200

    def test_traces_pendiente_firma_true(self, traces_request_body):
        """TRACES response payload must have pendiente_firma: true."""
        response = client.post("/api/v1/traces/certificado", json=traces_request_body)
        data = response.json()
        assert data["payload"]["firma"]["pendiente_firma"] is True

    def test_traces_aviso_legal(self, traces_request_body):
        """TRACES response must include the mandatory legal notice."""
        response = client.post("/api/v1/traces/certificado", json=traces_request_body)
        data = response.json()
        assert data["aviso"] == "Documento generado para REVISIÓN y FIRMA del productor"


class TestPACEndpoint:
    """Test PAC eco-esquema endpoint responses."""

    def test_pac_returns_200(self, pac_request_body):
        response = client.post("/api/v1/pac/eco-esquema", json=pac_request_body)
        assert response.status_code == 200

    def test_pac_pendiente_firma_true(self, pac_request_body):
        """PAC response payload must have pendiente_firma: true."""
        response = client.post("/api/v1/pac/eco-esquema", json=pac_request_body)
        data = response.json()
        assert data["payload"]["firma"]["pendiente_firma"] is True

    def test_pac_eco_cumplimiento(self, pac_request_body):
        """PAC with eco_esquema parcelas should show compliance."""
        response = client.post("/api/v1/pac/eco-esquema", json=pac_request_body)
        data = response.json()
        assert data["payload"]["estado_cumplimiento"]["pac_compliant"] is True
        assert data["payload"]["estado_cumplimiento"]["porcentaje_global"] == 100.0


class TestHealthEndpoint:
    def test_health_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["agent"] == "SABIONDA"
