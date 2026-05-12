# CASTÚO-SYSTEM™ API v3.1 — Referencia de Endpoints

Base URL: `https://api.castuo-system.cloud`

Autenticación: `Authorization: Bearer <JWT>` (HS256, roles: `admin | editor | api`)

Generar token de prueba:
```bash
python3 -c "
import jwt, time
print(jwt.encode({'sub':'operador','role':'editor','exp':int(time.time())+3600}, 'TU_JWT_SECRET', algorithm='HS256'))
"
```

---

## Sistema

### GET /health

Estado del sistema. **Sin autenticación.**

**Respuesta 200:**
```json
{
  "status": "ok",
  "service": "castuo-api",
  "version": "3.1.0",
  "chain_status": "disabled | ready | misconfigured",
  "neuromorphic_lab": false,
  "timestamp": "2026-04-01T10:00:00+00:00"
}
```

| Campo | Descripción |
|-------|-------------|
| `chain_status` | `disabled` = blockchain no activada; `ready` = configurada y operativa; `misconfigured` = faltan variables |
| `neuromorphic_lab` | Activado con `CASTUO_NEUROMORPHIC_LAB=1` |

---

## Skills — Trazabilidad

### POST /api/v1/skills/validar_lote

Registra un lote agrícola en GaiaChain, genera certificado PDF y QR de trazabilidad.

**Auth:** roles `admin | editor | api`

**Request:**
```json
{
  "lote_id": "LOTE-2026-001",
  "metadatos": {
    "cultivo": "cannabis_medicinal",
    "humedad_pct": 12.3,
    "thc_pct": 0.18,
    "cbd_pct": 8.5,
    "kg_cosechados": 45.2,
    "fecha_cosecha": "2026-04-01",
    "ubicacion": "Dehesa de Cáceres, parcela 42",
    "eco": true,
    "aemps_expediente": "EC-2026-0042"
  },
  "verify_base_url": "https://verify.castuo360.eu/lote",
  "output_dir": "/data/lotes"
}
```

| Campo | Tipo | Req | Descripción |
|-------|------|-----|-------------|
| `lote_id` | string | ✅ | Identificador único (min 3 chars) |
| `metadatos` | object | — | Datos del lote (libre) |
| `firma_digital` | string | — | JWT del operador para trazabilidad |
| `verify_base_url` | string | — | Base URL para el QR (default: `https://verify.castuo360.eu/lote`) |
| `output_dir` | string | — | Directorio de salida para PDF/QR |

**Respuesta 200:**
```json
{
  "status": "OK",
  "lote_id": "LOTE-2026-001",
  "tx_hash": "0xabc123...",
  "blockchain": "GaiaChain",
  "certificado_path": "/data/lotes/LOTE-2026-001_cert.pdf",
  "qr_path": "/data/lotes/LOTE-2026-001_qr.png",
  "generado_en": "2026-04-01T10:00:00+00:00"
}
```

| Campo | Valores | Descripción |
|-------|---------|-------------|
| `status` | `OK` / `FALLBACK` | `OK` = TX real en GaiaChain; `FALLBACK` = simulado (sin nodo) |
| `blockchain` | `GaiaChain` / `simulado` | Backend blockchain utilizado |
| `tx_hash` | `0x...` / `sim-...` | Hash de transacción |

**Errores:**
| Código | Causa |
|--------|-------|
| 401 | Sin cabecera Authorization |
| 403 | Rol no autorizado |
| 422 | `lote_id` ausente o menor de 3 chars |

---

## IA Predictiva

### POST /api/v1/ai/predict

Análisis predictivo agronómico con Mistral AI (fallback a reglas locales).

**Auth:** roles `admin | editor | api`

**Request:**
```json
{
  "tipo": "yield_prediction",
  "cultivo": "lechuga",
  "datos": {
    "humedad_pct": 68,
    "temperatura_c": 22,
    "radiacion_par": 420
  },
  "consulta_libre": "¿Cómo mejorar el rendimiento esta semana?"
}
```

| `tipo` | Descripción | Campos `datos` recomendados |
|--------|-------------|----------------------------|
| `yield_prediction` | Rendimiento esperado (kg/m²) | `humedad_pct`, `temperatura_c`, `radiacion_par` |
| `anomaly_detection` | Anomalías en sensores IoT | `humedad_pct`, `temperatura_c`, `ph`, `co2_ppm`, `ec_ms_cm` |
| `irrigation_advice` | Consejo de riego | `tension_matricial_cb`, `humedad_pct`, `temperatura_c` |
| `livestock_health` | Salud animal | `especie`, `temperatura_c`, `peso_kg` |

