# Cumplimiento DORA - Resiliencia operativa digital (scaffold)

*(Reglamento (UE) 2022/2554 - referencia de alto nivel; validar con asesor legal.)*

## 1) Alcance en Omega-9

El laboratorio defensivo Omega-9 puede aportar evidencia a la postura de resiliencia ICT de la entidad (analisis autorizado, registros de incidentes de laboratorio, simulacros).

Arquitectura: [`docs/ops/research/omega9-defensive-lab-architecture-2026.md`](../ops/research/omega9-defensive-lab-architecture-2026.md)

## 2) Requisitos (resumen) vs medidas Omega-9

| Requisito (resumen) | Medida en Omega-9 (objetivo) | Documentacion (placeholder) |
|---|---|---|
| Gestion de riesgos ICT | Evaluaciones periodicas + registro | [`dora/risk-assessments/README.md`](dora/risk-assessments/README.md) |
| Pruebas de resiliencia | Simulacros semestrales (planificar) | [`dora/resilience-tests/README.md`](dora/resilience-tests/README.md) |
| Registro de incidentes ICT | Witness GaiaChain sobre eventos canonico-hashed | `CASTUO-LAB-01` (por validar) |
| Intercambio de informacion | MISP / ISAC solo con acuerdos | URLs y feeds **por validar** |

## 3) Evidencia recomendada

- Runbooks y actas de simulacro.
- Hashes notarizados (contrato minimal: `hash`, `coop_id`, `ipfs_cid`).

## 4) Auditorias

Directorio placeholder para informes externos (si aplica):

- [`docs/compliance/audits/README.md`](audits/README.md)
