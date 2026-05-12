# Piloto: Cultivo hidropónico en bandejas con CASTUO-SYSTEM

Integración de hardware físico (Raspberry Pi, sensores, actuadores) con el software existente para trazabilidad, IoT y cumplimiento normativo (RD 903/2025, GaiaChain).

## 1. Componentes físicos mínimos

| Componente | Especificaciones | Proveedor (Extremadura) | Coste aprox. (€) |
|------------|------------------|--------------------------|------------------|
| Bandejas 40x60 cm | Food-grade, drenaje, soporte sensores | Plásticos Agrícolas Sáenz (Badajoz) | 8/unidad |
| Sustrato | Fibra de coco / lana de roca (certificado) | Sustratos Ecológicos Extremadura | 0,75/unidad |
| Sistema de riego | Bomba 12V, 1–4 L/h, filtro 100 µm | Riegos del Guadiana (Mérida) | 300 |
| Depósito nutrientes | 200 L + bomba dosificadora EC/pH | Hidroponía Ibérica (Cáceres) | 500 |
| Iluminación LED | 400–700 nm, 150 µmol/m²/s | LED Agrícola Extremadura | 300/unidad |
| Sensores IoT | DHT22, MH-Z19, EC/pH, cámara RGB | Electrónica Avanzada Mérida | 150/kit |
| Raspberry Pi 4 | 4 GB RAM, Raspberry Pi OS Lite | PCBox Cáceres | 60 |
| Etiquetas RFID | Tags UHF pasivos | RFID Extremadura | 0,20/unidad |

**Total piloto básico (4 bandejas):** ~1.260 €

## 2. Integración con CASTUO-SYSTEM

### 2.1 Módulo IoT (este repositorio)

- **`iot/raspberry_pi_agent.py`**: agente para Raspberry Pi; sin hardware usa sensores simulados.
- **`iot/api_endpoints.py`**: endpoints FastAPI `POST /api/iot/data` y `POST /api/iot/auth/iot`.
- **`iot/mqtt_handler.py`**: opcional; MQTT para datos y comandos (paho-mqtt).
- **GaiaChain**: `log_iot_data`, `log_iot_auth`, `log_iot_command` en `blockchain/gaia_chain.py`.

### 2.2 Cómo montar el router IoT en el backend

El backend CASTUO ya monta el router IoT si el paquete `iot` está en la raíz del proyecto:

```bash
# Desde la raíz del proyecto (Castuo-System)
export PYTHONPATH=.
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Endpoints disponibles:

- `POST /api/iot/data` — Recibir datos de sensores (session_id, tray_id, sensors, metadata).
- `POST /api/iot/auth/iot` — Autenticar dispositivo IoT (tray_id, device_type, location).
- `GET /api/iot/devices` — Listar dispositivos (stub).

### 2.3 Ejecutar el agente en la Raspberry Pi (o en PC para pruebas)

```bash
# Instalar dependencias (opcional: qrcode, requests)
pip install requests qrcode[pil]

