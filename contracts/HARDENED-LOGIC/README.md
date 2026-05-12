# HARDENED-LOGIC — Capa de ejecución financiera y energética [CIPHER-LEVEL-5]

Contratos e integraciones que blindan fondos y créditos PTM frente a reentrancy, oráculo único y robo de haz.

## Contratos

| Archivo | Rol |
|---------|-----|
| **BIOPAY-V2-PULL.sol** | Pago por biomasa: patrón **Authorize → Pull**. Consenso triple-check (NIR + VULCAN + TERRA) off-chain; orquestador llama `authorizePayment`; productor retira con `withdrawFunds`. |
| **ENERGY-CREDIT-MULTISIG.sol** | PTM: **doble firma** (emisor + receptor) para PoT; **ajuste calima** (`calimaLossBps`) para crédito neto. |

## Integraciones

| Archivo | Rol |
|---------|-----|
| **BIO-HUB-GATEWAY.js** | Oráculo que conecta sensores PLC/NIR de [BIO-HUB-DIGITAL] con BioPayV2; solo autoriza tras triple-check. |
| **PTM-SETTLEMENT-LOGIC.py** | Valida **alineación óptica** antes de autorizar sesión PTM (backend Aetheris). |
| **DILITHIUM-SIGNER.go** | Firma PQC (ML-DSA) para autorizaciones; sustituir placeholder por lib NIST en producción. |

## Regla [FINANCIAL-INTEGRITY]

No usar `send()` ni `transfer()` directos para movimientos de valor. Flujo: **Authorize → Pull**. Ver `SYSTEM_PROMPT.md`.

## Referencias

- Prioridades testnet: `docs/security/PRIORIDADES-HARDENING-SMART-CONTRACTS-TESTNET.md`
- VSA/PQC: `docs/security/CASTUO-SECURITY-VSA-PQC-EXECUTIVE.md`
