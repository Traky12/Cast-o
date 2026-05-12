# GaiaChain — Validación HSM y administración maestra (anti-hacking v1.0)

Contrato **GaiaChainValidator.sol**: validación de transacciones con firma HSM (ecrecover). Solo la dirección HSM puede validar; el owner puede revertir una transacción.

Contrato **MasterAdmin.sol**: administración maestra — registro de hash de clave maestra (una vez), `verifyMasterAccess(inputHash)`, `addAdmin`/`removeAdmin`, `executeCriticalTransaction(txHash, v, r, s)` con firma HSM. Solo owner puede registrar master key y añadir admins.

- `validateTransaction(txHash, v, r, s)` — Firma ECDSA en formato (v, r, s).
- `isValidTransaction(txHash)`, `getSigner(txHash)`.
- `revertTransaction(txHash, reason)` — Solo owner.

Despliegue: pasar dirección del HSM en el constructor. Ver [docs/security/Anti-Hacking-System-v1.0.md](../../docs/security/Anti-Hacking-System-v1.0.md).
