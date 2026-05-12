# Anexo TRL9 — Parametrización sin Hardcode (Zero-Leak v2)

Este anexo consolida el esquema definitivo de variables de entorno y la validación automática del workflow `zero_leak_encrypt_forward_v2`.

> Estado: el workflow del repo está parametrizado por entorno y `scripts/harden_n8n_flow.py` lo valida en TRL9.

---

## 1) Variables de Entorno Clave (URLs/credenciales centralizadas)

### 1.1 Endpoints (n8n -> backend)

Estas variables evitan edición manual dentro del JSON:

- `CASTUO_ENCRYPT_URL`  
  Endpoint de cifrado. Ejemplo: `http://api:8000/encrypt`
- `CASTUO_PQC_SIGN_URL`  
  Endpoint para firma PQC (ML-DSA). Ejemplo: `http://api:8000/api/admin/pqc/sign`
- `CASTUO_AUDIT_REGISTER_URL`  
  Endpoint para registrar evento de auditoría. Ejemplo: `http://api:8000/api/audit/register-event`
- `CASTUO_COMPLIANCE_LATEST_URL`  
  Endpoint para consistencia (último evento). Ejemplo: `http://api:8000/api/compliance/audit/latest?tokenId=0`

### 1.2 MQTT (Feedback Loop)

- `CASTUO_MQTT_BROKER`  
  Broker MQTT. Ejemplo: `mqtt://mosquitto:1883`
- `CASTUO_MQTT_USER`  
  Usuario MQTT. Ejemplo: `n8n-user`
- `CASTUO_MQTT_PASS`  
  Contraseña MQTT.

### 1.3 Autenticación Admin (para endpoints locales)

- `N8N_ADMIN_JWT`  
  Bearer token para endpoints admin/firmas/auditoría (rol `admin`).

### 1.4 Salida externa (cifrado activo)

- `ZERO_LEAK_OUT_URL`  
  URL destino externo (debe recibir `ciphertext_json` + `signature`).

### 1.5 GaiaChain

- `GAIA_CHAIN_AUDIT_CONTRACT`  
  Dirección del contrato de auditoría.
- `GAIA_CHAIN_AUDIT_ABI`  
  ABI del contrato (JSON).
- `GAIA_CHAIN_PRIVATE_KEY`  
  Clave privada (opcional para pruebas; idealmente gestionada vía Vault/HSM).

---

## 2) Estructura de Archivos (alineada al repo)

`zero_leak_encrypt_forward_v2.json` y los endpoints que usa están en:

- `n8n/workflows/zero_leak_encrypt_forward_v2.json`
- `backend/api/routes/audit.py` (registro en GaiaChain)
- `backend/api/routes/compliance_audit.py` (consistencia GET `/api/compliance/audit/latest`)
- `backend/api/config.py` (settings mínimo para GaiaChain en entorno)
- `scripts/harden_n8n_flow.py` (validación TRL9)

---

## 3) Validación TRL9 (sin bloqueos por URLs hardcodeadas)

Comando recomendado antes de activar producción:

```bash
python scripts/harden_n8n_flow.py \
  --input n8n/workflows/zero_leak_encrypt_forward_v2.json \
  --fail-on-violation
```

Qué valida:
- que los nodos de cifrado/firma/auditoría/consistencia usan `CASTUO_*_URL` y `ZERO_LEAK_OUT_URL`
- que la firma PQC referencia `N8N_ADMIN_JWT` en `headerParameters`
- que existe ruta de contingencia (Modo Isla) con patrón `tierra_firme_alert`
- que existe Feedback Loop MQTT hacia `sabionda/telemetry_anon` (warning si falta, para mantener compatibilidad)

---

## 4) Plantilla .env mínima (ejemplo copy/paste)

```ini
# Admin
N8N_ADMIN_JWT=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# MQTT
CASTUO_MQTT_BROKER=mqtt://mosquitto:1883
CASTUO_MQTT_USER=n8n-user
CASTUO_MQTT_PASS=contraseña_segura_mqtt

# Endpoints (backend FastAPI)
CASTUO_ENCRYPT_URL=http://api:8000/encrypt
CASTUO_PQC_SIGN_URL=http://api:8000/api/admin/pqc/sign
CASTUO_AUDIT_REGISTER_URL=http://api:8000/api/audit/register-event
CASTUO_COMPLIANCE_LATEST_URL=http://api:8000/api/compliance/audit/latest?tokenId=0

# Salida externa
ZERO_LEAK_OUT_URL=https://destino-seguro.example/api

# GaiaChain
GAIA_CHAIN_AUDIT_CONTRACT=0x123...abc
GAIA_CHAIN_AUDIT_ABI='{"inputs": [...], "name": "registerEvent"}'
GAIA_CHAIN_PRIVATE_KEY=0x4f3...
```

---

## 5) Nota de despliegue (Hetzner)

En Hetzner, el stack final puede ser `docker-compose.hetzner.yml` (backend/api) más un stack adicional para `n8n` y `mosquitto`.

Como regla: **si el servicio del backend se llama distinto** (por ejemplo `backend` en vez de `api`), ajusta únicamente `CASTUO_*_URL` para que apunten al contenedor real, sin tocar el JSON.

