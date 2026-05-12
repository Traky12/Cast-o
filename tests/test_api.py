"""
Tests for SABIONDA API endpoints and SIEX schema validation.
Validates:
  - SIEX JSON payloads against the JSON schema
  - pendiente_firma: true in all endpoint responses
  - Endpoint response structure
  - Schema compliance for all document endpoints
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jsonschema
import jwt
import pytest
from fastapi.testclient import TestClient

# Adjust path so api/main.py can be imported
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from main import app
from routers import skills as skills_router

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

    # ── contrato mínimo chain_status (DPIA-Robotics-2026 §6) ────────────────
    def test_health_chain_status_field_present(self):
        """chain_status debe estar siempre presente sin autenticación."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "chain_status" in data, "Falta campo chain_status (DPIA §6)"

    def test_health_chain_status_valid_values(self):
        """chain_status solo puede ser disabled | ready | misconfigured."""
        response = client.get("/health")
        data = response.json()
        assert data["chain_status"] in {"disabled", "ready", "misconfigured"}

    def test_health_chain_status_disabled_by_default(self, monkeypatch):
        """Sin CASTUO_ROBOTICS_LAB_CHAIN_REGISTER=1 → disabled."""
        monkeypatch.delenv("CASTUO_ROBOTICS_LAB_CHAIN_REGISTER", raising=False)
        import importlib, backend.routes.health as hr
        importlib.reload(hr)
        assert hr._chain_status() == "disabled"

    def test_health_chain_status_misconfigured(self, monkeypatch):
        """Flag activo pero sin vars de cadena → misconfigured."""
        monkeypatch.setenv("CASTUO_ROBOTICS_LAB_CHAIN_REGISTER", "1")
        monkeypatch.delenv("GAIA_CHAIN_RPC", raising=False)
        monkeypatch.delenv("GAIA_CHAIN_AUDIT_CONTRACT", raising=False)
        import importlib, backend.routes.health as hr
        importlib.reload(hr)
        assert hr._chain_status() == "misconfigured"

    def test_health_chain_status_ready(self, monkeypatch):
        """Flag activo + todas las vars presentes → ready."""
        monkeypatch.setenv("CASTUO_ROBOTICS_LAB_CHAIN_REGISTER", "1")
        monkeypatch.setenv("GAIA_CHAIN_RPC", "https://rpc.example.eu")
        monkeypatch.setenv("GAIA_CHAIN_AUDIT_CONTRACT", "0xABC")
        monkeypatch.setenv("GAIA_CHAIN_AUDIT_ABI", "[{}]")
        monkeypatch.setenv("GAIA_CHAIN_PRIVATE_KEY", "0xDEF")
        import importlib, backend.routes.health as hr
        importlib.reload(hr)
        assert hr._chain_status() == "ready"

    def test_health_neuromorphic_lab_field(self):
        """neuromorphic_lab debe estar presente y ser boolean."""
        response = client.get("/health")
        data = response.json()
        assert "neuromorphic_lab" in data
        assert isinstance(data["neuromorphic_lab"], bool)

    def test_health_timestamp_field(self):
        """timestamp debe estar presente y ser ISO 8601."""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        # Debe parsear como datetime ISO sin lanzar excepción
        from datetime import datetime
        datetime.fromisoformat(data["timestamp"])

    def test_health_no_auth_required(self):
        """El endpoint no debe requerir Authorization header."""
        response = client.get("/health")  # sin headers
        assert response.status_code == 200

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

    def test_iot_telemetry_rejects_out_of_range_ph(self):
        body = {
            "sensor_id": "iot-test-003",
            "readings": {"ph": 15.2, "temperature_c": 23.0},
        }
        response = client.post("/api/v1/iot/telemetry", json=body)
        assert response.status_code == 422
        assert "ph" in response.json()["detail"]

    def test_iot_telemetry_rejects_non_numeric_ec(self):
        body = {
            "sensor_id": "iot-test-004",
            "readings": {"ec_ms_cm": "alta", "humidity_pct": 60.0},
        }
        response = client.post("/api/v1/iot/telemetry", json=body)
        assert response.status_code == 422
        assert "ec_ms_cm" in response.json()["detail"]

    def test_iot_telemetry_accepts_valid_vpd(self):
        body = {
            "sensor_id": "iot-test-005",
            "readings": {"vpd_kpa": 1.45, "temperature_c": 22.0},
        }
        response = client.post("/api/v1/iot/telemetry", json=body)
        assert response.status_code == 200
        assert response.json()["estado"] == "accepted"


