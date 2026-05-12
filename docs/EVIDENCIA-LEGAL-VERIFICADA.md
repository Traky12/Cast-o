# EVIDENCIA LEGAL VERIFICADA (repo)

**Version:** 1.0  
**Fecha:** 20/03/2026  
**Autor:** Gregorio Jimenez Bodes / Sabionda IA  

> Enfoque: rutas del backend y contrato de evidencia "witness" que existen en el repo.  
> Donde dependemos de integraciones externas (GaiaChain API real, AEMPS API real, CLI, etc.) se marca como "por validar".

---

## 1) Endpoints reales de certificacion y verificacion (prefijo `/agents`)

### 1.1 Generacion de certificado soberano

- **Endpoint:** `POST /agents/certificates/generate`
- **Body (verificado en repo):**
  - `lote_id` (string)
  - `cultivo` (string; por defecto `cannabis_medicinal`)

### 1.2 Verificacion publica de certificado por `tx_hash`

- **Endpoint:** `GET /agents/certificates/verify/{tx_hash}`
- **Endpoint:** `GET /agents/certificates/verify?tx_hash={tx_hash}`

El campo a usar como `{tx_hash}` es el que el backend devuelve en `gaiachain_tx`.

## 1.3 Alias publico compatible (prefijo `/api`)

El repo expone adicionalmente el endpoint:
- `GET /api/certificates/verify/{tx_hash}`

En este repo, ese endpoint actua como alias: si `{tx_hash}` parece un TXID GaiaChain, proxy-a la verificacion soberana existente.

---

## 2) Contrato GaiaChain witness (verificado en scripts)

La evidencia inmutable para eventos del sistema se registra con el contrato del repo via:

- Script real: `scripts/Register-SecurityEvent.ps1`
- Endpoint: `POST {GAIA_CHAIN_API_URL}/api/v1/witness`

Payload minimal (repo):

```powershell
$payloadWitness = @{
  hash    = $eventHash   # SHA256 del metadata canonical (string JSON)
  coop_id = $CoopId
  ipfs_cid = $null
}
```

---

## 3) Flujo verificado: certificacion soberana de cannabis medicinal

### 3.1 Paso A: solicitar generacion de certificado

Ejemplo (curl):

```bash
curl -X POST "http://localhost:8001/agents/certificates/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "lote_id": "CAN-2026-001",
    "cultivo": "cannabis_medicinal"
  }'
```

Salida (esperada por estructura del repo):
- `gaiachain_tx` (TXID a verificar)
- `certificate_hash`
- `verification_url`

### 3.2 Paso B: verificar el certificado por `tx_hash`

```bash
curl "http://localhost:8001/agents/certificates/verify/0xTU_TX_HASH"
```

### 3.3 Paso C (opcional): registrar un evento de trazabilidad

Si quieres adjuntar un evento de auditoria (para trazabilidad interna) ejecuta:

```powershell
.\scripts\Register-SecurityEvent.ps1 `
  -EventType "certificate_generated" `
  -EventData @{ lote_id="CAN-2026-001"; gaiachain_tx="0xTU_TX_HASH" } `
  -Severity "info" `
  -CoopId 1 `
  -LogEventInBackend
```

> Nota: el `-LogEventInBackend` escribe en SQLite via `POST /agents/system/log-event`. El witness inmutable se registra via `api/v1/witness` (GaiaChain real, por validar en entorno).

---

## 4) Paso AEMPS (certificacion y trazabilidad verificable en el repo)

## 4.1) Certificacion AEMPS (endpoint existente)

El repo implementa el endpoint:
- `POST /cannabis/certify_aemps`

Este endpoint construye datos y, en el estado actual del repo, devuelve un resultado `pending` (integracion externa por validar).

---

## 4.2) Webhook receptor AEMPS (endpoint nuevo, implementado)

Endpoint:
- `POST /api/aemps/webhook`

Requiere:
- variable de entorno `AEMPS_WEBHOOK_SECRET`

Comportamiento:
- verifica firma sha256(payload_text + secret)
- registra evidencia local en SQLite (via `/agents/system/log-event`)
- registra witness GaiaChain (si GaiaChain esta disponible)

---

## 4.3) Auditoria end-to-end (script nuevo)

Script:
- `scripts/Audit-CannabisTrial.ps1`

Usa SOLO endpoints reales del repo para:
- solicitar certificacion AEMPS (pending)
- generar certificado soberano
- verificar el TX del certificado
- registrar witness+evidencia via `scripts/Register-SecurityEvent.ps1`

---

## 4.4) Dashboard Grafana (basado en metrics Prometheus del repo)

Metrics expuestas por el backend (derivadas de evidencia local):
- `cannabis_trial_status{trial_id,status}`
- `cannabis_trial_compliance{trial_id,standard}`

---

## 5) Enlaces bidireccionales

- Desde `docs/ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md` (seccion "Enlaces de trazabilidad")
- Desde `docs/PRONTUARIO_MAESTRO_EVOLUTIVO_ECSE.md` (prontuario relacionado)
- Coherencia de evidencias: `docs/ENLACES-DE-TRAZABILIDAD.md`

