"""
Tests extendidos — Invernadero Agrovoltaico Hidropónico
Cubre: actuadores REST, controlador de actuadores, detector de anomalías,
       predictor de cosecha, Modbus simulado, InfluxDB escritor simulado.
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app

client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tests — ActuatorController (unit)
# ─────────────────────────────────────────────────────────────────────────────

class TestActuatorController:
    def setup_method(self):
        from services.actuators.actuator_controller import ActuatorController
        self.ctrl = ActuatorController()

    def test_control_ventilacion_encender(self):
        r = self.ctrl.control("ventilacion", "encender", zona="zona-A", triggered_by="test")
        assert r["ok"] is True
        assert r["actuador"] == "ventilacion"
        assert r["accion"] == "encender"

    def test_control_ventilacion_ajustar(self):
        r = self.ctrl.control("ventilacion", "ajustar", zona="zona-A", valor=60.0)
        assert r["ok"] is True
        assert r["valor"] == 60.0

    def test_control_acido_pulso(self):
        r = self.ctrl.control("acido", "pulso", zona="zona-B", valor=15.0, duracion_seg=5)
        assert r["ok"] is True
        assert r["actuador"] == "acido"

    def test_control_actuador_invalido(self):
        r = self.ctrl.control("reactor_nuclear", "encender")
        assert r["ok"] is False
        assert "no reconocido" in r["error"]

    def test_estado_actualizacion(self):
        self.ctrl.control("calefaccion", "encender", zona="zona-C")
        estado = self.ctrl.get_status()
        assert "calefaccion" in estado
        assert estado["calefaccion"]["on"] is True

    def test_emergencia_stop_apaga_todo(self):
        self.ctrl.control("ventilacion", "encender", zona="general")
        self.ctrl.control("calefaccion", "encender", zona="general")
        r = self.ctrl.emergencia_stop(zona="all")
        assert r["ok"] is True
        assert r["actuadores_apagados"] > 0
        # Todos deben estar apagados
        estado = self.ctrl.get_status()
        activos = [k for k, v in estado.items() if v.get("on")]
        assert len(activos) == 0

    def test_historial_registra_eventos(self):
        self.ctrl.control("riego", "encender", zona="zona-D")
        self.ctrl.control("riego", "apagar",  zona="zona-D")
        historial = self.ctrl.get_history(limit=10)
        assert len(historial) >= 2
        actuadores = [e["actuador"] for e in historial]
        assert "riego" in actuadores

    def test_ml_dosificados_acumulan(self):
        self.ctrl.control("nutrientes_a", "pulso", zona="zona-A", valor=25.0)
        self.ctrl.control("nutrientes_a", "pulso", zona="zona-A", valor=25.0)
        estado = self.ctrl.get_status()
        assert estado["nutrientes_a"].get("ml_dosificados", 0) >= 50.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tests — Recomendaciones automáticas (unit)
# ─────────────────────────────────────────────────────────────────────────────

class TestRecomendacionesActuadores:
    def test_temperatura_alta_recomienda_ventilacion(self):
        from services.actuators.actuator_controller import recomendar_accion_temperatura
        r = recomendar_accion_temperatura(32.0, temp_min=18, temp_max=28)
        assert r is not None
        assert r["actuador"] == "ventilacion"
        assert r["accion"] == "ajustar"
        assert r["valor"] > 0

    def test_temperatura_baja_recomienda_calefaccion(self):
        from services.actuators.actuator_controller import recomendar_accion_temperatura
        r = recomendar_accion_temperatura(12.0, temp_min=18, temp_max=28)
        assert r is not None
        assert r["actuador"] == "calefaccion"
        assert r["accion"] == "encender"

    def test_temperatura_en_rango_sin_accion(self):
        from services.actuators.actuator_controller import recomendar_accion_temperatura
        r = recomendar_accion_temperatura(23.0, temp_min=18, temp_max=28)
        assert r is None

    def test_ph_alto_recomienda_acido(self):
        from services.actuators.actuator_controller import recomendar_accion_ph
        r = recomendar_accion_ph(7.0, ph_min=5.5, ph_max=6.5)
        assert r is not None
        assert r["actuador"] == "acido"
        assert r["accion"] == "pulso"

    def test_ph_bajo_recomienda_base(self):
        from services.actuators.actuator_controller import recomendar_accion_ph
        r = recomendar_accion_ph(4.8, ph_min=5.5, ph_max=6.5)
        assert r is not None
        assert r["actuador"] == "base"

    def test_ph_en_rango_sin_accion(self):
        from services.actuators.actuator_controller import recomendar_accion_ph
        r = recomendar_accion_ph(6.0, ph_min=5.5, ph_max=6.5)
        assert r is None

    def test_ec_baja_recomienda_nutrientes(self):
        from services.actuators.actuator_controller import recomendar_accion_ec
        r = recomendar_accion_ec(0.5, ec_min=1.5, ec_max=3.0)
        assert r is not None
        assert r["actuador"] == "nutrientes_a"

    def test_ec_alta_recomienda_dilusion(self):
        from services.actuators.actuator_controller import recomendar_accion_ec
        r = recomendar_accion_ec(4.0, ec_min=1.5, ec_max=3.0)
        assert r is not None
        assert r["actuador"] == "riego"

    def test_sombra_mucha_luz_aumentar(self):
        from services.actuators.actuator_controller import recomendar_sombra_agrovoltaica
        r = recomendar_sombra_agrovoltaica(800.0, cultivo="lechuga", cobertura_actual_pct=10.0)
        assert r is not None
        assert r["actuador"] == "sombra"
        assert r["accion"] == "ajustar"
        assert r["valor"] > 10.0

    def test_sombra_poca_luz_reducir(self):
        from services.actuators.actuator_controller import recomendar_sombra_agrovoltaica
        r = recomendar_sombra_agrovoltaica(50.0, cultivo="tomate", cobertura_actual_pct=50.0)
        assert r is not None
        assert r["valor"] < 50.0

    def test_sombra_luz_optima_sin_accion(self):
        from services.actuators.actuator_controller import recomendar_sombra_agrovoltaica
        r = recomendar_sombra_agrovoltaica(500.0, cultivo="tomate", cobertura_actual_pct=20.0)
        assert r is None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Tests — AnomalyDetector (unit)
# ─────────────────────────────────────────────────────────────────────────────

class TestAnomalyDetector:
    """Detección de anomalías con IsolationForest / reglas."""

    NORMAL_SAMPLE = {
        "temperatura_c": 24.0,
        "humedad_pct":   65.0,
        "co2_ppm":      950.0,
        "vpd_kpa":        0.9,
        "ph":             6.0,
        "ec_ms_cm":       2.5,
    }

    def _get_detector(self):
        from services.ai.anomaly_detector import GreenhouseAnomalyDetector
        d = GreenhouseAnomalyDetector(contamination=0.05)
        # Entrenar con 30 muestras normales
        training = []
        rng = np.random.default_rng(42)
        for _ in range(30):
            training.append({
                "temperatura_c": float(rng.normal(24, 1)),
                "humedad_pct":   float(rng.normal(65, 3)),
                "co2_ppm":       float(rng.normal(950, 50)),
                "vpd_kpa":       float(rng.normal(0.9, 0.1)),
                "ph":            float(rng.normal(6.0, 0.1)),
                "ec_ms_cm":      float(rng.normal(2.5, 0.2)),
            })
        d.fit(training)
        return d

    def test_lectura_normal_no_es_anomalia(self):
        d = self._get_detector()
        result = d.detect(self.NORMAL_SAMPLE)
        assert result.es_anomalia is False
        assert result.metodo in ("isolation_forest", "reglas_umbrales")

    def test_temperatura_extrema_es_anomalia(self):
        d = self._get_detector()
        lectura = {**self.NORMAL_SAMPLE, "temperatura_c": 55.0}
        result = d.detect(lectura)
        assert result.es_anomalia is True

    def test_ph_fuera_rango_es_anomalia(self):
        d = self._get_detector()
        lectura = {**self.NORMAL_SAMPLE, "ph": 9.5}
        result = d.detect(lectura)
        assert result.es_anomalia is True
        assert "ph" in result.variables_criticas

    def test_ec_extrema_es_anomalia(self):
        d = self._get_detector()
        lectura = {**self.NORMAL_SAMPLE, "ec_ms_cm": 12.0}
        result = d.detect(lectura)
        assert result.es_anomalia is True

    def test_resultado_tiene_timestamp(self):
        d = self._get_detector()
        result = d.detect(self.NORMAL_SAMPLE)
        assert "T" in result.timestamp  # ISO-8601

    def test_resultado_serializable(self):
        d = self._get_detector()
        result = d.detect(self.NORMAL_SAMPLE)
        d_dict = result.to_dict()
        assert "es_anomalia" in d_dict
        assert "score" in d_dict
        assert "metodo" in d_dict

    def test_detector_sin_entrenar_usa_reglas(self):
        from services.ai.anomaly_detector import GreenhouseAnomalyDetector
        d = GreenhouseAnomalyDetector()  # Sin fit
        lectura = {**self.NORMAL_SAMPLE, "temperatura_c": 45.0}
        result = d.detect(lectura)
        assert result.metodo == "reglas_umbrales"
        assert result.es_anomalia is True


# ─────────────────────────────────────────────────────────────────────────────
# 4. Tests — HarvestPredictor (unit)
# ─────────────────────────────────────────────────────────────────────────────

class TestHarvestPredictor:
    def _predictor(self):
        from services.ai.anomaly_detector import HarvestPredictor
        return HarvestPredictor()

    def test_prediccion_tomate_condiciones_optimas(self):
        p = self._predictor()
        result = p.predict(
            cultivo="tomate",
            temp_media_c=22.0,
            co2_medio_ppm=950.0,
            dli_medio_mol_m2_dia=20.0,
            ec_medio_ms_cm=3.0,
            dias_cultivo=30,
            superficie_m2=100.0,
        )
        # En condiciones óptimas debe acercarse al referencia (35 kg/m²)
        assert result.rendimiento_estimado_kg_m2 > 20.0
        assert result.confianza_pct > 60.0
        assert result.dias_para_cosecha >= 0

    def test_prediccion_condiciones_suboptimas_menor_rendimiento(self):
        p = self._predictor()
        optimo = p.predict("tomate", 22.0, 950.0, 20.0, 3.0, 30)
        suboptimo = p.predict("tomate", 10.0, 300.0, 5.0, 0.5, 30)
        assert suboptimo.rendimiento_estimado_kg_m2 < optimo.rendimiento_estimado_kg_m2

    def test_prediccion_lechuga_referencia_menor(self):
        p = self._predictor()
        result = p.predict("lechuga", 20.0, 800.0, 15.0, 1.2, 20)
        # Lechuga tiene ref 4 kg/m² << tomate 35 kg/m²
        assert result.rendimiento_estimado_kg_m2 < 10.0

    def test_prediccion_tiene_factores(self):
        p = self._predictor()
        result = p.predict("tomate", 22.0, 950.0, 20.0, 3.0, 30)
        assert "temperatura" in result.factores
        assert "co2" in result.factores
        assert "luz_dli" in result.factores
        assert "ec_nutrientes" in result.factores

    def test_prediccion_serializable(self):
        p = self._predictor()
        result = p.predict("pimiento", 22.0, 900.0, 18.0, 2.5, 45)
        d = result.to_dict()
        assert d["cultivo"] == "pimiento"
        assert isinstance(d["rendimiento_estimado_kg_m2"], float)
        assert "metodo" in d

    def test_dias_cosecha_decrece_con_avance(self):
        p = self._predictor()
        r_inicio = p.predict("tomate", 22.0, 950.0, 20.0, 3.0, dias_cultivo=0)
        r_medio  = p.predict("tomate", 22.0, 950.0, 20.0, 3.0, dias_cultivo=45)
        r_fin    = p.predict("tomate", 22.0, 950.0, 20.0, 3.0, dias_cultivo=90)
        assert r_inicio.dias_para_cosecha > r_medio.dias_para_cosecha
        assert r_fin.dias_para_cosecha == 0


# ─────────────────────────────────────────────────────────────────────────────
# 5. Tests — ModbusEnergyClient simulado (unit)
# ─────────────────────────────────────────────────────────────────────────────

class TestModbusClientSimulado:
    def _client(self):
        from services.energy.modbus_client import ModbusEnergyClient
        return ModbusEnergyClient()  # Sin inversor real → modo simulación

    def test_lectura_simulada_retorna_reading(self):
        c = self._client()
        r = c.read_solar_data()
        assert r is not None
        assert r.simulado is True
        assert r.voltaje_v > 0
        assert r.potencia_w >= 0

    def test_lectura_tiene_timestamp(self):
        c = self._client()
        r = c.read_solar_data()
        assert "T" in r.timestamp

    def test_lectura_serializable(self):
        c = self._client()
        d = c.read_solar_data().to_dict()
        assert "voltaje_v" in d
        assert "potencia_w" in d
        assert "simulado" in d
        assert d["simulado"] is True

    def test_temperatura_panel_en_rango(self):
        c = self._client()
        r = c.read_solar_data()
        # Temperatura panel simulada debe estar entre 20 y 65°C
        assert 20.0 <= r.temperatura_panel_c <= 65.0

    def test_calculate_shadow_adjustment_mucha_luz(self):
        from services.energy.modbus_client import calculate_shadow_adjustment
        r = calculate_shadow_adjustment(800.0, "lechuga", 10.0)  # PAR 800 > óptimo 350
        assert r["accion"] == "aumentar_sombra"
        assert r["nueva_cobertura_pct"] > 10.0

    def test_calculate_shadow_adjustment_poca_luz(self):
        from services.energy.modbus_client import calculate_shadow_adjustment
        r = calculate_shadow_adjustment(50.0, "tomate", 50.0)  # PAR 50 << óptimo 600
        assert r["accion"] == "reducir_sombra"
        assert r["nueva_cobertura_pct"] < 50.0

    def test_calculate_shadow_adjustment_luz_optima(self):
        from services.energy.modbus_client import calculate_shadow_adjustment
        r = calculate_shadow_adjustment(600.0, "tomate", 20.0)  # PAR 600 = óptimo tomate
        assert r["accion"] == "mantener"
        assert r["delta_pct"] == 0

    def test_autoconsumo_pct(self):
        from services.energy.modbus_client import calcular_autoconsumo_pct
        assert calcular_autoconsumo_pct(40.0, 36.0) == pytest.approx(90.0, abs=0.01)
        assert calcular_autoconsumo_pct(40.0, 40.0) == 100.0
        assert calcular_autoconsumo_pct(0.0, 5.0) == 0.0

    def test_excedente_kwh(self):
        from services.energy.modbus_client import calcular_excedente_kwh
        assert calcular_excedente_kwh(42.5, 35.0) == pytest.approx(7.5, abs=0.01)
        assert calcular_excedente_kwh(30.0, 35.0) == pytest.approx(-5.0, abs=0.01)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Tests — InfluxWriter simulado (unit)
# ─────────────────────────────────────────────────────────────────────────────

class TestInfluxWriterSimulado:
    def _writer(self):
        from services.influxdb.influx_writer import InfluxWriter
        return InfluxWriter()  # Sin token → modo simulación

    def test_write_sensor_sin_influx_guarda_en_buffer(self):
        w = self._writer()
        w.flush_sim_buffer()
        w.write_sensor_reading(
            lote_id="TEST-001",
            zona="zona-A",
            cultivo="tomate",
            measurement="clima",
            fields={"temp_aire_c": 24.0, "co2_ppm": 950.0},
        )
        buf = w.get_sim_buffer()
        assert len(buf) == 1
        assert buf[0]["measurement"] == "clima"
        assert buf[0]["fields"]["temp_aire_c"] == 24.0

    def test_write_energy_en_bucket_correcto(self):
        w = self._writer()
        w.flush_sim_buffer()
        w.write_energy_reading("TEST-001", "string-01", {"potencia_w": 5000.0})
        buf = w.get_sim_buffer()
        assert buf[0]["bucket"].endswith("energia")

    def test_write_actuator_event(self):
        w = self._writer()
        w.flush_sim_buffer()
        w.write_actuator_event("ventilacion", "encender", "zona-A", valor=75.0)
        buf = w.get_sim_buffer()
        assert buf[0]["tags"]["actuador"] == "ventilacion"
        assert buf[0]["tags"]["accion"] == "encender"

    def test_buffer_no_supera_1000(self):
        w = self._writer()
        w.flush_sim_buffer()
        for i in range(1100):
            w.write_sensor_reading("L", "z", "t", "m", {"v": float(i)})
        assert len(w.get_sim_buffer()) <= 1000

    def test_flush_borra_buffer(self):
        w = self._writer()
        w.write_sensor_reading("L", "z", "t", "m", {"v": 1.0})
        w.flush_sim_buffer()
        assert len(w.get_sim_buffer()) == 0


# ─────────────────────────────────────────────────────────────────────────────
# 7. Tests — API Actuadores REST
# ─────────────────────────────────────────────────────────────────────────────

class TestActuadoresAPI:
    """Tests de los endpoints REST del router actuadores (dev-mode JWT)."""

    def test_listar_actuadores_sin_auth(self):
        resp = client.get("/api/v1/actuadores/actuadores-disponibles")
        assert resp.status_code == 200
        data = resp.json()
        assert "actuadores" in data
        assert "acciones" in data
        nombres = [a["id"] for a in data["actuadores"]]
        assert "ventilacion" in nombres
        assert "acido" in nombres
        assert "sombra" in nombres

    def test_sombra_ajuste_sin_auth(self):
        resp = client.get(
            "/api/v1/actuadores/sombra/ajuste",
            params={"luz_par_umol": 800, "cultivo": "lechuga", "cobertura_actual_pct": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "accion" in data
        assert data["luz_actual"] == 800.0

    def test_control_ventilacion_dev_mode(self):
        resp = client.post("/api/v1/actuadores/control", json={
            "actuador": "ventilacion",
            "accion":   "ajustar",
            "zona":     "zona-A",
            "valor":    70.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["actuador"] == "ventilacion"
        assert data["valor"] == 70.0

    def test_control_actuador_invalido_422(self):
        resp = client.post("/api/v1/actuadores/control", json={
            "actuador": "motorreactor",
            "accion":   "encender",
        })
        assert resp.status_code == 422

    def test_control_ajustar_sin_valor_422(self):
        resp = client.post("/api/v1/actuadores/control", json={
            "actuador": "ventilacion",
            "accion":   "ajustar",
            # sin valor
        })
        assert resp.status_code == 422

    def test_estado_endpoint(self):
        resp = client.get("/api/v1/actuadores/estado")
        assert resp.status_code == 200
        data = resp.json()
        assert "estado" in data
        assert "total_actuadores" in data
        assert data["total_actuadores"] > 0

    def test_historial_endpoint(self):
        # Primero ejecutar un control
        client.post("/api/v1/actuadores/control", json={
            "actuador": "riego",
            "accion":   "encender",
            "zona":     "zona-B",
        })
        resp = client.get("/api/v1/actuadores/historial", params={"limit": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert "eventos" in data
        assert isinstance(data["eventos"], list)

    def test_historial_limit_invalido_422(self):
        resp = client.get("/api/v1/actuadores/historial", params={"limit": 9999})
        assert resp.status_code == 422

    def test_emergencia_stop(self):
        # Encender primero
        client.post("/api/v1/actuadores/control", json={
            "actuador": "calefaccion", "accion": "encender", "zona": "general"
        })
        resp = client.post("/api/v1/actuadores/emergencia", params={"zona": "all"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["accion"] == "emergencia_stop"
        assert data["actuadores_apagados"] > 0

    def test_control_automatico_temperatura(self):
        resp = client.post("/api/v1/actuadores/automatico", json={
            "zona": "zona-test",
            "temperatura_c": 35.0,
            "temp_min": 18.0,
            "temp_max": 28.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["acciones_ejecutadas"] >= 1

    def test_control_automatico_ph(self):
        resp = client.post("/api/v1/actuadores/automatico", json={
            "zona": "zona-test",
            "ph": 7.5,
            "ph_min": 5.5,
            "ph_max": 6.5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["acciones_ejecutadas"] >= 1
        # Debe haber dosificado ácido
        actuadores = [e["actuador"] for e in data["detalle"]["ejecutadas"]]
        assert "acido" in actuadores

    def test_control_automatico_ec_baja(self):
        resp = client.post("/api/v1/actuadores/automatico", json={
            "zona": "zona-test",
            "ec_ms_cm": 0.3,
            "ec_min": 1.5,
            "ec_max": 3.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["acciones_ejecutadas"] >= 1

    def test_control_automatico_todo_en_rango(self):
        resp = client.post("/api/v1/actuadores/automatico", json={
            "zona":           "zona-optima",
            "temperatura_c":  23.0,
            "temp_min":       18.0,
            "temp_max":       28.0,
            "ph":              6.0,
            "ph_min":          5.5,
            "ph_max":          6.5,
            "ec_ms_cm":        2.5,
            "ec_min":          1.5,
            "ec_max":          3.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        # Todo en rango → cero acciones ejecutadas
        assert data["acciones_ejecutadas"] == 0
        assert data["sin_accion_requerida"] == 3
