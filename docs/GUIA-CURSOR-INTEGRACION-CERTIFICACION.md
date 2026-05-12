# Guía completa para Cursor: integración y certificación

Enfoque en conectar equipos externos, probar flujos reales y generar evidencia para certificación (ISO, AEMPS, RD 903/2025).

## 1. Estructura del proyecto en Cursor

En este repositorio los módulos están en la **raíz** del workspace; el backend FastAPI está en `backend/` e importa los paquetes de la raíz cuando `PYTHONPATH` incluye la raíz:

```
Castuo-System/
├── backend/              # FastAPI (main.py, routers, agents)
├── blockchain/           # GaiaChain (gaia_chain.py)
├── core/                 # profile_engine, response_engine, audit_system
├── iot/                  # raspberry_pi_agent, api_endpoints, mqtt_handler
├── messaging/            # european_drone_network, european_drone_coordinator
├── production/           # drone_traceability, local_production_system
├── interfaces/           # sabionda_master_interface
├── scripts/              # tests e informes
│   ├── test_gaia_chain.py
│   ├── test_cross_border_mission.py
│   ├── test_sabionda_master.py
│   ├── test_iot_integration.py
│   └── generate_certification_reports.py
├── docs/
├── .vscode/
│   ├── launch.json       # Configuraciones de depuración
│   └── tasks.json        # Tareas (instalar deps, tests, informes)
└── .env
```

Para que el backend cargue el router IoT y el resto de módulos, arrancar con:

```bash
PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 2. Configuración en Cursor

### 2.1 Depuración (launch.json)

En `.vscode/launch.json` hay configuraciones para:

- **Python: FastAPI Backend** – arranca uvicorn con `PYTHONPATH=${workspaceFolder}`.
- **Frontend: Next.js** – si existe `frontend/`, arranca `npm run dev`.
- **IoT Agent (Simulator)** – ejecuta `iot/raspberry_pi_agent.py` en modo simulación.
- **Test: GaiaChain** – ejecuta `scripts/test_gaia_chain.py`.
- **Test: Cross-Border Mission** – ejecuta `scripts/test_cross_border_mission.py`.
- **Test: Sabionda Master** – ejecuta `scripts/test_sabionda_master.py`.
- **Test: Backend (pytest)** – ejecuta pytest sobre `backend/tests/`.

### 2.2 Tareas (tasks.json)

Tareas disponibles:

- **Install Backend Dependencies** – `pip install -r backend/requirements.txt`
- **Install Frontend Dependencies** – `npm install` en `frontend/`
- **Start MQTT Broker** – `mosquitto -v` (en segundo plano)
- **Run IoT Agent** – agente IoT en segundo plano
- **Run Tests (Backend)** – pytest en `backend/tests/`
- **Run Test GaiaChain** – `python scripts/test_gaia_chain.py`
- **Run Test Cross-Border Mission** – `python scripts/test_cross_border_mission.py`
- **Generate Certification Reports** – `python scripts/generate_certification_reports.py`

## 3. Integración con GaiaChain

El cliente actual (`blockchain/gaia_chain.py`) es un **stub** que registra eventos en memoria (sin Ganache/Web3). Para probar los métodos desde Cursor:

1. Abre `scripts/test_gaia_chain.py`.
2. Ejecútalo con F5 (configuración "Test: GaiaChain") o desde terminal:
   ```bash
   cd Castuo-System
   set PYTHONPATH=.
   python scripts/test_gaia_chain.py
   ```

Se comprueban: `log_cross_border_proposal`, `get_cross_border_mission`, `log_smart_contract`, `get_smart_contract`, `log_cross_border_acceptance`, `log_iot_data`, `log_iot_auth`.

## 4. Coordinador transfronterizo

Para probar el flujo completo de una misión (propuesta → aceptación → inicio → completado):

1. Ejecuta **Test: Cross-Border Mission** desde Cursor (F5) o:
   ```bash
   PYTHONPATH=. python scripts/test_cross_border_mission.py
   ```
2. Verás en consola: propuesta España→Portugal, aceptación por PT-ALG-001, inicio, telemetría y completado, estado final y estadísticas de la red.

Los eventos se registran en el cliente GaiaChain (stub) usado por el coordinador.

## 5. Interfaz master SABIONDA

Para probar visión general, versiones, producción, misiones e informes:

1. Ejecuta **Test: Sabionda Master** o:
   ```bash
   PYTHONPATH=. python scripts/test_sabionda_master.py
   ```
2. Se comprueban: `get_system_overview`, `manage_versions` (list/create), `monitor_production`, `create_drone_manufacturing_order`, `manage_european_missions` (propose), `generate_strategic_report`, `execute_strategic_action` (expand_market).

## 6. Integración IoT

### 6.1 Envío por HTTP (sin MQTT)

Con el backend en marcha en el puerto 8000:

```bash
PYTHONPATH=. python scripts/test_iot_integration.py
```

El script obtiene un `session_id` vía `POST /api/iot/auth/iot` y envía varias lecturas a `POST /api/iot/data`. La respuesta incluye `gaiachain_tx` y `commands` (riego, luz, alertas).

### 6.2 Agente en Raspberry Pi (o simulador)

En la raíz del proyecto:

```bash
PYTHONPATH=. python -m iot.raspberry_pi_agent
```

O con parámetros desde código: `RaspberryPiIoTAgent(api_endpoint="http://localhost:8000/api/iot", tray_id="CASTUO-TRAY-001").run(interval=300)`.

Sin hardware, el agente usa sensores simulados.

## 7. Generar evidencia para certificación

Para generar los informes en `reports/`:

1. Ejecuta la tarea **Generate Certification Reports** o:
   ```bash
   PYTHONPATH=. python scripts/generate_certification_reports.py
   ```
2. Se generan:
   - `reports/production_certification.json`
   - `reports/security_certification.json`
   - `reports/compliance_certification.json`
   - `reports/european_network_report.json`
   - `reports/SUMMARY_CERTIFICATION.md` (resumen ejecutivo en Markdown)

El resumen incluye métricas de producción, red europea, seguridad, cumplimiento normativo e impacto ambiental, y referencias a los JSON anteriores.

## 8. Checklist para demo en vivo

| Paso | Acción | Evidencia |
|------|--------|-----------|
| 1 | Iniciar backend (y opcionalmente frontend/MQTT) | Logs en terminal |
| 2 | Ejecutar `test_iot_integration.py` (HTTP) | Respuestas con `gaiachain_tx` y `commands` |
| 3 | Simular alerta (p. ej. humedad &lt; 60% en payload) | `commands` con `water_pump: 1` y/o `alert` |
| 4 | Ejecutar `test_cross_border_mission.py` | Flujo completo y logs GaiaChain |
| 5 | Ejecutar `generate_certification_reports.py` | Archivos en `reports/` y `SUMMARY_CERTIFICATION.md` |
| 6 | Revisar cumplimiento | Tabla en `compliance_certification.json` y en el resumen |
| 7 | Revisar seguridad | `security_dashboard` vía Sabionda Master / informes |
| 8 | Escalabilidad | Documentación en `docs/ARQUITECTURA-SABIONDA-CASTUO-SYSTEM.md` y piloto hidropónico |

## 9. Próximos pasos para producción

1. **Despliegue**: Usar `docker-compose` para backend, frontend y MQTT; en producción restringir CORS y usar HTTPS.
2. **Hardware real**: Conectar sensores y actuadores a Raspberry Pi y apuntar el agente al API en producción.
3. **Certificaciones**: Entregar los informes de `reports/` y `SUMMARY_CERTIFICATION.md` a un organismo acreditado (p. ej. TÜV SÜD, AENOR).
4. **Escalar**: Aumentar bandejas, drones y operadores; monitorear con los mismos flujos (IoT, misiones, informes).

---

Con esta guía puedes **integrar equipos externos**, **probar flujos reales** (GaiaChain, coordinador, SABIONDA, IoT) y **generar evidencia para certificación** desde Cursor usando los scripts y la configuración descritos.
