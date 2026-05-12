# Arquitectura Legal y Tecnica (Verificada en el repo)

**Version:** 1.0  
**Fecha:** 20/03/2026  
**Autor:** Gregorio Jimenez Bodes / Sabionda IA  

> Este documento marca como "Verificado" unicamente lo que puede comprobarse en el repo (archivos, scripts y endpoints). Lo demas queda como "Por validar" (dependiente de tu despliegue).

---

## 1) Diagrama de arquitectura verificable

```mermaid
graph TD
    subgraph Tecnica["Infraestructura tecnica (repo)"]
        A[Backend (FastAPI)] -->|/agents/*| B[SQLite local (log-event)]
        A -->|/agents/system/sync-gaiachain| C[Sincronizacion GaiaChain (por script)]
        A -->|/mistral/ask| D[Sabionda IA (Mistral backend)]
        A -->|/api/v1/witness| E[GaiaChain witness (payload hash)]
    end

    subgraph Seguridad["Seguridad (documentacion)"]
        Q[Qubes OS / AppVMs] -->|plantillas de docs| B
        W[Whonix / Tor] -->|plantillas de docs| B
        P[Parrot Security / Wazuh / OpenVAS] -->|plantillas de docs| B
    end

    subgraph Evidencia["Evidencia (exports)"]
        F[Scripts de evidencia] -->|hash SHA256| E
        D -->|recomendaciones| F
        E -->|TXID/resp| G[Archivos: witness/info local]
    end
```

---

## 2) Matriz de cumplimiento (solo verificado en repo)

| Componente | Normativa | Mecanismo | Evidencia verificable en repo | Estado |
|---|---|---|---|---|
| GaiaChain witness | eIDAS 2.0 (trazabilidad) | SHA256 + POST a `/api/v1/witness` | `scripts/Register-SecurityEvent.ps1` y `backend/services/gaia_chain_witness.py` | Verificado (contrato witness) |
| Eventos de seguridad local | ISO 27001 / NIS2 (auditoria) | POST `/agents/system/log-event` (SQLite) | `backend/routers/agents_autonomous.py` y `scripts/Register-SecurityEvent.ps1` | Verificado (endpoint y payload) |
| Monitoreo/diagnostico | NIS2 | GET `/agents/system/health` y `/agents/system/status` | `docs/PRONTUARIO_MAESTRO_MONITOREO_DIAGNOSTICO_TRL9.md` y backend alias de compatibilidad | Verificado (endpoints) |
| Sabionda IA (Mistral backend) | AI Act | POST `/mistral/ask` con `{prompt,model}` | `backend/main.py` y `scripts/Generate-ECSEReport.ps1` | Verificado (endpoint y uso por script) |
| ECSE reporte (evidencia exportable) | ISO/GDPR (trazabilidad) | Export `report.json/csv/pdf` + witness opcional | `scripts/Generate-ECSEReport.ps1` | Verificado (export + witness) |
| Qubes OS / Whonix / Parrot | NIS2 / GDPR | Plantillas en docs + ejecucion dependiente de tu infra | `docs/ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md` | Por validar (despliegue real) |

---

## 3) Protocolo de evidencia legal (GaiaChain witness verificado)

### 3.1 Contrato de witness (repo)

El script `scripts/Register-SecurityEvent.ps1` registra un witness con el payload minimal:

```powershell
$payloadWitness = @{
  hash    = $eventHash  # SHA256 del metadata canono (string JSON)
  coop_id = $CoopId      # default 1
  ipfs_cid = $null       # IPFS opcional (no usado aqui)
}

$witnessUrl = ($GaiaChainApiUrl.TrimEnd("/")) + "/api/v1/witness"

$response = Invoke-RestMethod -Uri $witnessUrl -Method Post -Headers @{
  "Authorization" = "Bearer $GaiaChainApiKey"
  "Content-Type"  = "application/json"
} -Body ($payloadWitness | ConvertTo-Json -Depth 20 -Compress)
```

### 3.2 Endpoint witness en el backend (usa el mismo contrato)

En el backend se implementa el witness como:

- endpoint: `POST /api/v1/witness`
- payload: `{"hash": ..., "coop_id": ..., "ipfs_cid": ...}`

