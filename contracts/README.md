# Contratos GaiaChain — CASTÚO / Sabionda

Contratos Solidity para trazabilidad y certificados educativos.

---

## BioPayQualityV1.sol / EnergyCredit.sol

- **BioPay:** pago cooperativas por **Pe** (peso × azúcares × sequedad × bonus carbono); oráculo IoT; tesorería ETH.
- **EnergyCredit:** sesiones **PTM** (PoT doble firma, liquidación kWh).

## CastuoRegistry.sol (5.PRO+ Ladanum)

- **Uso:** `submitEvidence(bytes32 evidenceHash, string dataRoomId)` — registro gemelo / VERDFIRMA antes de mercado.
- **ABI:** `CastuoRegistryABI.json` (Node / Python web3).
- **Par:** `CastuoToken.sol` (BIOC placeholder gobernanza).

---

## SabiondaCertificates.sol

- **Uso**: Emisión de certificados de formación verificables en blockchain (Sistema Sabionda).
- **Funciones**: `issueCertificate`, `verifyCertificate`, `revokeCertificate`, `isCertificateValid`.
- **Despliegue**: Compilar con Hardhat (o Solidity 0.8.x). Desplegar en GaiaChain testnet primero; luego mainnet.
- **Integración**: Backend (FastAPI) llama al nodo GaiaChain vía Web3; Moodle/plataforma Sabionda invoca API del backend al completar curso.

## PAC2027Subvenciones.sol (SABIONDA v7.1)

- **Uso**: Trazabilidad legal de subvenciones PAC 2027 en GaiaChain (módulo Legal v7.1).
- **Funciones**: `requestSubvencion`, `setEligibility`, `setFarm`; evento `SubvencionApproved`.
- **Lógica**: Solo auditor; finca debe ser elegible y haber pasado ≥365 días desde última auditoría para solicitar subvención (500 €/ha).
- **Despliegue**: Mismo proceso que SabiondaCertificates; auditor = cuenta CASTÚO o autoridad designada.

---

## Contratos globales (CASTÚO v9.0) — `global/`

Contratos por continente para cumplimiento legal y trazabilidad.

| Contrato | Región | Uso | Validación |
|----------|--------|-----|------------|
| **EUCore.sol** | Europa | Núcleo UE: GDPR, AI Act 2024/1689, PAC 2027 | AEMPS, ANSM, BfArM |
| **JapanCompliance.sol** | Asia (Japón) | THC ≤ 0.3 %, MHLW + JAS | MHLW, JAS |
| **ChileCompliance.sol** | América (Chile) | THC ≤ 1.0 %, SAG, licencia exportación | SAG |

- **EUCore**: `addCompliantStandard`, `isCompliant`.
- **JapanCompliance**: `requestApproval` (thc en basis points: 30 = 0.30 %), `approveBatch` (MHLW), `certifyJAS`.
- **ChileCompliance**: `requestApproval` (thc ≤ 100 = 1.0 %), `approveBatch(batchId, license)` (SAG).

---

## Requisitos

- Solidity ^0.8.0
- Hardhat (recomendado) para compilación y tests