**Respuesta 200 — yield_prediction:**
```json
{
  "tipo": "yield_prediction",
  "resultado": {
    "ici": 0.923,
    "kg_m2_estimado": 4.15,
    "kg_m2_optimo": 4.5,
    "eficiencia_pct": 92.3,
    "factores": {
      "humedad_score": 0.957,
      "temperatura_score": 1.0,
      "radiacion_score": 0.84
    }
  },
  "proveedor_ia": "mistral-ai",
  "modelo": "mistral-large-latest",
  "confianza": 0.923,
  "recomendacion": "Condiciones óptimas. Mantener parámetros actuales.",
  "generado_en": "2026-04-01T10:00:00+00:00"
}
```

**Respuesta 200 — anomaly_detection:**
```json
{
  "tipo": "anomaly_detection",
  "resultado": {
    "anomalias_detectadas": 1,
    "anomalias": [
      { "sensor": "temperatura_c", "valor": 55, "limite": 40, "tipo": "alto" }
    ],
    "estado": "ALERTA"
  },
  "proveedor_ia": "reglas-locales",
  "modelo": "castuo-rules-v1",
  "confianza": 0.95,
  "recomendacion": "Se detectaron 1 anomalía(s). Revisar sensores afectados.",
  "generado_en": "2026-04-01T10:00:00+00:00"
}
```

---

## Orquestador

### GET /api/v1/orchestrator/status

Estado de todos los servicios del ecosistema CASTÚO en paralelo.

**Auth:** no requerida

**Respuesta 200:**
```json
{
  "status": "ok",
  "summary": {
    "total_services": 8,
    "healthy": 6,
    "degraded": 1,
    "unreachable": 1
  },
  "services": {
    "fastapi": { "status": "healthy", "latency_ms": 12 },
    "gaiachain": { "status": "healthy", "latency_ms": 45 },
    "ipfs": { "status": "degraded", "error": "timeout" },
    "mistral": { "status": "unreachable", "error": "API key not configured" }
  }
}
```

### POST /api/v1/orchestrator/task

Ejecuta una tarea orquestada por SABIONDA.

**Request:**
```json
{
  "task_type": "validar_lote_completo",
  "parameters": { "lote_id": "LOTE-001" }
}
```

---

## Invernadero

### GET /api/v1/invernadero/status
### POST /api/v1/invernadero/riego
### POST /api/v1/invernadero/clima

Ver router `api/routers/invernadero.py` para modelos completos.

---

## Trazabilidad QR

### POST /api/v1/qr/generar
### GET /api/v1/qr/{lote_id}
### GET /api/v1/qr/list

Ver router `api/routers/trazabilidad_qr.py` para modelos completos.

---

## Documentos Gubernamentales

| Endpoint | Documento |
|----------|-----------|
| `POST /api/v1/siex/cuaderno-campo` | SIEX Cuaderno de Campo Digital |
| `POST /api/v1/traces/certificado` | TRACES Certificado Sanitario |
| `POST /api/v1/pac/eco-esquema` | PAC 2026 Eco-esquema |
| `POST /api/v1/regepa/explotacion` | REGEPA Registro Explotación |
| `POST /api/v1/sigpac/parcelas` | SIGPAC Informe de Parcelas |
| `GET /api/v1/schemas/{schema_name}` | Esquema JSON de validación |

---

## Variables de Entorno

| Variable | Descripción | Defecto |
|----------|-------------|---------|
| `JWT_SECRET` | Secreto para firmar JWT | — (modo dev si ausente) |
| `JWT_SECRET_FILE` | Ruta a fichero con JWT secret (Opción A) | — |
| `GAIACHAIN_RPC_URL` | Nodo RPC GaiaChain | — |
| `GAIACHAIN_PRIVATE_KEY` | Clave privada para TX | — |
| `MISTRAL_API_KEY` | Clave API Mistral AI | — (reglas locales si ausente) |
| `CASTUO_ROBOTICS_LAB_CHAIN_REGISTER` | Activar blockchain (`1`/`0`) | `0` |
| `CASTUO_CORS_ORIGINS` | Orígenes CORS permitidos | `https://castuo360.eu,...` |
| `QR_REGISTRY_PATH` | Ruta JSON del registro QR | `/tmp/castuo_qr_registry.json` |
| `CASTUO_IOT_TELEMETRY_URL` | Endpoint telemetría IoT | — |
| `CASTUO_IOT_DEVICE_CMD_URL` | Endpoint comandos IoT | — |

---

## Códigos de Error

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 401 | Sin autenticación o token inválido |
| 403 | Rol insuficiente |
| 422 | Validación fallida (ver `detail`) |
| 500 | Error interno del servidor |
| 502 | Error de servicio upstream (GaiaChain, Mistral) |
