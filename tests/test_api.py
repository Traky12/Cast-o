"""
Tests for SABIONDA API endpoints and SIEX schema validation.
Validates:
  - SIEX JSON payloads against the JSON schema
  - pendiente_firma: true in all endpoint responses
  - Endpoint response structure
  - Schema compliance for all document endpoints
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
def traces_schema():
    with open(SCHEMAS_DIR / "traces.schema.json") as f:
        return json.load(f)


@pytest.fixture
def pac_schema():
    with open(SCHEMAS_DIR / "pac.schema.json") as f:
        return json.load(f)


@pytest.fixture
def regepa_schema():
    with open(SCHEMAS_DIR / "regepa.schema.json") as f:
        return json.load(f)


@pytest.fixture
def sigpac_schema():
    with open(SCHEMAS_DIR / "sigpac.schema.json") as f:
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
        "direccion_explotacion": "Calle Test 1, Badajoz",
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
                "uso": "tierra_arable",
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


@pytest.fixture
def regepa_request_body():
    return {
        "explotacion_rega": "ES100600000001",
        "tipo_explotacion": "produccion",
        "clasificacion_zootecnica": "porcino ibérico extensivo",
        "capacidad_maxima": 500,
        "sistema_explotacion": "extensivo",
        "titular_nif": "12345678A",
        "titular_nombre": "Finca Dehesa Test",
        "titular_comunidad": "Extremadura",
        "especies": [
            {
                "especie": "porcino",
                "raza": "Ibérico",
                "censo": 200,
                "orientacion_productiva": "carne",
            }
        ],
        "grasp_compliant": True,
    }


@pytest.fixture
def sigpac_request_body():
    return {
        "titular_nombre": "Finca Dehesa Test",
        "titular_nif": "12345678A",
        "parcelas": [
            {
                "provincia": 10,
                "municipio": 20,
                "poligono": 1,
                "parcela": 1,
                "recinto": 1,
                "uso_sigpac": "TA",
                "superficie_ha": 50.0,
                "coeficiente_regadio": 0.0,
                "pendiente_media_pct": 2.5,
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

    def test_traces_payload_matches_schema(self, traces_request_body, traces_schema):
        """The TRACES endpoint payload must validate against the TRACES schema."""
        response = client.post("/api/v1/traces/certificado", json=traces_request_body)
        payload = response.json()["payload"]
        jsonschema.validate(instance=payload, schema=traces_schema)

    def test_traces_certificado_numero_present(self, traces_request_body):
        """TRACES response must include a generated certificate number."""
        response = client.post("/api/v1/traces/certificado", json=traces_request_body)
        data = response.json()
        assert "numero" in data["payload"]["certificado"]
        assert data["payload"]["certificado"]["numero"].startswith("TRACES-ES-")


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

    def test_pac_payload_matches_schema(self, pac_request_body, pac_schema):
        """The PAC endpoint payload must validate against the PAC schema."""
        response = client.post("/api/v1/pac/eco-esquema", json=pac_request_body)
        payload = response.json()["payload"]
        jsonschema.validate(instance=payload, schema=pac_schema)

    @pytest.mark.parametrize("uso", ["cultivo_permanente", "pasto_permanente", "barbecho", "forestal"])
    def test_pac_uso_values_accepted(self, pac_request_body, pac_schema, uso):
        """PAC parcelas with any valid PAC uso value must produce schema-compliant payloads."""
        body = dict(pac_request_body)
        body["parcelas"] = [{**body["parcelas"][0], "uso": uso}]
        response = client.post("/api/v1/pac/eco-esquema", json=body)
        assert response.status_code == 200
        jsonschema.validate(instance=response.json()["payload"], schema=pac_schema)


class TestREGEPAEndpoint:
    """Test REGEPA explotacion endpoint responses."""

    def test_regepa_returns_200(self, regepa_request_body):
        response = client.post("/api/v1/regepa/explotacion", json=regepa_request_body)
        assert response.status_code == 200

    def test_regepa_pendiente_firma_true(self, regepa_request_body):
        """REGEPA response payload must have pendiente_firma: true."""
        response = client.post("/api/v1/regepa/explotacion", json=regepa_request_body)
        data = response.json()
        assert data["payload"]["firma"]["pendiente_firma"] is True

    def test_regepa_aviso_legal(self, regepa_request_body):
        """REGEPA response must include the mandatory legal notice."""
        response = client.post("/api/v1/regepa/explotacion", json=regepa_request_body)
        data = response.json()
        assert data["aviso"] == "Documento generado para REVISIÓN y FIRMA del productor"

    def test_regepa_payload_matches_schema(self, regepa_request_body, regepa_schema):
        """The REGEPA endpoint payload must validate against the REGEPA schema."""
        response = client.post("/api/v1/regepa/explotacion", json=regepa_request_body)
        payload = response.json()["payload"]
        jsonschema.validate(instance=payload, schema=regepa_schema)

    def test_regepa_estado_cumplimiento(self, regepa_request_body):
        """REGEPA response must include compliance status."""
        response = client.post("/api/v1/regepa/explotacion", json=regepa_request_body)
        estado = response.json()["payload"]["estado_cumplimiento"]
        assert estado["regepa_compliant"] is True
        assert estado["rd_285_2023"] is True


class TestSIGPACEndpoint:
    """Test SIGPAC parcelas endpoint responses."""

    def test_sigpac_returns_200(self, sigpac_request_body):
        response = client.post("/api/v1/sigpac/parcelas", json=sigpac_request_body)
        assert response.status_code == 200

    def test_sigpac_pendiente_firma_true(self, sigpac_request_body):
        """SIGPAC response payload must have pendiente_firma: true."""
        response = client.post("/api/v1/sigpac/parcelas", json=sigpac_request_body)
        data = response.json()
        assert data["payload"]["firma"]["pendiente_firma"] is True

    def test_sigpac_aviso_legal(self, sigpac_request_body):
        """SIGPAC response must include the mandatory legal notice."""
        response = client.post("/api/v1/sigpac/parcelas", json=sigpac_request_body)
        data = response.json()
        assert data["aviso"] == "Documento generado para REVISIÓN y FIRMA del productor"

    def test_sigpac_payload_matches_schema(self, sigpac_request_body, sigpac_schema):
        """The SIGPAC endpoint payload must validate against the SIGPAC schema."""
        response = client.post("/api/v1/sigpac/parcelas", json=sigpac_request_body)
        payload = response.json()["payload"]
        jsonschema.validate(instance=payload, schema=sigpac_schema)

    def test_sigpac_titular_key(self, sigpac_request_body):
        """SIGPAC response explotacion must use 'titular' key."""
        response = client.post("/api/v1/sigpac/parcelas", json=sigpac_request_body)
        data = response.json()
        assert "titular" in data["payload"]["explotacion"]
        assert data["payload"]["explotacion"]["titular"] == "Finca Dehesa Test"


class TestHealthEndpoint:
    def test_health_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["agent"] == "SABIONDA"


class TestClaudeIntegrationEndpoints:
    def test_claude_tools_catalog_available(self):
        response = client.get("/api/v1/claude/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)
        assert any(t["name"] == "generate_siex_cuaderno" for t in data["tools"])

    def test_claude_context_available(self):
        response = client.get("/api/v1/claude/context")
        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert "capabilities" in data
        assert "system_prompt" in data

    def test_claude_execute_siex(self, siex_request_body):
        response = client.post(
            "/api/v1/claude/execute/generate_siex_cuaderno",
            json={"payload": siex_request_body},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "ok"
        assert data["resultado"]["tipo_documento"] == "SIEX Cuaderno Campo Digital"

    def test_claude_execute_invalid_tool(self):
        response = client.post(
            "/api/v1/claude/execute/tool_inexistente",
            json={"payload": {}},
        )
        assert response.status_code == 400


class TestIoTEndpoints:
    def test_iot_telemetry_ingest_returns_accepted(self):
        body = {
            "sensor_id": "iot-test-001",
            "temperature_c": 23.1,
            "humidity_pct": 61.2,
            "source": "pytest",
        }
        response = client.post("/api/v1/iot/telemetry", json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "accepted"
        assert data["sensor_id"] == "iot-test-001"
        assert data["traces_status"] in {"disabled", "queued"}

    def test_iot_telemetry_latest_returns_stored_event(self):
        body = {
            "sensor_id": "iot-test-002",
            "temperature_c": 24.8,
            "humidity_pct": 59.0,
        }
        post_response = client.post("/api/v1/iot/telemetry", json=body)
        assert post_response.status_code == 200

        get_response = client.get("/api/v1/iot/telemetry/iot-test-002/latest")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["sensor_id"] == "iot-test-002"
        assert data["readings"]["temperature_c"] == 24.8

    def test_iot_telemetry_latest_404_when_missing(self):
        response = client.get("/api/v1/iot/telemetry/iot-unknown/latest")
        assert response.status_code == 404
