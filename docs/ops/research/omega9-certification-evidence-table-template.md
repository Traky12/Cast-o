# Tabla de evidencia para certificacion (Omega-9)

*(Plantilla ASCII para auditorias DORA/NIS2)*

| ID | Tipo de evidencia | Descripcion | Hash SHA-256 | TX GaiaChain | IPFS CID | Fecha | Estado |
|---|---|---|---|---|---|---|---|
| EV-001 | Informe de analisis | Resultados del analisis estatico/dinamico de una muestra EICAR. | `a1b2c3d4e5f6...` | `0x123...` | `QmXoy...` | 2026-03-23 | ✅ Validado |
| EV-002 | Documento de arquitectura | `omega9-defensive-lab-architecture-2026.md`. | `x1y2z3w4v5...` | `0x456...` | - | 2026-03-22 | ✅ Validado |
| EV-003 | Prueba de resiliencia | Simulacion de ataque DDoS (DORA Art. 6). | `b2c3d4e5f6...` | `0x789...` | - | 2026-05-15 | PENDIENTE |
| EV-004 | Politica de seguridad | Documento `security/policies.md` (version 2026). | `c3d4e5f6g7...` | `0xabc...` | - | 2026-03-20 | ✅ Validado |

**Nota sobre el formato de ejemplo**

> Los valores `a1b2c3...`, `0x123...` y `QmXoy...` son **solo ilustrativos**.  
> En auditorias reales, sustituir por:
>
> - Hashes **reales** del witness (`witness_payload_hash` del script) y, si aplica, `sha256sum` del fichero en disco.
> - Transacciones reales en GaiaChain (ej. `0x123...456` segun vuestra API).
> - CIDs IPFS solo si politica lo permite (documentos publicos / desclasificados).

**Estado**: usar `PENDIENTE` / `✅ Validado` segun control interno (no implica certificacion externa hasta informe del acreditador).
