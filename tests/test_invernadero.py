"""
Tests de integración — Invernadero Agrovoltaico Hidropónico + Trazabilidad QR
Valida parámetros reales: pH, EC, O₂ disuelto, CO₂, VPD, DLI, agrovoltaico, cadena QR.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))
from main import app

client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures base
# ─────────────────────────────────────────────────────────────────────────────

LOTE_ID = "INVH-ES12345-TOMATE-ABCD1234"
OPERADOR_NIF = "12345678Z"


@pytest.fixture
def apertura_payload():
    return {
        "explotacion_rea": "ES12345",
        "operador_nif": OPERADOR_NIF,
        "cultivo": "tomate",
        "variedad": "Raf",
        "sistema": "goteo",
        "zona": "zona-A1",
        "superficie_m2": 500.0,
        "fecha_siembra": "2026-01-15",
        "semilla_origen": "Semillas Fitó — Lote SFT-2026-001",
        "semilla_certificada": True,
        "sustrato": "fibra_coco",
        "eco_certificado": True,
        "sigpac_ref": "14:123:0:45:1",
    }


@pytest.fixture
def solucion_optima():
    return {
        "lote_id": LOTE_ID,
        "zona": "zona-A1",
        "cultivo": "tomate",
        "sistema": "goteo",
        "ph": 6.0,
        "ec_ms_cm": 3.0,
        "temp_solucion_c": 20.0,
        "o2_disuelto_mg_l": 8.5,
        "nitrogeno_ppm": 180.0,
        "fosforo_ppm": 50.0,
        "potasio_ppm": 210.0,
        "caudal_l_h": 120.0,
    }


@pytest.fixture
def clima_optimo():
    return {
        "lote_id": LOTE_ID,
        "zona": "zona-A1",
        "cultivo": "tomate",
        "etapa": "fructificacion",
        "co2_ppm": 950.0,
        "vpd_kpa": 1.0,
        "temp_aire_c": 24.0,
        "humedad_relativa_pct": 70.0,
        "dli_mol_m2_dia": 20.0,
    }


@pytest.fixture
def agrovoltaico_payload():
    return {
        "lote_id": LOTE_ID,
        "panel_id": "string-01",
        "irradiancia_w_m2": 850.0,
        "kwh_generados": 42.5,
        "kwh_autoconsumidos": 35.0,
        "temperatura_panel_c": 55.0,
        "cobertura_sombra_pct": 25.0,
        "temp_bajo_panel_c": 28.0,
        "temp_zona_abierta_c": 33.5,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tests apertura de lote
# ─────────────────────────────────────────────────────────────────────────────

class TestAperturaLote:
    def test_apertura_genera_lote_id(self, apertura_payload):
        resp = client.post("/api/v1/invernadero/lote/apertura", json=apertura_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado"] == "abierto"
        assert data["lote_id"].startswith("INVH-ES12345-TOMATE-")
        assert len(data["hash_apertura"]) == 64  # SHA-256 hex

    def test_apertura_eco_certificado(self, apertura_payload):
        resp = client.post("/api/v1/invernadero/lote/apertura", json=apertura_payload)
        assert resp.status_code == 200
        assert resp.json()["payload"]["eco_certificado"] is True

    def test_apertura_sin_sigpac(self, apertura_payload):
        apertura_payload["sigpac_ref"] = None
        resp = client.post("/api/v1/invernadero/lote/apertura", json=apertura_payload)
        assert resp.status_code == 200

    def test_apertura_variedad_registrada(self, apertura_payload):
        resp = client.post("/api/v1/invernadero/lote/apertura", json=apertura_payload)
        assert resp.json()["variedad"] == "Raf"


# ─────────────────────────────────────────────────────────────────────────────
# Tests solución nutritiva — parámetros reales
# ─────────────────────────────────────────────────────────────────────────────

class TestSolucionNutritiva:
    def test_parametros_optimos_sin_alerta(self, solucion_optima):
        resp = client.post("/api/v1/invernadero/solucion-nutritiva", json=solucion_optima)
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado"] == "OPTIMO"
        assert data["alertas"] == []

    def test_ph_bajo_genera_alerta(self, solucion_optima):
        solucion_optima["ph"] = 5.0  # Tomate: mínimo 5.8
        resp = client.post("/api/v1/invernadero/solucion-nutritiva", json=solucion_optima)
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("pH" in a for a in data["alertas"])

    def test_ph_alto_genera_alerta(self, solucion_optima):
        solucion_optima["ph"] = 7.0  # Tomate: máximo 6.3
        resp = client.post("/api/v1/invernadero/solucion-nutritiva", json=solucion_optima)
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("pH" in a for a in data["alertas"])

    def test_ec_bajo_genera_alerta(self, solucion_optima):
        solucion_optima["ec_ms_cm"] = 0.5  # Tomate: mínimo 2.0
        resp = client.post("/api/v1/invernadero/solucion-nutritiva", json=solucion_optima)
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("EC" in a for a in data["alertas"])

    def test_o2_critico_genera_alerta(self, solucion_optima):
        solucion_optima["o2_disuelto_mg_l"] = 4.0  # Mínimo absoluto: 6.0 mg/L
        resp = client.post("/api/v1/invernadero/solucion-nutritiva", json=solucion_optima)
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("O₂" in a or "disuelto" in a for a in data["alertas"])

    def test_temp_solucion_alta_alerta(self, solucion_optima):
        solucion_optima["temp_solucion_c"] = 28.0  # Tomate: máximo 22°C
        resp = client.post("/api/v1/invernadero/solucion-nutritiva", json=solucion_optima)
        data = resp.json()
        assert data["estado"] == "ALERTA"

    def test_ph_invalido_rechazado(self, solucion_optima):
        solucion_optima["ph"] = 12.0  # Fuera del rango del modelo [4.0-8.5]
        resp = client.post("/api/v1/invernadero/solucion-nutritiva", json=solucion_optima)
        assert resp.status_code == 422

    def test_ec_negativa_rechazada(self, solucion_optima):
        solucion_optima["ec_ms_cm"] = -1.0
        resp = client.post("/api/v1/invernadero/solucion-nutritiva", json=solucion_optima)
        assert resp.status_code == 422

    def test_lechuga_ec_optimo_diferente(self):
        """Lechuga tiene rangos EC menores que tomate — validar por cultivo."""
        resp = client.post("/api/v1/invernadero/solucion-nutritiva", json={
            "lote_id": LOTE_ID,
            "zona": "zona-B1",
            "cultivo": "lechuga",
            "sistema": "NFT",
            "ph": 6.0,
            "ec_ms_cm": 1.2,   # Correcto para lechuga [0.8-1.6]
            "temp_solucion_c": 20.0,
            "o2_disuelto_mg_l": 8.0,
        })
        assert resp.status_code == 200
        assert resp.json()["estado"] == "OPTIMO"


# ─────────────────────────────────────────────────────────────────────────────
# Tests clima invernadero
# ─────────────────────────────────────────────────────────────────────────────

class TestClimaInvernadero:
    def test_clima_optimo_sin_alertas(self, clima_optimo):
        resp = client.post("/api/v1/invernadero/clima", json=clima_optimo)
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado"] == "OPTIMO"
        assert data["alertas"] == []

    def test_co2_bajo_alerta(self, clima_optimo):
        clima_optimo["co2_ppm"] = 400.0  # Tomate: mínimo 800 ppm
        resp = client.post("/api/v1/invernadero/clima", json=clima_optimo)
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("CO₂" in a for a in data["alertas"])

    def test_vpd_fuera_rango_alerta(self, clima_optimo):
        clima_optimo["vpd_kpa"] = 2.5  # Tomate: máximo 1.2 kPa
        resp = client.post("/api/v1/invernadero/clima", json=clima_optimo)
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("VPD" in a for a in data["alertas"])

    def test_hr_excesiva_alerta_hongos(self, clima_optimo):
        clima_optimo["humedad_relativa_pct"] = 90.0
        resp = client.post("/api/v1/invernadero/clima", json=clima_optimo)
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("HR" in a or "botrytis" in a.lower() for a in data["alertas"])

    def test_temperatura_excesiva_alerta(self, clima_optimo):
        clima_optimo["temp_aire_c"] = 38.0
        resp = client.post("/api/v1/invernadero/clima", json=clima_optimo)
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("calor" in a.lower() or "temperatura" in a.lower() for a in data["alertas"])

    def test_dli_bajo_en_floracion_alerta(self, clima_optimo):
        clima_optimo["dli_mol_m2_dia"] = 10.0  # Mínimo 15 en floración
        resp = client.post("/api/v1/invernadero/clima", json=clima_optimo)
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("DLI" in a for a in data["alertas"])

    def test_dli_bajo_en_vegetativo_no_alerta(self, clima_optimo):
        """En etapa vegetativa, DLI bajo no es alerta."""
        clima_optimo["etapa"] = "vegetativo"
        clima_optimo["dli_mol_m2_dia"] = 10.0
        resp = client.post("/api/v1/invernadero/clima", json=clima_optimo)
        data = resp.json()
        # Sin otras desviaciones → OPTIMO
        assert data["estado"] == "OPTIMO"


# ─────────────────────────────────────────────────────────────────────────────
# Tests agrovoltaico
# ─────────────────────────────────────────────────────────────────────────────

class TestAgrovoltaico:
    def test_registro_normal(self, agrovoltaico_payload):
        resp = client.post("/api/v1/invernadero/agrovoltaico", json=agrovoltaico_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado"] == "OK"
        assert data["alertas"] == []

    def test_delta_temperatura_calculado(self, agrovoltaico_payload):
        """Panel a 28°C bajo panel vs 33.5°C abierto → delta = 5.5°C de beneficio."""
        resp = client.post("/api/v1/invernadero/agrovoltaico", json=agrovoltaico_payload)
        data = resp.json()
        assert data["payload"]["delta_temperatura_c"] == pytest.approx(5.5, abs=0.01)
        assert data["payload"]["beneficio_termico"] is True

    def test_excedente_energetico_calculado(self, agrovoltaico_payload):
        """42.5 kWh generados - 35.0 consumidos = 7.5 kWh excedente."""
        resp = client.post("/api/v1/invernadero/agrovoltaico", json=agrovoltaico_payload)
        data = resp.json()
        assert data["payload"]["excedente_kwh"] == pytest.approx(7.5, abs=0.01)
        assert data["payload"]["balance_energetico"] == "excedente"

    def test_sombra_excesiva_alerta(self, agrovoltaico_payload):
        agrovoltaico_payload["cobertura_sombra_pct"] = 55.0  # > 40%
        resp = client.post("/api/v1/invernadero/agrovoltaico", json=agrovoltaico_payload)
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("sombra" in a.lower() or "DLI" in a for a in data["alertas"])

    def test_panel_sobrecalentado_alerta(self, agrovoltaico_payload):
        agrovoltaico_payload["temperatura_panel_c"] = 82.0  # > 75°C
        resp = client.post("/api/v1/invernadero/agrovoltaico", json=agrovoltaico_payload)
        data = resp.json()
        assert data["estado"] == "ALERTA"
        assert any("75" in a or "panel" in a.lower() for a in data["alertas"])

    def test_deficit_energetico(self, agrovoltaico_payload):
        agrovoltaico_payload["kwh_autoconsumidos"] = 50.0  # > generados
        resp = client.post("/api/v1/invernadero/agrovoltaico", json=agrovoltaico_payload)
        data = resp.json()
        assert data["payload"]["balance_energetico"] == "deficit"


# ─────────────────────────────────────────────────────────────────────────────
# Tests cosecha + cadena QR completa
# ─────────────────────────────────────────────────────────────────────────────

class TestCosechaYQR:
    def test_cosecha_genera_hash_cierre(self):
        resp = client.post("/api/v1/invernadero/cosecha", json={
            "lote_id": LOTE_ID,
            "fecha_cosecha": "2026-03-15",
            "kg_cosechados": 1250.0,
            "calibre": "Extra",
            "brix": 8.5,
            "destino": "mercado_local",
            "operador_nif": OPERADOR_NIF,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado"] == "LOTE_CERRADO"
        assert len(data["payload"]["hash_cierre_lote"]) == 64
        assert data["payload"]["qr_pendiente_generacion"] is True

    def test_cosecha_kg_cero_rechazado(self):
        resp = client.post("/api/v1/invernadero/cosecha", json={
            "lote_id": LOTE_ID,
            "fecha_cosecha": "2026-03-15",
            "kg_cosechados": 0.0,  # Debe ser > 0
            "destino": "mercado_local",
            "operador_nif": OPERADOR_NIF,
        })
        assert resp.status_code == 422

    def test_flujo_completo_qr_consumidor(self):
        """
        Flujo real completo:
        1. Registrar evento de siembra
        2. Registrar evento de cosecha
        3. Generar QR con cadena de hashes
        4. Verificar QR → consumidor ve datos auténticos
        """
        # 1. Evento siembra
        ev1 = client.post(
            "/api/v1/trazabilidad/qr/evento",
            params={
                "lote_id": LOTE_ID,
                "etapa": "siembra",
                "operador_nif": OPERADOR_NIF,
            },
            json={"variedad": "Raf", "sustrato": "fibra_coco"},
        )
        assert ev1.status_code == 200
        hash_ev1 = ev1.json()["hash_evento"]
        assert len(hash_ev1) == 64

        # 2. Evento cosecha
        ev2 = client.post(
            "/api/v1/trazabilidad/qr/evento",
            params={
                "lote_id": LOTE_ID,
                "etapa": "cosecha",
                "operador_nif": OPERADOR_NIF,
            },
            json={"kg": 1250.0, "brix": 8.5},
        )
        assert ev2.status_code == 200
        hash_ev2 = ev2.json()["hash_evento"]

        # 3. Generar QR
        hash_cierre = "a" * 64  # simulado
        qr_resp = client.post("/api/v1/trazabilidad/qr/generar", json={
            "lote_id": LOTE_ID,
            "hash_cierre": hash_cierre,
            "cultivo": "tomate",
            "variedad": "Raf",
            "fecha_cosecha": "2026-03-15",
            "kg_cosechados": 1250.0,
            "eco_certificado": True,
            "sin_pesticidas_sinteticos": True,
            "explotacion_rea": "ES12345",
            "operador_nif": OPERADOR_NIF,
            "sigpac_ref": "14:123:0:45:1",
            "destino": "mercado_local",
            "ph_medio": 6.1,
            "ec_medio_ms_cm": 2.8,
            "kwh_generados_total": 250.0,
            "kwh_autoconsumidos_total": 200.0,
            "eventos": [
                {"etapa": "siembra",  "timestamp": ev1.json()["timestamp"], "operador_nif": OPERADOR_NIF, "hash_evento": hash_ev1, "datos_resumidos": {}},
                {"etapa": "cosecha",  "timestamp": ev2.json()["timestamp"], "operador_nif": OPERADOR_NIF, "hash_evento": hash_ev2, "datos_resumidos": {}},
            ],
        })
        assert qr_resp.status_code == 200
        qr_data = qr_resp.json()
        assert len(qr_data["hash_cadena"]) == 64
        assert "verify.castuo360.eu" in qr_data["verify_url"]
        assert qr_data["resumen_consumidor"]["certificaciones"]["eco_certificado"] is True
        assert qr_data["resumen_consumidor"]["certificaciones"]["sin_pesticidas_sinteticos"] is True

        # 4. Verificar QR (consumidor escanea)
        hash_cadena = qr_data["hash_cadena"]
        verify_resp = client.get(f"/api/v1/trazabilidad/qr/verificar/{LOTE_ID}/{hash_cadena}")
        assert verify_resp.status_code == 200
        verify_data = verify_resp.json()
        assert verify_data["autentico"] is True
        assert verify_data["datos_lote"] is not None

    def test_verificar_qr_manipulado(self):
        """Si el hash no coincide, el QR debe marcarse como no auténtico."""
        # Primero generar un QR legítimo
        client.post("/api/v1/trazabilidad/qr/generar", json={
            "lote_id": "INVH-ES99999-LECHUGA-FFFF9999",
            "hash_cierre": "b" * 64,
            "cultivo": "lechuga",
            "variedad": "Lolla Rossa",
            "fecha_cosecha": "2026-03-20",
            "kg_cosechados": 80.0,
            "eco_certificado": True,
            "sin_pesticidas_sinteticos": True,
            "explotacion_rea": "ES99999",
            "operador_nif": OPERADOR_NIF,
            "destino": "directo_consumidor",
            "eventos": [],
        })
        # Verificar con hash falso
        resp = client.get("/api/v1/trazabilidad/qr/verificar/INVH-ES99999-LECHUGA-FFFF9999/hashfalso0000000000000000000000000000000000000000000000000000000")
        assert resp.status_code == 200
        assert resp.json()["autentico"] is False

    def test_verificar_lote_inexistente(self):
        resp = client.get("/api/v1/trazabilidad/qr/verificar/INVH-NOEXI-STE-00000000/cualquierhash00000000000000000000000000000000000000000000000000000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["autentico"] is False
        assert data["hash_registrado"] is None

    def test_energia_solar_en_resumen_consumidor(self):
        """El consumidor debe ver qué % de energía solar se usó en su cultivo."""
        qr_resp = client.post("/api/v1/trazabilidad/qr/generar", json={
            "lote_id": "INVH-ES00001-PIMIENTO-AA112233",
            "hash_cierre": "c" * 64,
            "cultivo": "pimiento",
            "variedad": "Ramiro",
            "fecha_cosecha": "2026-03-10",
            "kg_cosechados": 500.0,
            "eco_certificado": True,
            "sin_pesticidas_sinteticos": True,
            "explotacion_rea": "ES00001",
            "operador_nif": OPERADOR_NIF,
            "destino": "exportacion",
            "kwh_generados_total": 400.0,
            "kwh_autoconsumidos_total": 360.0,
            "eventos": [],
        })
        assert qr_resp.status_code == 200
        energia = qr_resp.json()["resumen_consumidor"]["energia_solar"]
        assert energia is not None
        assert energia["origen"] == "solar_agrovoltaico"
        assert energia["autoconsumo_pct"] == pytest.approx(90.0, abs=0.1)


# ─────────────────────────────────────────────────────────────────────────────
# Tests rangos óptimos
# ─────────────────────────────────────────────────────────────────────────────

class TestRangosOptimos:
    def test_rangos_tomate(self):
        resp = client.get("/api/v1/invernadero/rangos/tomate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["parametros"]["ph"]["min"] == 5.8
        assert data["parametros"]["ph"]["max"] == 6.3
        assert data["parametros"]["ec"]["unidad"] == "mS/cm"

    def test_rangos_lechuga_ec_menor(self):
        resp = client.get("/api/v1/invernadero/rangos/lechuga")
        assert resp.status_code == 200
        data = resp.json()
        # Lechuga necesita menos EC que tomate
        assert data["parametros"]["ec"]["max"] < 2.0

    def test_cultivo_desconocido_404(self):
        resp = client.get("/api/v1/invernadero/rangos/platano")
        assert resp.status_code == 422  # Pydantic enum validation


# ─────────────────────────────────────────────────────────────────────────────
# Tests registro fitosanitario
# ─────────────────────────────────────────────────────────────────────────────

class TestFitosanitario:
    def test_registro_sin_tratamiento(self):
        """Para certificación sin químicos: documentar inspección sin tratamiento."""
        resp = client.post("/api/v1/invernadero/fitosanitario", json={
            "lote_id": LOTE_ID,
            "fecha": "2026-02-01",
            "tipo": "ninguno",
            "justificacion": "Inspección preventiva semanal. Sin incidencias. Sin tratamiento requerido.",
            "operador_nif": OPERADOR_NIF,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["payload"]["eco_compatible"] is True

    def test_biocontrol_eco_compatible(self):
        resp = client.post("/api/v1/invernadero/fitosanitario", json={
            "lote_id": LOTE_ID,
            "fecha": "2026-02-10",
            "tipo": "biocontrol",
            "producto": "Trichoderma harzianum",
            "justificacion": "Aplicación preventiva de agente biocontrolador contra Fusarium.",
            "operador_nif": OPERADOR_NIF,
        })
        assert resp.status_code == 200

    def test_curativo_sin_producto_rechazado(self):
        resp = client.post("/api/v1/invernadero/fitosanitario", json={
            "lote_id": LOTE_ID,
            "fecha": "2026-02-15",
            "tipo": "curativo",
            "justificacion": "Tratamiento curativo sin especificar producto",
            "operador_nif": OPERADOR_NIF,
        })
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# Test health check global
# ─────────────────────────────────────────────────────────────────────────────

def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "3.0.0"
