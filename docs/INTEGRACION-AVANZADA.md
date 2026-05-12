# CASTUO-SYSTEM™ — Plan de integración avanzada

Robótica agrícola, tokenización de activos, materiales compuestos, modo offline 72h y capa de seguridad (FHSS, red privada).

## 1. Robótica agrícola autónoma

- **Odoo**: modelo `castu.robot` (tipo: deshierbe, poda, cosecha). Acciones: Iniciar Patrulla, Detener.
- **Backend**: `POST /robotica/command` recibe `robot_id`, `command`, `params` y publica en MQTT `castuo/robot/{id}/command`.
- **Flujo**: Odoo → FastAPI → MQTT → Antenas Conquistadoras (LoRaWAN/5G) → Robot (Raspberry Pi + Arduino).

Variables: `MQTT_HOST`, `MQTT_PORT` para el broker.

## 2. Tokenización de activos (red privada)

- **Odoo**: modelo `castu.asset.token` (activo = granja, oferta total, dueño, TX blockchain). Acción: Crear en Blockchain.
- **Backend**: `POST /blockchain/token/create` y `POST /blockchain/token/transfer` (stub; en producción Hyperledger Fabric).
- **Flujo**: Activo real → registro en red privada → token → wallet agricultor → mercado interno → BioCoin Castúo.

## 3. Materiales compuestos (economía circular)

- **Odoo**: modelos `castu.material.compuesto` (tipo, materia prima, stock kg, precio) y `castu.material.aplicacion` (producto final, granja destino).
- **Backend**: `POST /materiales/producir` (kg materia prima → kg compuesto) y `POST /materiales/fabricar_pieza` (kg compuesto → alas, carcasas, paneles, sensores).
- **Tipos**: hemp_composite, pla_starch, cellulose_nano, magnesium_alloy. Aplicaciones: drones, invernaderos, sensores, riego.

## 4. Modo offline (72 horas)

- **Backend**: módulo `backend/offline/` con `OfflineDB` (SQLite) y `SyncManager`.
  - `POST /offline/store`: guarda `action_type` + `payload` (ej. `activate_riego`, `robot_command`).
  - `POST /offline/sync`: ejecuta todas las pendientes contra la API (llamar cuando vuelva la red).
  - `GET /offline/pending`: lista acciones pendientes.
- **Uso**: Castuo Gate o app móvil guardan acciones sin red; un cron o el propio gate llama a `/offline/sync` al detectar conexión.

Variable: `OFFLINE_DB_PATH` (opcional). Por defecto: `data/offline.db` en la raíz del proyecto.

## 5. Seguridad (FHSS / red privada)

- **Backend**: `backend/security/fhss.py` — `FHSSManager` con secuencia de frecuencias EU868 para LoRa (stub; en producción integrar con gateway).
- **Medidas** (documentadas): saltos de frecuencia (FHSS), firmas ECDSA en MQTT, VPN (Tailscale), cifrado en reposo (Age) y tránsito (TLS 1.3), rate limiting en gateway.

## 6. Estación terrena / satélites

- Descarga directa de señales (ej. NOAA-19, SatNOGS) y procesamiento con GNU Radio / QGIS quedan como integración externa; los modelos de teledetección en Odoo (`castu.teledeteccion`) pueden alimentarse desde ese pipeline.

## Resumen de endpoints nuevos

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/robotica/command` | Comando a robot (MQTT) |
| POST | `/blockchain/token/create` | Crear token (stub) |
| POST | `/blockchain/token/transfer` | Transferir token (stub) |
| POST | `/materiales/producir` | Producir compuesto desde materia prima |
| POST | `/materiales/fabricar_pieza` | Fabricar pieza desde compuesto |
| POST | `/offline/store` | Guardar acción offline |
| POST | `/offline/sync` | Sincronizar pendientes |
| GET | `/offline/pending` | Listar pendientes |

## Menús Odoo nuevos

- **CASTUO** → Robots (robots agrícolas).
- **CASTUO** → Tokenización (tokens de activos).
- **CASTUO** → Materiales (compuestos y aplicaciones).
