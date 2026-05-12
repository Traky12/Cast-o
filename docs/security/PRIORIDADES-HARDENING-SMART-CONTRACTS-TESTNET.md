# Prioridades de Hardening — Smart Contracts (pre-Testnet)

**Fuente:** `CASTUO-SECURITY-VSA-PQC-EXECUTIVE.md` (VSA §2.2).  
**Alcance:** despliegue seguro antes de **testnet** Hyperledger Fabric (chaincode) y, donde exista, **EVM** (`BioPayQualityV1`, `EnergyCredit`, vaults asociados).

---

## P0 — Bloqueantes antes de testnet pública

| # | Área | Acción | Contrato / capa |
|---|------|--------|------------------|
| P0-1 | Oráculo único | Sustituir oráculo monopersonal por **multisig 2/3** o contrato **aggregator** con ventana de disputa antes de pago definitivo | BioPayQualityV1 |
| P0-2 | PoT EnergyCredit | Exigir **firma verificable on-chain** (ecrecover / EIP-712) de extremos HSM, no solo `settler` backend | EnergyCredit |
| P0-3 | Tesorería | **Límite diario** de retiros + **pausa** administrativa (emergencia) | BioPayQualityV1, EnergyCredit |
| P0-4 | Fabric chaincode | Misma lógica de **no pago sin consenso** y **idempotencia** de settlement; políticas **Endorsement** 2-of-N | Chaincode Mayday / liquidación |

---

## P1 — Alta prioridad (primera iteración testnet)

| # | Área | Acción |
|---|------|--------|
| P1-1 | Reentrancy residual | BioPay: patrón **pull** (`claim`) para productores contrato; o **whitelist EOA** |
| P1-2 | Admin/oracle rotation | **Timelock** en `setOracle` / `setSettler` (p. ej. 48 h) |
| P1-3 | Auditoría | **Slither** + informe; roadmap **Certora** / formal para funciones de pago |
| P1-4 | Eventos | Eventos de **disputa** y **pausa** para trazabilidad Fabric off-chain |

---

## P2 — Endurecimiento operativo

| # | Área | Acción |
|---|------|--------|
| P2-1 | Upgrade | Proxy **solo** con gobernanza multisig documentada |
| P2-2 | Oracle data | Hash **WORM** de lecturas NIR/planta en cadena antes de `submitQuality` |
| P2-3 | Sesiones PTM | Expiración `openedAt` + máximo **TTL** sesión no liquidada |

---

## Nota Hyperledger Fabric

En Fabric, el **settler/oráculo** equivale a identidades con certificados X.509: mapear **P0-2** a **firmas de endorsers** y **P0-1** a política de **mayoría** en endorsment. Los contratos Solidity en EVM pueden actuar como **espejo** de estado para demos; la **fuente de verdad** operativa debe alinearse con el modelo de confianza Fabric acordado.

---

*Lista viva. Completar fechas de pen-test e ISO 27001 según VSA §4.*
