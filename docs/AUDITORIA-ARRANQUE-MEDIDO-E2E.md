# Auditoría arranque medido — test E2E (referencia)

## Alcance

1. **Integridad ZIP:** `python scripts/rebuild_system.py --zip-path … --manifest …` → salida 0.

2. **Trust:** `TrustOrchestrator` en estado TRUSTED antes de API crítica (`CASTUO_MEASURED_BOOT=1`).

3. **BioCoin cadena off-chain:**

   - `harvest_geolocation_digest` → `compute_evidence_hash` (NIR + geo ± piezo/ALD).

   - `build_manifest_canonical` → `manifest_canonical_hash`.

   - `sign_mint_oracle` → `(v,r,s)` coherente con `BioCoinVault.mintWithEvidence`.



## Automatizado

```bash

pytest tests/test_biocoin_e2e_mint_flow.py tests/test_trust_resilience.py -v

```



## P&ID operativo

Checklist sala técnica: [PID-SALA-TECNICA-FASE1-600.md](../instalaciones/PID-SALA-TECNICA-FASE1-600.md) (ORP, OI, fail-safe pH/O₃).