# Modo simulación (sin hardware)
python -m iot.raspberry_pi_agent
# O con parámetros:
python -c "
from iot import RaspberryPiIoTAgent
agent = RaspberryPiIoTAgent(
    api_endpoint='http://TU_SERVIDOR:8000/api/iot',
    tray_id='CASTUO-TRAY-001',
    auth_token='TU_TOKEN',
)
agent.run(interval=300)  # cada 5 minutos
"
```

### 2.4 Integración con otros módulos

| Módulo | Uso en el piloto |
|--------|-------------------|
| **ProfileManager** | Sesión del agente como TECHNICIAN (opcional). |
| **GaiaChain** | Registro de datos IoT, auth y comandos. |
| **AuditSystem** | Registro de interacciones del agente. |
| **DroneTraceabilitySystem** | Trazabilidad de bandejas (ID por bandeja, QR/RFID). |
| **LocalProductionSystem** | Órdenes de producción de bandejas/sustrato. |

## 3. Protocolo de prueba (4 semanas)

- **Semana 1**: Siembra, parámetros iniciales (humedad 60–70 %, EC 1,2, pH 5,8), registro en GaiaChain y QR.
- **Semana 2**: Monitoreo vegetativo, datos cada 5 min, alertas automáticas (humedad &lt; 60 %).
- **Semana 3**: Transición a floración (luz 12h/12h), EC 1,8–2,0, registro de cambios.
- **Semana 4**: Cosecha, informe final, certificado de trazabilidad (`DroneTraceabilitySystem` / `verify_drone` adaptado a bandejas).

## 4. Métricas a demostrar

- **Trazabilidad 100 %**: Cada bandeja con registro inmutable en GaiaChain.
- **Ahorro de agua**: Reducción 30–50 % vs. cultivo tradicional (datos en GaiaChain).
- **Precisión nutrientes**: EC/pH en rango ±5 % (logs `log_iot_data`).
- **Cumplimiento**: RD 903/2025 (cannabis) o normativa hidroponía; ComplianceManager para informes.

## 5. Lista de verificación previa al piloto

### Hardware

- [ ] 4 bandejas 40x60 cm con drenaje.
- [ ] Sustrato (fibra de coco o lana de roca), 4 unidades.
- [ ] Sistema de riego (bomba 12V, emisores, filtro).
- [ ] Depósito nutrientes 200 L con dosificadora.
- [ ] Iluminación LED espectro completo.
- [ ] Sensores: DHT22, MH-Z19, EC/pH, cámara RGB.
- [ ] Raspberry Pi 4 (4 GB), Raspberry Pi OS Lite.
- [ ] Etiquetas RFID por bandeja.

### Software

- [ ] CASTUO-SYSTEM desplegado con módulos iot, blockchain, production.
- [ ] Endpoints IoT (`/api/iot/data`, `/api/iot/auth/iot`) accesibles.
- [ ] Agente IoT instalado en la Raspberry Pi (o ejecutable en PC en modo simulación).
- [ ] Perfiles TECHNICIAN y FARMER configurados en ProfileManager.
- [ ] Alertas configuradas (temperatura 18–28 °C, humedad, EC/pH).

### Configuración inicial

- [ ] Bandejas registradas en GaiaChain (p. ej. vía DroneTraceabilitySystem / producción).
- [ ] Códigos QR generados por bandeja (agente o script).
- [ ] Parámetros iniciales en el agente: etapa "vegetative", rangos temp/humedad/EC/pH.
- [ ] Prueba de conexión Raspberry Pi ↔ CASTUO-SYSTEM.

## 6. Referencia rápida de código

### Registrar bandejas en trazabilidad (ejemplo)

```python
from datetime import datetime
from blockchain.gaia_chain import GaiaChainClient
from production.drone_traceability import DroneTraceabilitySystem

traceability = DroneTraceabilitySystem(gaiachain_client=GaiaChainClient())
for i in range(1, 5):
    traceability.register_manufacturing(
        product_id="CASTUO-TRAY-001",
        components=[
            {"component_id": f"SUBSTRATE-{datetime.now().strftime('%Y%m%d')}-{i:03d}",
             "type": "Fibra de coco", "supplier": "Sustratos Ecológicos Extremadura",
             "batch": f"BATCH-{datetime.now().strftime('%Y%m%d')}", "certification": ["ISO 9001", "EcoCert"]},
            {"component_id": f"NUTRIENTS-{datetime.now().strftime('%Y%m%d')}-{i:03d}",
             "type": "Nutrientes hidropónicos", "supplier": "Hidroponía Ibérica",
             "batch": f"NUT-{datetime.now().strftime('%Y%m%d')}", "certification": ["ISO 22000"]}
        ],
        quality_checks=[
            {"check_id": f"QC-{datetime.now().strftime('%Y%m%d')}-{i:03d}-01",
             "type": "Esterilidad del sustrato", "result": "passed",
             "standard": "ISO 11135", "timestamp": datetime.now().isoformat()}
        ]
    )
```

### Enviar datos IoT desde Python (ejemplo)

```python
import requests

r = requests.post(
    "http://localhost:8000/api/iot/data",
    json={
        "session_id": "dev-session-001",
        "tray_id": "CASTUO-TRAY-001",
        "timestamp": "2026-03-12T10:00:00",
        "sensors": {"temperature": 22.5, "humidity": 65, "co2": 500, "ec": 1.4, "ph": 5.9},
        "metadata": {"growth_stage": "Vegetativo", "location": "Cáceres"},
    },
)
print(r.json())  # Incluye gaiachain_tx y commands (water_pump, grow_light, alert si aplica)
```

## 7. Próximos pasos después del piloto

- Escalar a 20–50 bandejas con el mismo sistema.
- Integrar drones (EuropeanDroneCoordinator) para fumigación o monitoreo.
- Automatizar siembra/cosecha (robots).
- Certificaciones: ISO 9001, ISO 27001, certificación ecológica UE.
