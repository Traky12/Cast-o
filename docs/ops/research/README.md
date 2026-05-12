# Investigacion y laboratorio (Ops)

## Omega-9 (defensivo)

Arquitectura de laboratorio autorizado para analisis de muestras, cadena de custodia y triage notarizado:

- [`omega9-defensive-lab-architecture-2026.md`](omega9-defensive-lab-architecture-2026.md)
- Procedimiento notarizacion / auditoria: [`omega9-notarization-procedure-2026.md`](omega9-notarization-procedure-2026.md)

## Scripts (GaiaChain witness minimal)

| Script | Proposito |
|---|---|
| `scripts/ops/research/ingest-sample.sh` | Ingesta de muestra: JSON canonico + hash witness |
| `scripts/ops/research/Register-LabEvidence.sh` | JSON por stdin o `--file` (solo JSON); **un argumento** = fichero JSON o documento (sobre `document_path`, `document_sha256`) |
| `scripts/ops/research/recover-from-ddos.sh` | Stub runbook recuperacion DDoS (sustituir en prod) |

## Auditoria energetica (agrovoltaica / satelite)

- Indice Ops: [`../energy-audit/README.md`](../energy-audit/README.md)
- Arquitectura: [`../energy-audit/AUDITORIA-ENERGETICA-SATELITE-CASTUO-2026.md`](../energy-audit/AUDITORIA-ENERGETICA-SATELITE-CASTUO-2026.md)

## Cumplimiento

- DORA: [`docs/compliance/dora.md`](../../compliance/dora.md)
- NIS2 (stub): [`docs/compliance/nis2/README.md`](../../compliance/nis2/README.md)
