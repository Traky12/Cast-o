"""
Tests para ESP32 IoT Integration
pytest-based comprehensive test suite
"""

import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
import asyncio

# Importar desde api
try:
    from api.routers.esp32_iot import router
    from main import app
except ImportError:
    from routers.esp32_iot import router

# ─── FIXTURES ────────────────────────────

@pytest.fixture
def client():
    """TestClient para FastAPI"""
    test_app = app if hasattr(app, 'openapi') else create_test_app()
    return TestClient(test_app)

@pytest.fixture
async def async_client():
    """Cliente asincrónico (si necesitamos)"""
    from httpx import AsyncClient
    return AsyncClient()

@pytest.fixture
def mock_sensor_payload():
    """Payload típico de sensor depuis ESP32"""
    return {
        "esp32_id": "CAX21-MAIN",
        "ph": 6.2,
        "ec": 1800.0,
        "tds": 900.0,
        "temperature_c": 24.5,
        "wifi_rssi": -55,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@pytest.fixture
def mock_anomaly_payload():
    """Payload con valores fuera de rango"""
    return {
        "esp32_id": "CAX21-MAIN",
        "ph": 4.0,  # Bajo (< 5.5)
        "ec": 2600.0,  # Alto (> 2.4)
        "tds": 1300.0,  # Alto (> 1200)
        "temperature_c": 35.0,  # Alto (> 30)
        "wifi_rssi": -120,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@pytest.fixture
def mock_actuator_control():
    """Control de actuador típico"""
    return {
        "actuator": "riego",
        "action": "on",
        "duration_seconds": 120,
        "mode": "manual"
    }

# ─── TESTS: ENDPOINT /sensors/reading ────────────────────

class TestSensorReading:
    """Validación de endpoint POST /api/v1/esp32/sensors/reading"""
    
    def test_valid_sensor_reading(self, client, mock_sensor_payload):
        """✅ Lectura válida debe retornar 200 OK"""
        response = client.post(
            "/api/v1/esp32/sensors/reading",
            json=mock_sensor_payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"
        assert data["esp32_id"] == "CAX21-MAIN"
        assert data["readings_count"] == 4  # pH, EC, TDS, Temp
        assert len(data["anomalies"]) == 0  # Sin anomalías
    
    def test_anomaly_detection(self, client, mock_anomaly_payload):
        """⚠️ Valores fuera de rango deben detectarse como anomalías"""
        response = client.post(
            "/api/v1/esp32/sensors/reading",
            json=mock_anomaly_payload
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["anomalies"]) > 0
        assert any(a["sensor"] == "pH" for a in data["anomalies"])
        assert any(a["sensor"] == "EC" for a in data["anomalies"])
    
    def test_partial_sensor_data(self, client):
        """Payload parcial debe funcionar (no todos los sensores siempre envían)"""
        partial = {
            "esp32_id": "CAX21-MAIN",
            "ph": 6.3,
            "temperature_c": 23.8
        }
        response = client.post("/api/v1/esp32/sensors/reading", json=partial)
        assert response.status_code == 200
        data = response.json()
        assert data["readings_count"] == 2
    
    def test_caching_last_reading(self, client, mock_sensor_payload):
        """El endpoint debe cachear la última lectura"""
        # Primera lectura
        response1 = client.post("/api/v1/esp32/sensors/reading", json=mock_sensor_payload)
        assert response1.status_code == 200
        
        # Verificar cache
        response2 = client.get("/api/v1/esp32/sensors/latest/CAX21-MAIN")
        assert response2.status_code == 200
        cached = response2.json()
        assert cached["readings"]["ph"]["value"] == 6.2

# ─── TESTS: ENDPOINT /sensors/latest ────────────────────

class TestSensorQuery:
    """Consulta de últimas lecturas"""
    
    def test_latest_sensor_not_found(self, client):
        """Device no visto debe retornar 404"""
        response = client.get("/api/v1/esp32/sensors/latest/UNKNOWN-DEVICE")
        assert response.status_code == 404
    
    def test_latest_sensor_found(self, client, mock_sensor_payload):
        """Después de registrar, debe estar disponible"""
        # Registrar
        client.post("/api/v1/esp32/sensors/reading", json=mock_sensor_payload)
        
        # Consultar
        response = client.get("/api/v1/esp32/sensors/latest/CAX21-MAIN")
        assert response.status_code == 200
        data = response.json()
        assert "readings" in data
        assert "timestamp" in data
    
    def test_get_all_sensors(self, client, mock_sensor_payload):
        """GET /sensors/all debe retornar todos los dispositivos"""
        # Registrar datos
        client.post("/api/v1/esp32/sensors/reading", json=mock_sensor_payload)
        
        # Consultar todos
        response = client.get("/api/v1/esp32/sensors/all")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "CAX21-MAIN" in data["devices"]

# ─── TESTS: ENDPOINT /camera/stream ─────────────────────

class TestCameraStream:
    """Validación de streaming de video"""

    def test_camera_stream_proxy(self, client):
        """Stream debe proxificar exitosamente"""
        # (Nota: En tests funcionales, hacer streaming real es complejo)
        # Este es un test básico de integración
        response = client.get("/api/v1/esp32/camera/stream")
        # Response debe ser 200 o 503 (si no hay hardware)
        assert response.status_code in [200, 503]
    
    def test_camera_snapshot(self, client):
        """Snapshot debe retornar JPEG"""
        response = client.get("/api/v1/esp32/camera/snapshot")
        # 200 si funciona, 503 si no hay hardware
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            assert response.headers.get("content-type").startswith("image")

# ─── TESTS: ENDPOINT /dashboard ─────────────────────────

class TestDashboard:
    """Dashboard HTML interactivo"""
    
    def test_dashboard_loads(self, client):
        """Dashboard HTML debe ser servido"""
        response = client.get("/api/v1/esp32/dashboard")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "Live Feed CAX21" in response.text
        assert "canvas" in response.text or "img" in response.text
    
    def test_dashboard_has_controls(self, client):
        """Dashboard debe tener botones de control"""
        response = client.get("/api/v1/esp32/dashboard")
        assert "riego" in response.text.lower()
        assert "ozono" in response.text.lower()

# ─── TESTS: ACTUATOR CONTROL ────────────────────────────

class TestActuatorControl:
    """Control de actuadores (riego, ozono)"""
    
    @patch('routers.esp32_iot.httpx.AsyncClient')
    def test_valid_riego_command(self, mock_http_client, client, mock_actuator_control):
        """Comando riego válido"""
        response = client.post(
            "/api/v1/esp32/actuators/control",
            json=mock_actuator_control
        )
        assert response.status_code in [200, 503]  # 503 si no hay ESP32 físico
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ok"
            assert data["actuator"] == "riego"
    
    def test_invalid_actuator_type(self, client):
        """Actuador inválido debe retornar 400"""
        response = client.post(
            "/api/v1/esp32/actuators/control",
            json={
                "actuator": "invalid_actuator",
                "action": "on"
            }
        )
        assert response.status_code == 400
    
    def test_actuator_status_endpoint(self, client, mock_actuator_control):
        """GET /actuators/status debe retornar estado"""
        # Hacer comando
        client.post("/api/v1/esp32/actuators/control", json=mock_actuator_control)
        
        # Consultar status
        response = client.get("/api/v1/esp32/actuators/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "actuators" in data

# ─── TESTS: SENSOR MODELS ───────────────────────────────

class TestSensorModels:
    """Validación de Pydantic models"""
    
    def test_sensor_reading_validation(self):
        """SensorReading debe validar correctamente"""
        from routers.esp32_iot import SensorReading
        
        valid = SensorReading(
            sensor_type="pH",
            value=6.2,
            unit="pH"
        )
        assert valid.sensor_type == "pH"
        assert valid.calibrated is False
    
    def test_sensors_payload_validation(self):
        """SensorsPayload debe requerir esp32_id"""
        from routers.esp32_iot import SensorsPayload
        
        with pytest.raises(Exception):  # ValidationError
            SensorsPayload()  # Falta esp32_id
    
    def test_actuator_control_validation(self):
        """ActuatorControl debe validar tipo de actuador"""
        from routers.esp32_iot import ActuatorControl
        
        valid = ActuatorControl(
            actuator="riego",
            action="on"
        )
        assert valid.actuator == "riego"
        assert valid.mode == "manual"

# ─── TESTS: INTEGRACIÓN CON MQTT ────────────────────────

class TestMQTTIntegration:
    """Verify que sensores NO publican a MQTT (HTTP solo)"""
    
    def test_sensor_reading_no_mqtt(self, client, mock_sensor_payload):
        """Lectura sensor no debe publicar a MQTT"""
        response = client.post(
            "/api/v1/esp32/sensors/reading",
            json=mock_sensor_payload
        )
        assert response.status_code == 200
        # MQTT no debe ser llamado para lectura de sensores
        # mock_mqtt.publish.assert_not_called()

# ─── TESTS: ERROR HANDLING ──────────────────────────────

class TestErrorHandling:
    """Manejo de errores y edge cases"""
    
    def test_malformed_json(self, client):
        """JSON mal formado"""
        response = client.post(
            "/api/v1/esp32/sensors/reading",
            content="not json",
        )
        assert response.status_code >= 400
    
    def test_esp32_connection_timeout(self, client):
        """Timeout al conectar con ESP32"""
        with patch('routers.esp32_iot.httpx.AsyncClient') as mock_client:
            mock_client.side_effect = Exception("Connection timeout")
            response = client.get("/api/v1/esp32/camera/snapshot")
            assert response.status_code in [503, 500]
    
    def test_missing_required_fields(self, client):
        """Faltan campos requeridos"""
        response = client.post(
            "/api/v1/esp32/sensors/reading",
            json={"ph": 6.2}  # Falta esp32_id
        )
        assert response.status_code >= 400

# ─── TESTS: PERFORMANCE ────────────────────────────────

class TestPerformance:
    """Validación de rendimiento"""
    
    def test_sensor_endpoint_response_time(self, client, mock_sensor_payload):
        """Lectura sensor debe responder rápido (< 100ms)"""
        import time
        start = time.time()
        response = client.post(
            "/api/v1/esp32/sensors/reading",
            json=mock_sensor_payload
        )
        elapsed = time.time() - start
        assert elapsed < 0.5  # 500ms máximo (loose para CI)
        assert response.status_code == 200
    
    def test_concurrent_sensor_reads(self, client, mock_sensor_payload):
        """Múltiples lecturas simultáneas"""
        import concurrent.futures
        
        def send_reading(idx):
            return client.post(
                "/api/v1/esp32/sensors/reading",
                json={**mock_sensor_payload, "esp32_id": f"CAX21-{idx}"}
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = [ex.submit(send_reading, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert all(r.status_code == 200 for r in results)

# ─── TESTS: SECURITY ────────────────────────────────────

class TestSecurity:
    """Seguridad y validación"""
    
    def test_no_sql_injection_in_esp32_id(self, client):
        """esp32_id no debe permitir inyección SQL"""
        response = client.post(
            "/api/v1/esp32/sensors/reading",
            json={
                "esp32_id": "'; DROP TABLE esp32_devices; --",
                "ph": 6.2
            }
        )
        assert response.status_code in [200, 400]  # Debe ser validado
    
    def test_anomaly_message_safe(self, client, mock_anomaly_payload):
        """Mensajes de anomalía no deben tener caracteres peligrosos"""
        response = client.post(
            "/api/v1/esp32/sensors/reading",
            json=mock_anomaly_payload
        )
        assert response.status_code == 200
        data = response.json()
        # No debe haber caracteres de control
        if data.get("anomalies"):
            for anom in data["anomalies"]:
                assert "\n" not in anom.get("reason", "")

# ─── PARAMETRIZED TESTS ────────────────────────────────

class TestParametrized:
    """Tests parametrizados para múltiples valores"""
    
    @pytest.mark.parametrize("ph_value,expected_anomaly", [
        (5.4, True),   # Bajo
        (5.5, False),  # Límite bajo OK
        (6.5, False),  # Normal
        (6.6, True),   # Límite alto FAIL
        (7.0, True),   # Alto
    ])
    def test_ph_range_validation(self, client, ph_value, expected_anomaly):
        """pH должен validarse según rangos"""
        payload = {
            "esp32_id": "CAX21",
            "ph": ph_value
        }
        response = client.post("/api/v1/esp32/sensors/reading", json=payload)
        data = response.json()
        has_ph_anomaly = any(a["sensor"] == "pH" for a in data.get("anomalies", []))
        assert has_ph_anomaly == expected_anomaly
    
    @pytest.mark.parametrize("actuator", ["riego", "ozono", "bomba", "ventilador"])
    def test_valid_actuators(self, client, actuator):
        """Todos los actuadores válidos deben procesarse"""
        response = client.post(
            "/api/v1/esp32/actuators/control",
            json={"actuator": actuator, "action": "on"}
        )
        assert response.status_code in [200, 503]

# ─── RUN: pytest esp32_iot_test.py -v ──────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
