# Marco PEI-002 — Huella de informes SIGPAC y cadena de auditoría (2026)

**Ámbito:** anclar informes `pei-001-sigpac` **sin inventar** exploradores de bloques ni contratos inexistentes en el clon. **No** es certificación eIDAS.

**Relación:** [SIGPAC-Compliance-2026.md](./SIGPAC-Compliance-2026.md) · [DPIA-TraceChain-2026.md](./DPIA-TraceChain-2026.md) · [PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md) · [pei-002-tracechain/README.md](../../pei-002-tracechain/README.md)

---

## 1. Evidencia primaria

- El JSON (y PDF opcional) de PEI-001 es la **fuente operativa**.
- La cadena / API audit es **complementaria**; si falla RPC o JWT, el fichero en disco prevalece.

## 2. Payload Castuo (producción)

| Pieza | Nota |
|--------|------|
| Servicio | `backend/api/services/gaiachain_service.py` → `register_event_in_chain(event_data: dict)` |
| HTTP | `POST /api/audit/register-event` (Keycloak, roles `dpo` / `admin`) |
| Cuerpo | `tokenId` (int), `action`, `status`, `details`, `compliance` |

Generación:

```bash
python pei-002-tracechain/register_sigpac_digest.py \
  --report-path pei-001-sigpac/reports/sigpac_real.json \
  --post
```

Variables: `CASTUO_AUDIT_API_URL`, `CASTUO_AUDIT_API_TOKEN`, `CASTUO_AUDIT_TOKEN_ID`.

El script añade en `details` el campo **`cumple_via_counts`** (coherencia con `results` del informe).

## 3. Envelope TraceChain (integradores / laboratorio)

Formato **sin geometrias** (minimización RGPD):

- `event_type`: `sigpac_validation`
- `digest`: `sha256:<hex>` del fichero del informe
- `timestamp`: Unix derivado de `generated_utc` del informe
- `parcelas`, `cumplen`
- `metadata`: `mapping_path`, `usos_problematicos`, `summary` (subset PEI-001: `cumple`, no `cumplen` en fuente), `cumple_via_counts`, `report_generated_utc` (ISO del informe), `report_generated_utc_unix`

Generación:

```bash
python pei-002-tracechain/register_sigpac_digest.py \
  --report-path pei-001-sigpac/reports/sigpac_real.json \
  --out-payload pei-002-tracechain/payloads/sigpac_20260327.json
```

Salida **stdout** sigue siendo el **payload Castuo** (compatibilidad con `--post`). El envelope solo se escribe con `--out-payload` (y mensaje de ruta en stderr).

POST opcional al stub:

```bash
set PEI002_ENVELOPE_POST_URL=http://127.0.0.1:8010/api/pei-002/envelope
set PEI002_STUB_BEARER_TOKEN=...
python pei-002-tracechain/register_sigpac_digest.py --report-path ... --post-envelope
```

`--post-envelope` usa **`requests`** si está instalado (`pip install -r pei-002-tracechain/requirements.txt`); si no, `urllib` estándar.

## 3.1. Stub vs producción (resumen)

| Campo | Stub PEI-002 (`:8010`) | Producción Castuo |
|--------|-------------------------|-------------------|
| Ruta HTTP | `POST /api/pei-002/envelope` | `POST /api/audit/register-event` |
| Autenticación | `PEI002_STUB_BEARER_TOKEN` (env servicio) | Keycloak JWT + roles `dpo` / `admin` |
| Cuerpo | Envelope (`event_type`, `digest`, …) | Dict `register_event_in_chain` (`tokenId` **int**, `action`, `status`, `details`, `compliance`) |
| `blockchain_tx` | `null` (sin fingir TX) | Hash real si RPC y contrato OK |
| `explorer_url` | `null` | Solo si existe explorador **real** del despliegue |

Respuesta típica stub:

```json
{
  "status": "received",
  "token_id": "pei002-env-…",
  "blockchain_tx": null,
  "explorer_url": null
}
```

## 4. Stub FastAPI (no sustituye al backend)

Ubicación: `pei-002-tracechain/api/`. Rutas bajo **`/api/pei-002/*`** para no colisionar con el monolito Castuo.

- **No** devuelve URLs de explorador inventadas; `blockchain_tx` y `explorer_url` son `null` en el stub.
- Registro por parcela: `POST /api/pei-002/parcel` con modelo **sin geometría**; ver [DPIA-TraceChain-2026.md](./DPIA-TraceChain-2026.md).

## 5. Registro por parcela y cadena real

- El contrato actual agrupa por **`tokenId`**, no por parcela física.
- Para una fila: usar **digest** de un objeto redactado (sin `geometry`) o un evento agregado en `details` del payload Castuo, siempre tras DPIA.
- **No** importar `GaiaChainService` ficticio desde el stub: la vía real sigue siendo `gaiachain_service` en el backend desplegado.

## 6. CI

Workflow `.github/workflows/tracechain-pei002.yml`:

- `workflow_dispatch` (informe con fixtures si no indicas ruta) o **`workflow_run`** tras **SIGPAC validation PEI-001** (descarga artefacto `sigpac-report-pei001`, informe `sigpac_pei001_ci.json`).
- Escribe `pei-002-tracechain/payloads/ci_envelope.json`, sube artefacto **`pei002-envelope`**.
- Pasos POST usan `--no-stdout-payload` para no repetir JSON en el log.

---

*Documento orientativo; integración crítica sujeta a despliegue y contrato real.*
