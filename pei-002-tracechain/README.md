# PEI-002 — Huella de informe SIGPAC (digest + cadena de auditoría)

**Objetivo:** derivar un **digest SHA-256** del JSON de PEI-001, emitir (1) **payload Castuo** para `register_event_in_chain` y (2) **envelope** sin geometrías para integradores o stub de laboratorio.

**Territorio:** registro on-chain real → `backend/api/services/gaiachain_service.py` + `POST /api/audit/register-event` (JWT Keycloak). Ver [PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](../docs/legal/PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md) y [TraceChain-Compliance-2026.md](../docs/legal/TraceChain-Compliance-2026.md).

## Flujo Castuo (stdout + POST opcional)

```bash
python pei-002-tracechain/register_sigpac_digest.py \
  --report-path pei-001-sigpac/reports/sigpac_informe.json

set CASTUO_AUDIT_API_URL=https://api.ejemplo/api/audit/register-event
set CASTUO_AUDIT_API_TOKEN=...
set CASTUO_AUDIT_TOKEN_ID=1
python pei-002-tracechain/register_sigpac_digest.py \
  --report-path pei-001-sigpac/reports/sigpac_informe.json \
  --post
```

(`--report` es alias de `--report-path`.)

Instalación opcional de **`requests`** (recomendado para `--post-envelope`):

```bash
pip install -r pei-002-tracechain/requirements.txt
```

## Envelope TraceChain (archivo JSON, sin geometrías)

```bash
python pei-002-tracechain/register_sigpac_digest.py \
  --report-path pei-001-sigpac/reports/sigpac_informe.json \
  --out-payload pei-002-tracechain/payloads/sigpac_20260327.json
```

Incluye `cumple_via_counts` en `metadata` para contrastar con `results` del informe.

## POST al stub de laboratorio

```bash
set PEI002_ENVELOPE_POST_URL=http://127.0.0.1:8010/api/pei-002/envelope
set PEI002_STUB_BEARER_TOKEN=...
python pei-002-tracechain/register_sigpac_digest.py \
  --report-path pei-001-sigpac/reports/sigpac_informe.json \
  --post-envelope
```

En CI, los pasos POST usan `--no-stdout-payload` para no duplicar el JSON Castuo en el log.

Stub FastAPI: [api/README.md](api/README.md). **No** sustituye al backend Castuo.

## RGPD / por parcela

Ver [DPIA-TraceChain-2026.md](../docs/legal/DPIA-TraceChain-2026.md). El stub expone `POST /api/pei-002/parcel` **sin** geometría en el payload; los metadatos recibidos se guardan en **SQLite** (misma política de minimización: no se almacena geometría del polígono aquí).

## Relación con PEI-001

1. `validate_sigpac.py` → JSON.  
2. `register_sigpac_digest.py` → payload Castuo (stdout) + envelope (opcional) + POST reales o stub.
