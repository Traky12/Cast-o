# Alianza Junta de Extremadura — CASTÚO-SYSTEM™

Contrato de alianza para programas de subvenciones (PAC 2027, formación, infraestructura).

| Función | Quién | Descripción |
|---------|-------|-------------|
| createSubsidyProgram(name, budget, maxPerFarm) | Junta | Crea programa activo. |
| distributeSubsidy(farm, programId, amount) | Junta | Asigna subvención a finca (respetando budget y maxPerFarm). |
| registerInvestment(amount, purpose) | Junta | Registra inversión (ej. centro de datos Cáceres). |
| getFarmSubsidies(farm) | Público | Total subvenciones recibidas por la finca. |
| getProgramStatus(programId) | Público | Estado del programa. |

Despliegue: pasar dirección de la Junta en el constructor. Ver [docs/strategy/Plan-Maestro-Sinergias-2026-2031.md](../../docs/strategy/Plan-Maestro-Sinergias-2026-2031.md).
