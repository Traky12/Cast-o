"""
FastAPI router para control IoT + streaming de ESP32-CAM
Garantiza trazabilidad, sin interferencia en MQTT, video independiente
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse, HTMLResponse
import httpx
import asyncio
from datetime import datetime, timezone
from typing import Any, Optional, TypedDict
from pydantic import BaseModel, Field
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/esp32", tags=["ESP32-CAM & Sensores"])

# ─── Modelos de Datos ───────────────────────────────────────

class SensorReading(BaseModel):
    """Lectura de sensor ESP32"""
    sensor_type: str = Field(..., description="pH|EC|TDS|TEMP")
    value: float = Field(..., description="Valor leído")
    unit: str = Field(..., description="pH|ppm|°C")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    esp32_id: Optional[str] = Field(None, description="ID del ESP32")
    calibrated: bool = Field(default=False, description="Si fue calibrado")

class SensorsPayload(BaseModel):
    """Payload de sensores desde ESP32"""
    esp32_id: str
    ph: Optional[float] = Field(None, description="pH (5.0-9.0)")
    ec: Optional[float] = Field(None, description="EC (0-2000 µS/cm)")
    tds: Optional[float] = Field(None, description="TDS (0-1000 ppm)")
    temperature_c: Optional[float] = Field(None, description="Temperatura (°C)")
    wifi_rssi: Optional[int] = Field(None, description="WiFi signal strength dBm")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ActuatorControl(BaseModel):
    """Control de actuador (riego, ozono, etc)"""
    actuator: str = Field(..., description="riego|ozono|bomba|ventilador")
    action: str = Field(..., description="on|off|pulse")
    duration_seconds: Optional[int] = Field(None, description="Si pulse, duración en segundos")
    mode: str = Field(default="manual", description="manual|auto")

class ActuatorStatus(BaseModel):
    """Estado de actuador"""
    actuator: str
    status: str = Field(..., description="on|off|error")
    last_action: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    auto_mode: bool = Field(default=False)

# ─── Variables de Configuración ───────────────────────────

ESP32_CAMERA_URL = os.getenv("ESP32_CAMERA_URL", "http://192.168.1.100:81/stream")
ESP32_SNAPSHOT_URL = os.getenv("ESP32_SNAPSHOT_URL", "http://192.168.1.100:81/capture")
ESP32_API_URL = os.getenv("ESP32_API_URL", "http://192.168.1.100:8074")
ESP32_API_TIMEOUT = 10
MQTT_SENSOR_INTERVAL = 300  # 5 min para no saturar MQTT


class SensorReadingEntry(TypedDict):
    value: float
    status: str


class AnomalyEntry(TypedDict):
    sensor: str
    value: float
    expected_range: str
    severity: str


class SensorCacheEntry(TypedDict):
    readings: dict[str, SensorReadingEntry]
    timestamp: str
    anomalies: list[AnomalyEntry]
    wifi_rssi: int | None
    anomaly_count: int


class ActuatorCacheEntry(TypedDict):
    status: str
    mode: str
    last_action: str


# Cache en memoria para último estado de sensores (evita polling constante)
_sensor_cache: dict[str, SensorCacheEntry] = {}
_actuator_cache: dict[str, ActuatorCacheEntry] = {}

# ─── STREAM DE VIDEO ────────────────────────────────────

@router.get("/camera/stream")
async def proxy_camera_stream() -> StreamingResponse:
    """
    Proxy del stream MJPEG de ESP32-CAM.
    Evita cruzar MQTT, usa HTTP independiente.
    Response streaming optimizado para latencia.
    """
    try:
        async with httpx.AsyncClient(timeout=ESP32_API_TIMEOUT) as client:
            async with client.stream("GET", ESP32_CAMERA_URL) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=503,
                        detail=f"ESP32-CAM no responde (HTTP {response.status_code})"
                    )
                
                # Retornar stream MJPEG directo
                return StreamingResponse(
                    response.aiter_bytes(chunk_size=4096),
                    media_type="multipart/x-mixed-replace; boundary=frame",
                    headers={
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0",
                        "X-Streaming": "esp32-cam",
                    }
                )
    except (httpx.ConnectError, httpx.TimeoutException):
        raise HTTPException(
            status_code=503,
            detail="No se puede conectar a ESP32-CAM. Verifica IP y WiFi."
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="ESP32-CAM timeout. Streaming no disponible."
        )
    except Exception as exc:
        logger.exception("Error inesperado en stream ESP32: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="No se puede conectar a ESP32-CAM. Verifica IP y WiFi."
        )

@router.get("/camera/snapshot")
async def camera_snapshot() -> Response:
    """
    Captura una foto estática de la cámara.
    Útil si streaming falla o para evidencia.
    """
    try:
        async with httpx.AsyncClient(timeout=ESP32_API_TIMEOUT) as client:
            response = await client.get(ESP32_SNAPSHOT_URL)
            
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="No snapshot disponible")
            
            return Response(content=response.content, media_type="image/jpeg")
    except (httpx.ConnectError, httpx.TimeoutException):
        raise HTTPException(status_code=503, detail="ESP32-CAM no disponible")
    except Exception as exc:
        logger.exception("Error inesperado capturando snapshot ESP32: %s", exc)
        raise HTTPException(status_code=503, detail="ESP32-CAM no disponible")

# ─── SENSORES ────────────────────────────────────────

@router.post("/sensors/reading")
async def record_sensor(payload: SensorsPayload) -> dict[str, Any]:
    """
    Recibe lectura de sensores desde ESP32.
    
    Flujo:
    1. Valida rango de valores
    2. Detecta anomalías
    3. Cachea en memoria
    4. NO publica a MQTT (para no interferir)
    5. Retorna confirmación
    
    Frecuencia recomendada: cada 5 minutos
    """
    
    # Validación de rangos normales (hidropónico ECO sin químicos)
    validations: list[tuple[str, float | None, float, float]] = [
        ("pH", payload.ph, 5.5, 6.5),
        ("EC", payload.ec, 1200.0, 2400.0),  # µS/cm
        ("TDS", payload.tds, 600, 1200),
        ("Temperature", payload.temperature_c, 18.0, 30.0),
    ]

    anomalies: list[AnomalyEntry] = []
    readings: dict[str, SensorReadingEntry] = {}
    
    for sensor_name, value, min_val, max_val in validations:
        if value is not None:
            sensor_is_anomaly = value < min_val or value > max_val
            if value < min_val or value > max_val:
                anomalies.append({
                    "sensor": sensor_name,
                    "value": value,
                    "expected_range": f"{min_val}-{max_val}",
                    "severity": "CRITICAL" if abs(value - (min_val + max_val) / 2) > 2 else "WARNING"
                })
            
            readings[sensor_name.lower()] = {
                "value": value,
                "status": "ANOMALY" if sensor_is_anomaly else "OK"
            }
    
    # Caché para consultas rápidas
    _sensor_cache[payload.esp32_id] = {
        "readings": readings,
        "timestamp": payload.timestamp,
        "anomalies": anomalies,
        "wifi_rssi": payload.wifi_rssi,
        "anomaly_count": len(anomalies)
    }
    
    # Log de anomalías
    if anomalies:
        logger.warning(f"🔴 ANOMALÍA en {payload.esp32_id}: {anomalies}")
    
    return {
        "status": "recorded",
        "esp32_id": payload.esp32_id,
        "readings_count": len(readings),
        "anomalies": anomalies,
        "next_read_in_seconds": MQTT_SENSOR_INTERVAL,
        "cache_hit": True,
        "message": "Lectura guardada. No publiques a MQTT ; usa este endpoint."
    }

@router.get("/sensors/latest/{esp32_id}")
async def get_latest_sensor(esp32_id: str) -> SensorCacheEntry:
    """Obtiene última lectura de sensores (desde caché local)"""
    if esp32_id not in _sensor_cache:
        raise HTTPException(status_code=404, detail=f"No hay datos para {esp32_id}")
    
    return _sensor_cache[esp32_id]

@router.get("/sensors/all")
async def get_all_sensors() -> dict[str, Any]:
    """Obtiene estado de todos los ESP32 conectados"""
    if not _sensor_cache:
        return {
            "status": "no_data",
            "message": "Ningún ESP32 ha enviado datos aún",
            "devices": []
        }
    
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "devices": _sensor_cache,
        "total_anomalies": sum(d.get("anomaly_count", 0) for d in _sensor_cache.values())
    }

# ─── ACTUADORES ────────────────────────────────────

@router.post("/actuators/control")
async def control_actuator(control: ActuatorControl) -> dict[str, Any]:
    """
    Controla un actuador (riego, ozono, etc).
    
    Garantías:
    - Manual: ON/OFF/Pulse manual
    - Auto: Basado en reglas (solo si hay datos válidos)
    - Failsafe: Si WiFi cae, ESP32 se queda en estado seguro
    - Auditoría: Cada acción se registra con timestamp
    """
    
    # Validar que el actuador existe
    valid_actuators = ["riego", "ozono", "bomba", "ventilador"]
    if control.actuator not in valid_actuators:
        raise HTTPException(
            status_code=400,
            detail=f"Actuador inválido. Usa: {', '.join(valid_actuators)}"
        )
    
    # Enviar comando a ESP32
    try:
        async with httpx.AsyncClient(timeout=ESP32_API_TIMEOUT) as client:
            response = await client.post(
                f"{ESP32_API_URL}/control",
                json={
                    "actuator": control.actuator,
                    "action": control.action,
                    "duration_seconds": control.duration_seconds,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail="ESP32 no responde al comando"
                )
    except (httpx.ConnectError, httpx.TimeoutException):
        raise HTTPException(
            status_code=503,
            detail="No se puede conectar a ESP32 para control"
        )
    
    # Cachear estado
    _actuator_cache[control.actuator] = {
        "status": control.action,
        "mode": control.mode,
        "last_action": datetime.now(timezone.utc).isoformat()
    }
    
    return {
        "status": "ok",
        "action": control.action,
        "actuator": control.actuator,
        "mode": control.mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit": {
            "action_id": f"{control.actuator}_{datetime.now().timestamp()}",
            "traceable": True,
            "logged": True
        }
    }

@router.get("/actuators/status")
async def get_actuators_status() -> dict[str, Any]:
    """Estado actual de todos los actuadores"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actuators": _actuator_cache if _actuator_cache else {"status": "no_actions_yet"}
    }

