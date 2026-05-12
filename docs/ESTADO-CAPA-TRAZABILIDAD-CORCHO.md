# Estado — Capa de trazabilidad corcho (Propiedad digital del árbol)

**Propiedad digital del árbol:** al exigir **`cambium_integrity_score > 0.99`**, el registro no es solo extracción; certifica **salud biológica** coherente con láser de precisión **SEGUREJA**.

## Componentes activos (MVP)

| Componente | Función | Validación |
|------------|---------|------------|
| **PQC-ready** | Preparación firma post-cuántica | Campo `pqc_signature` en esquema |
| **GaiaChain** | Ancla soberana | `gaia_chain_hash` / alias **`gaichain_hash`** (SHA-3-512 hex) |
| **CIS Calculator** | Impacto → activo | 100 L = 1 CIS; 1 kg CO₂ = 1 CIS |
| **Audit summary** | Transparencia certificadores | `GET .../audit-summary` + histórico por `tree_uuid` |

Código: `backend/traceability/` · API [API-TRACEABILITY-CORK-CIS.md](API-TRACEABILITY-CORK-CIS.md).

## Evolución: persistencia (PostgreSQL + QuestDB)

- **PostgreSQL:** metadatos del árbol (`traceability_trees`), relaciones legales, operadores.
- **QuestDB (o PG particionado):** alto volumen de **eventos de extracción** e histórico multi-decada (ciclo corcho).

Esquema sugerido: [sql/cork_extractions_postgresql.sql](sql/cork_extractions_postgresql.sql) · variant QuestDB: [sql/cork_extractions_questdb.sql](sql/cork_extractions_questdb.sql).

*Nota: el borrador con `INHERIT (traceability_master)` se sustituye por FK explícita a tabla maestra de árboles para portabilidad.*