Ver `backend/services/gaia_chain_witness.py`.

---

## 4) Protocolo de auditoria local (endpoint verificado)

Para registrar un evento critico local en SQLite, el repo expone:

- endpoint: `POST /agents/system/log-event`
- payload esperado (compatibilidad con plan de evidencias):
  - `event_type` (string)
  - `details` (object o texto)
  - `severity` (string en `critical|error|warning|info`)

Ejemplo (alineado con `scripts/Register-SecurityEvent.ps1`):

```powershell
$payload = @{
  event_type = "manual_check"
  details    = @{ example = "hello" }
  severity   = "warning"
} | ConvertTo-Json -Compress

Invoke-RestMethod -Uri "http://localhost:8001/agents/system/log-event" `
  -Method Post -ContentType "application/json" -Body $payload
```

### 4.1 Valores soportados para `severity` (verificados en el repo)

- En `scripts/Register-SecurityEvent.ps1`, el parametro `-Severity` valida contra:
  - `critical|error|warning|info`
- En el backend, `POST /agents/system/log-event` toma `severity` (si no se define, usa `critical`).

---

## 5) Plantilla legal para CTAEX (con trazabilidad verificable)

Esta plantilla esta pensada para referenciar TXIDs y hashes que tu despliegue genere (no afirma resultados sin evidencia).

```markdown
# INFORME DE CUMPLIMIENTO LEGAL PARA CTAEX (con trazabilidad repo)
**Codigo de Proyecto:** {project_code}
**Fecha:** {generation_date}

## Evidencia verificable
- Eventos de seguridad (repo): TXID/txid desde `Register-SecurityEvent.ps1` (si GaiaChain esta configurado)
- Monitoreo/diagnostico (repo): `GET /agents/system/health` y `GET /agents/system/status`
- Reporte ECSE: `scripts/Generate-ECSEReport.ps1` (report.json/csv y witness opcional)
```

---

## 6) Sabionda IA (Mistral backend) - contrato verificado en el repo

### 6.1 Endpoint `POST /mistral/ask`

El backend define `POST /mistral/ask` con un cuerpo:
- `prompt` (string)
- `model` (string; por defecto `mistral-tiny`)

Internamente el backend llama `.../v1/chat/completions` con:
- `model: request.model`
- `messages: [{"role":"user","content": request.prompt}]`

Referencia:
- `backend/main.py` -> `class MistralRequest` y `@app.post("/mistral/ask")`

### 6.2 Uso desde `scripts/Generate-ECSEReport.ps1`

El script construye:

```powershell
$mistralPayload = @{
  prompt = $prompt
  model  = $MistralModel
}

$aiRaw = Invoke-PostJsonOrNull -Uri "$BaseUrl/mistral/ask" -BodyObj $mistralPayload
```

---

## 7) Verificacion de coherencia (checklist repo)

1. Validar endpoints de monitoreo:
   - `GET http://localhost:8001/agents/system/health`
   - `GET http://localhost:8001/agents/system/status`

2. Validar endpoint witness:

```bash
curl -X POST "$GAIA_CHAIN_API_URL/api/v1/witness" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "coop_id": 1,
    "hash": "sha256_del_metadata_canono",
    "ipfs_cid": null
  }'
```

3. Ejecutar el script verificado:

```powershell
.\scripts\Register-SecurityEvent.ps1 `
  -EventType "system_test" `
  -EventData @{ message="Prueba de integracion"; status="success" } `
  -Severity "info" `
  -CoopId 1 `
  -LogEventInBackend
```

4. Validar que se genero evidencia local:
   - ruta: `security-events/<yyyyMMdd>/<txid>.json`

---

## 7) Enlaces

- Arquitectura de seguridad reforzada: `docs/ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md`
- Marco ECSE y trazabilidad: `docs/PRONTUARIO_MAESTRO_EVOLUTIVO_ECSE.md`
- Monitoreo y evidencias operativas: `docs/PRONTUARIO_MAESTRO_MONITOREO_DIAGNOSTICO_TRL9.md`
- Coherencia de trazabilidad: `docs/ENLACES-DE-TRAZABILIDAD.md`