class TestUserDashboardStatusEndpoint:
    def test_user_status_returns_compact_dashboard_payload(self):
        body = {
            "sensor_id": "caix21-hub-001",
            "source": "niwa-hub",
            "readings": {
                "ph": 5.85,
                "ec": 1.82,
                "temperature_c": 24.2,
                "humidity_pct": 65.0,
                "lux": 18500,
            },
        }
        ingest_response = client.post("/api/v1/iot/telemetry", json=body)
        assert ingest_response.status_code == 200

        status_response = client.get("/api/v1/user/caix21/status")
        assert status_response.status_code == 200
        payload = status_response.json()

        assert payload["tenant_id"] == "caix21"
        assert payload["status"] == "ok"
        assert payload["metrics"]["ph"] == 5.85
        assert payload["metrics"]["ec"] == 1.82
        assert payload["metrics"]["temperature_c"] == 24.2
        assert payload["metrics"]["humidity_pct"] == 65.0
        assert payload["metrics"]["lux"] == 18500
        assert "alerts" in payload
        assert "next_irrigation_at" in payload

    def test_user_status_alias_path_without_api_prefix(self):
        body = {
            "sensor_id": "caix21-hub-002",
            "source": "niwa-hub",
            "readings": {"ph": 5.9, "ec": 1.9, "temperature_c": 24.0},
        }
        ingest_response = client.post("/api/v1/iot/telemetry", json=body)
        assert ingest_response.status_code == 200

        status_response = client.get("/user/caix21/status")
        assert status_response.status_code == 200
        payload = status_response.json()
        assert payload["tenant_id"] == "caix21"


