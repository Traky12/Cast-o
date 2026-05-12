# Contratos globales — CASTÚO-SYSTEM™ v10.0

Cumplimiento legal por continente y gobernanza global. Desplegar en GaiaChain o red compatible.

| Contrato | Región / Uso | Normativa / Función |
|----------|----------------|----------------------|
| EUCore.sol | Europa (núcleo v10) | GDPR, AI Act, PAC 2027; `authorizeNode`, `StandardAdded` |
| DynamicCompliance.sol | Global (50+ países) | Reglas por país; `addCountryRules`, `isCompliant`, `setGovernance` |
| GlobalGovernance.sol | DAO global | Votación y ejecución de propuestas → DynamicCompliance |
| CASTUO_System.sol | Maestro legal (raíz contracts/) | RPI/EUIPO placeholders; `verifyLegalStatus`, `setLegalNumbers` |
| JapanCompliance.sol | Japón | MHLW, JAS |
| ChileCompliance.sol | Chile | Ley 20.000, SAG |
| FranchiseContract.sol | Franquicias globales | Regalías SABIONDA; cooperativa extremeña concede/revoca. |

**Despliegue v10**: 1) DynamicCompliance, 2) GlobalGovernance(dynamicCompliance), 3) dynamicCompliance.setGovernance(globalGovernance).  
Ver [../README.md](../README.md) y [SABIONDA v10.0](../../docs/ai/SABIONDA-v10.0-Global-Standard.md).
