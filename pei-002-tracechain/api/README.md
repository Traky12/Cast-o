# API stub PEI-002 (laboratorio)

**Puerto recomendado:** `8010` (no chocar con el backend Castuo en `8000`).

## Arranque local

```bash
cd pei-002-tracechain/api
pip install -r requirements.txt
set PEI002_STUB_BEARER_TOKEN=dev-secreto-local
REM opcional: ruta absoluta de la BD (default: ./data/pei002_stub.db desde este directorio api/)
set PEI002_SQLITE_PATH=
uvicorn main:app --reload --port 8010
```

## Rutas

| Método | Ruta | Cuerpo |
|--------|------|--------|
| POST | `/api/pei-002/envelope` | `SigpacValidationEnvelope` (JSON) |
| POST | `/api/pei-002/parcel` | `ParcelAuditPayload` (sin geometría) |
| GET | `/api/pei-002/events/envelopes` | Lista desde **SQLite** |
| GET | `/api/pei-002/events/parcels` | Lista desde **SQLite** |
| GET | `/health` | Estado |

**Authorization:** `Bearer <PEI002_STUB_BEARER_TOKEN>`  
**Persistencia:** tablas `sigpac_validation_envelopes` y `parcel_validations` en SQLite (`PEI002_SQLITE_PATH` o `./data/pei002_stub.db` bajo este directorio `api/`). En Docker, montar volumen en `/app/data`.

## Docker

Contexto de build = carpeta `api/` (incluye `models.py`, `main.py`, `sqlite_store.py`, `data/`).

```bash
docker build -t pei002-stub -f pei-002-tracechain/api/Dockerfile pei-002-tracechain/api
docker run -p 8010:8010 -e PEI002_STUB_BEARER_TOKEN=dev-secreto -v pei002_data:/app/data pei002-stub
```

*`WORKDIR`: `/app`; BD por defecto `/app/data/pei002_stub.db`. Smoke de persistencia: [`tests/smoke/smoke_test_persistence.sh`](../../tests/smoke/smoke_test_persistence.sh).*

## Generar envelope desde informe PEI-001

```bash
python pei-002-tracechain/register_sigpac_digest.py \
  --report-path pei-001-sigpac/reports/informe.json \
  --out-payload pei-002-tracechain/payloads/env.json
curl -X POST http://127.0.0.1:8010/api/pei-002/envelope \
  -H "Authorization: Bearer dev-secreto" \
  -H "Content-Type: application/json" \
  -d @pei-002-tracechain/payloads/env.json
```

Respuesta JSON incluye `status: received`, `token_id`, `blockchain_tx: null`, `explorer_url: null`.

Este servicio **no** ejecuta `register_event_in_chain`; para cadena real usar el backend Castuo.