class TestValidarLoteEndpoint:
    def _token(self, secret: str) -> str:
        payload = {
            "sub": "pytest",
            "roles": ["api"],
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()),
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    def test_validar_lote_rechaza_firma_invalida(self, monkeypatch, tmp_path):
        monkeypatch.setenv("JWT_SECRET", "test-secret")
        monkeypatch.setenv("SKILLS_TMP_DIR", str(tmp_path))

        response = client.post(
            "/api/v1/skills/validar_lote",
            json={
                "lote_id": "L-001",
                "metadatos": {"cultivo": "tomate"},
                "firma_digital": "token-invalido",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Firma invalida"

    def test_validar_lote_rechaza_sin_token(self, monkeypatch, tmp_path):
        monkeypatch.setenv("JWT_SECRET", "test-secret")
        monkeypatch.setenv("SKILLS_TMP_DIR", str(tmp_path))

        response = client.post(
            "/api/v1/skills/validar_lote",
            json={
                "lote_id": "L-001B",
                "metadatos": {"cultivo": "cebada"},
                "firma_digital": None,
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Firma invalida"

    def test_validar_lote_ok_con_authorization_bearer(self, monkeypatch, tmp_path):
        secret = "test-secret"
        token = self._token(secret)
        monkeypatch.setenv("JWT_SECRET", secret)
        monkeypatch.setenv("SKILLS_TMP_DIR", str(tmp_path))

        response = client.post(
            "/api/v1/skills/validar_lote",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "lote_id": "L-002B",
                "metadatos": {"cultivo": "olivo", "origen": "EX"},
                "firma_digital": None,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert Path(data["qr_path"]).exists()
        assert Path(data["certificado_path"]).exists()

    def test_validar_lote_ok_genera_qr(self, monkeypatch, tmp_path):
        secret = "test-secret"
        monkeypatch.setenv("JWT_SECRET", secret)
        monkeypatch.setenv("SKILLS_TMP_DIR", str(tmp_path))

        response = client.post(
            "/api/v1/skills/validar_lote",
            json={
                "lote_id": "L-002",
                "metadatos": {"cultivo": "lechuga", "origen": "EXT"},
                "firma_digital": self._token(secret),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert data["tx_hash"].startswith("sim-")
        assert Path(data["qr_path"]).exists()
        assert data["qr_path"].endswith(".png")

    def test_validar_lote_ok_genera_pdf(self, monkeypatch, tmp_path):
        """Punto 4: la respuesta incluye certificado_path apuntando a un PDF generado."""
        secret = "test-secret"
        monkeypatch.setenv("JWT_SECRET", secret)
        monkeypatch.setenv("SKILLS_TMP_DIR", str(tmp_path))

        response = client.post(
            "/api/v1/skills/validar_lote",
            json={
                "lote_id": "L-003",
                "metadatos": {"cultivo": "maiz", "variedad": "hibrido"},
                "firma_digital": self._token(secret),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "certificado_path" in data
        assert data["certificado_path"].endswith(".pdf")
        assert Path(data["certificado_path"]).exists()

    def test_validar_lote_blockchain_web3_fallback(self, monkeypatch, tmp_path):
        """Punto 2: si GaiaChain no responde, devuelve fallback sim-lote-timestamp."""
        import unittest.mock as mock

        secret = "test-secret"
        monkeypatch.setenv("JWT_SECRET", secret)
        monkeypatch.setenv("SKILLS_TMP_DIR", str(tmp_path))
        monkeypatch.setenv("GAIACHAIN_PRIVATE_KEY", "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")

        fake_w3 = mock.MagicMock()
        fake_w3.is_connected.return_value = False
        monkeypatch.setattr(skills_router, "w3", fake_w3)

        response = client.post(
            "/api/v1/skills/validar_lote",
            json={
                "lote_id": "L-004",
                "metadatos": {"campo": "norte"},
                "firma_digital": self._token(secret),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tx_hash"].startswith("sim-L-004-")

    def test_validar_lote_blockchain_web3_onchain(self, monkeypatch, tmp_path):
        """Punto 2: con Web3 global mockeado produce hash hexadecimal on-chain."""
        import unittest.mock as mock

        secret = "test-secret"
        monkeypatch.setenv("JWT_SECRET", secret)
        monkeypatch.setenv("SKILLS_TMP_DIR", str(tmp_path))
        monkeypatch.setenv("GAIACHAIN_PRIVATE_KEY", "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")

        fake_tx_hash = bytes.fromhex("a" * 64)

        fake_w3 = mock.MagicMock()
        fake_w3.is_connected.return_value = True
        fake_w3.eth.default_account = "0xDeAdBeEf"
        fake_w3.eth.get_transaction_count.return_value = 0
        fake_w3.to_wei.return_value = 50_000_000_000
        signed_tx = mock.MagicMock()
        signed_tx.rawTransaction = b"\x00" * 32
        fake_w3.eth.account.sign_transaction.return_value = signed_tx
        fake_w3.eth.send_raw_transaction.return_value = fake_tx_hash
        monkeypatch.setattr(skills_router, "w3", fake_w3)

        response = client.post(
            "/api/v1/skills/validar_lote",
            json={
                "lote_id": "L-005",
                "metadatos": {"zona": "A1"},
                "firma_digital": self._token(secret),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tx_hash"] == f"0x{'a' * 64}"

    def test_generar_pdf_fallback_texto_plano(self, monkeypatch, tmp_path):
        """Punto 4: si falla reportlab, se genera texto plano con extensión .pdf."""
        output_path = tmp_path / "fallback.pdf"

        class BrokenDoc:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("reportlab disabled")

        monkeypatch.setattr(skills_router, "SimpleDocTemplate", BrokenDoc)

        pdf_path = skills_router.generar_pdf(
            "L-006",
            {"humedad": 60},
            "sim-L-006-1234567890",
            output_path,
        )

        assert pdf_path == str(output_path)
        assert output_path.exists()
        assert "TX Hash: sim-L-006-1234567890" in output_path.read_text()


class TestMetricsEndpoint:
    """Tests para /metrics (Prometheus)."""

    def test_metrics_returns_200(self):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type_text(self):
        response = client.get("/metrics")
        assert "text/plain" in response.headers.get("content-type", "")

    def test_metrics_contains_uptime(self):
        response = client.get("/metrics")
        assert "castuo_api_uptime_seconds" in response.text

    def test_metrics_contains_request_counter(self):
        client.get("/health")  # genera al menos 1 request contabilizado
        response = client.get("/metrics")
        assert "castuo_api_requests_total" in response.text


class TestAIPredictEndpoint:
    """Tests para /api/v1/ai/predict."""

    def test_predict_returns_200(self):
        response = client.post(
            "/api/v1/ai/predict",
            json={"data": {"humedad": 65, "temperatura": 25}},
        )
        assert response.status_code == 200

    def test_predict_response_has_prediction(self):
        response = client.post(
            "/api/v1/ai/predict",
            json={"data": {"humedad": 65, "temperatura": 25}},
        )
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert "model_version" in data

    def test_predict_empty_data_returns_422(self):
        response = client.post("/api/v1/ai/predict", json={})
        assert response.status_code == 422

    def test_predict_confidence_between_0_and_1(self):
        response = client.post(
            "/api/v1/ai/predict",
            json={"data": {"humedad": 65, "temperatura": 25}},
        )
        confidence = response.json()["confidence"]
        assert 0.0 <= confidence <= 1.0
