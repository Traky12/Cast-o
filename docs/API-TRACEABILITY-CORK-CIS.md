# API — Trazabilidad corcho (Segureja) + CIS

## Endpoints (`/traceability`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/cork-extraction-events` | Registro extracción: `tree_uuid`, operador, mJ láser, score cambium **>0.99**, firma PQC, `gaia_chain_hash` o alias JSON **`gaichain_hash`** (SHA-3-512 hex). |
| `GET` | `/cork-extraction-events?limit=` | Lista auditables (memoria; sustituir por BD). |
| `GET` | `/cork-extraction-events/tree/{tree_uuid}` | Historial por alcornoque. |
| `GET` | `/cork-extraction-events/audit-summary` | Conteo total + último `tree_uuid`. |
| `POST` | `/cis/calculate` | Cuerpo: `water_saved_liters`, `carbon_avoided_kg`, opc. `edge_node_id` → `cis_credits`. |

## CIS

`1 CIS = 100 L agua ahorrada + 1 kg CO₂ evitado` (suma entera `floor`).

## Código

- Modelos: `backend/traceability/cork_models.py`
- CIS: `backend/traceability/cis_calculator.py`
- Store: `backend/traceability/cork_store.py`
- Router: `backend/routers/traceability_governance.py`

## Persistencia (post-MVP)

- PostgreSQL + QuestDB: [sql/cork_extractions_postgresql.sql](sql/cork_extractions_postgresql.sql), [sql/cork_extractions_questdb.sql](sql/cork_extractions_questdb.sql).
- Estado: [ESTADO-CAPA-TRAZABILIDAD-CORCHO.md](ESTADO-CAPA-TRAZABILIDAD-CORCHO.md).

## Contexto

[SEGUREJA-LASER-DESCORCHE-5.md](SEGUREJA-LASER-DESCORCHE-5.md) · [CASTUO-CLOUD-5X-SOBERANIA-TERRITORIAL.md](CASTUO-CLOUD-5X-SOBERANIA-TERRITORIAL.md)
