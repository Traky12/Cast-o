# Cursor — Inmutabilidad (anti-hacking v1.0)

Contrato **CursorImmutability.sol**: registro de ejecuciones de scripts Cursor firmadas por HSM. Evita re-ejecución y permite auditoría en blockchain.

- `registerExecution(scriptHash, v, r, s, environment)` — Firma sobre `keccak256(scriptHash, environment)`.
- `isExecuted(scriptHash)`, `getSignature(scriptHash)`, `getEnvironment(scriptHash)`.
- `revertExecution(scriptHash, reason)` — Solo owner.

Despliegue: pasar dirección del HSM en el constructor. Ver [docs/security/Anti-Hacking-System-v1.0.md](../../docs/security/Anti-Hacking-System-v1.0.md).