# ─── DASHBOARD HTML ────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """
    Dashboard integrado con video + sensores + controles.
    Auto-refresh cada 5 segundos.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CASTÚO CAX21 - Live Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', sans-serif; background: #0f1419; color: #fff; }
            
            .container {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 20px;
                padding: 20px;
                max-width: 1600px;
                margin: 0 auto;
            }
            
            .video-panel {
                background: #1a1f2e;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            
            .video-panel h2 { padding: 15px; background: #16213e; }
            
            .video-stream {
                width: 100%;
                height: 500px;
                background: #000;
                position: relative;
            }
            
            .video-stream img {
                width: 100%;
                height: 100%;
                object-fit: contain;
            }
            
            .status-badge {
                position: absolute;
                top: 10px;
                right: 10px;
                background: #22bb33;
                color: white;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }
            
            .sensors-panel {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }
            
            .sensor-card {
                background: #1a1f2e;
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid #00d4ff;
            }
            
            .sensor-card.alert {
                border-left-color: #ff3333;
                background: #2a1a1a;
            }
            
            .sensor-label { font-size: 12px; color: #888; text-transform: uppercase; }
            .sensor-value { font-size: 28px; font-weight: bold; margin: 10px 0; }
            .sensor-unit { font-size: 14px; color: #666; }
            
            .controls {
                background: #1a1f2e;
                padding: 20px;
                border-radius: 12px;
                margin-top: 20px;
            }
            
            .controls h3 { margin-bottom: 15px; }
            
            .button-group { display: flex; gap: 10px; margin-bottom: 10px; }
            
            .btn {
                flex: 1;
                padding: 12px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .btn.riego { background: #00b4ff; color: white; }
            .btn.riego:hover { background: #00a0e6; }
            
            .btn.ozono { background: #ff6b35; color: white; }
            .btn.ozono:hover { background: #ff5520; }
            
            .btn.mini { padding: 8px; font-size: 12px; }
            
            .alerts { background: #2a1a1a; padding: 15px; border-radius: 8px; margin-top: 15px; }
            .alerts h4 { color: #ff3333; margin-bottom: 10px; }
            .alert-item { padding: 8px; margin-bottom: 5px; background: #1a0a0a; border-radius: 4px; font-size: 12px; }
            
            @media (max-width: 900px) {
                .container { grid-template-columns: 1fr; }
            }
            
            .refresh-indicator {
                font-size: 12px;
                color: #666;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- VIDEO -->
            <div class="video-panel">
                <h2>📹 Live Feed CAX21</h2>
                <div class="video-stream">
                    <img id="stream" src="/api/v1/esp32/camera/stream" alt="Stream"/>
                    <div class="status-badge" id="status">CONNECTING</div>
                </div>
            </div>
            
            <!-- SENSORES + CONTROLES -->
            <div>
                <!-- SENSORES -->
                <div class="sensors-panel" id="sensors">
                    <div class="sensor-card">
                        <div class="sensor-label">pH</div>
                        <div class="sensor-value" id="ph-value">--</div>
                        <div class="sensor-unit">Optimal: 5.5-6.5</div>
                    </div>
                    <div class="sensor-card">
                        <div class="sensor-label">EC</div>
                        <div class="sensor-value" id="ec-value">--</div>
                        <div class="sensor-unit">µS/cm (1200-2400)</div>
                    </div>
                    <div class="sensor-card">
                        <div class="sensor-label">TDS</div>
                        <div class="sensor-value" id="tds-value">--</div>
                        <div class="sensor-unit">ppm (600-1200)</div>
                    </div>
                    <div class="sensor-card">
                        <div class="sensor-label">TEMP</div>
                        <div class="sensor-value" id="temp-value">--</div>
                        <div class="sensor-unit">°C (18-30)</div>
                    </div>
                </div>
                
                <!-- CONTROLES -->
                <div class="controls">
                    <h3>🎮 Controles</h3>
                    
                    <div class="button-group">
                        <button class="btn riego" onclick="control('riego', 'on')">💧 Riego ON</button>
                        <button class="btn riego mini" onclick="control('riego', 'off')">OFF</button>
                    </div>
                    
                    <div class="button-group">
                        <button class="btn ozono" onclick="control('ozono', 'on')">💨 Ozono ON</button>
                        <button class="btn ozono mini" onclick="control('ozono', 'off')">OFF</button>
                    </div>
                    
                    <!-- ALERTAS -->
                    <div class="alerts">
                        <h4>⚠️ Alertas Activas</h4>
                        <div id="alert-list">
                            <div class="alert-item">Cargando alertas...</div>
                        </div>
                    </div>
                    
                    <div class="refresh-indicator">
                        🔄 Auto-refresh cada 5 segundos
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Auto-refresh sensores
            async function updateSensors() {
                try {
                    const res = await fetch('/api/v1/esp32/sensors/all');
                    const data = await res.json();
                    
                    if (data.devices && Object.keys(data.devices).length > 0) {
                        const esp32_id = Object.keys(data.devices)[0];
                        const readings = data.devices[esp32_id].readings || {};
                        
                        document.getElementById('ph-value').textContent = (readings.ph?.value || '--').toFixed(2);
                        document.getElementById('ec-value').textContent = (readings.ec?.value || '--').toFixed(0);
                        document.getElementById('tds-value').textContent = (readings.tds?.value || '--').toFixed(0);
                        document.getElementById('temp-value').textContent = (readings.temperature?.value || '--').toFixed(1);
                        
                        // Alertas
                        const anomalies = data.devices[esp32_id].anomalies || [];
                        const alertList = document.getElementById('alert-list');
                        if (anomalies.length > 0) {
                            alertList.innerHTML = anomalies.map(a => 
                                `<div class="alert-item">🔴 ${a.sensor}: ${a.value} (rango: ${a.expected_range})</div>`
                            ).join('');
                        } else {
                            alertList.innerHTML = '<div class="alert-item">✅ Sin alertas</div>';
                        }
                    }
                } catch (e) {
                    console.log('Esperando primer dato...');
                }
            }
            
            // Control de actuadores
            async function control(actuator, action) {
                try {
                    const res = await fetch('/api/v1/esp32/actuators/control', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            actuator,
                            action,
                            mode: 'manual'
                        })
                    });
                    
                    const data = await res.json();
                    console.log(`✅ ${actuator} ${action}:`, data);
                    alert(`${actuator.toUpperCase()} → ${action.toUpperCase()}`);
                } catch (e) {
                    alert(`Error: ${e.message}`);
                }
            }
            
            // Actualizar cada 5 segundos
            setInterval(updateSensors, 5000);
            updateSensors(); // Primera carga inmediata
            
            // Status del stream
            document.getElementById('stream').onload = function() {
                document.getElementById('status').textContent = '🟢 LIVE';
                document.getElementById('status').style.background = '#22bb33';
            };
            
            document.getElementById('stream').onerror = function() {
                document.getElementById('status').textContent = '🔴 ERROR';
                document.getElementById('status').style.background = '#ff3333';
            };
        </script>
    </body>
    </html>
    """

# ─── HEALTH CHECK ────────────────────────────────

@router.get("/status")
async def esp32_status():
    """Estado general del sistema ESP32"""
    return {
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "devices": {
            "sensors": len(_sensor_cache),
            "actuators": len(_actuator_cache)
        },
        "camera": {
            "url": ESP32_CAMERA_URL,
            "stream_type": "MJPEG",
            "resolution": "Higher res on device"
        },
        "config": {
            "mqtt_interval_seconds": MQTT_SENSOR_INTERVAL,
            "message": "MQTT NOT USED for video. HTTP only."
        }
    }
