# API — Logs XAI firmados (CASTUO Ledger)

## Modelo lógico

1. Cliente (dron / Lab) construye cuerpo **sin** `event_anchor_hash` ni `signature`.
2. Servicio o firmware calcula `event_anchor_hash = SHA256( parent_ledger || SHA256(canonical_unsigned) )`.
3. **Secure Element** firma los **32 bytes** de `event_anchor_hash` (política ECDSA del módulo).
4. Registro completo se persiste (WORM / cadena); siguiente evento usa este `event_anchor_hash` como `ledger_hash`.

`parent_ledger_hash` en el primer evento de misión = **genesis** (`0x` + 64 ceros).

## Endpoints sugeridos (FastAPI)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/v1/patrimonio/xai-log/preview` | Body: campos sin anchor/firma → `{ canonical, event_anchor_hash, parent_ledger_hash }` |
| `POST` | `/v1/patrimonio/xai-log/commit` | Body: registro completo → valida cadena + almacena |
| `GET` | `/v1/patrimonio/xai-log/mission/{mission_id}` | Lista ordenada para verificación |

## Esquema JSON

[schemas/castuo_xai_ledger_log.v1.schema.json](schemas/castuo_xai_ledger_log.v1.schema.json)

## Implementación Python

`backend/patrimonio/xai_ledger.py` — `verify_log_chain()`, `XAILedgerLogV1.seal()`.

## Caso de uso narrativo

[CASTUO-SIMULACION-OPERACION-CRIPTA-SILENCIO.md](CASTUO-SIMULACION-OPERACION-CRIPTA-SILENCIO.md)
