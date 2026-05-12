# BioCoin Castuo — Infraestructura físico-digital

## Entregables en repo

| Artefacto | Ruta |
|-----------|------|
| BOM materiales | [BOM_Materiales.csv](BOM_Materiales.csv) |
| Curado UV/Plasma | [PROTOCOLO_CURADO_UV_PLASMA.md](PROTOCOLO_CURADO_UV_PLASMA.md) |
| MiCA / REACH / ISO | [REGULATORY-MICA-REACH.md](REGULATORY-MICA-REACH.md) |
| Vínculo material–digital | [VINCULO-MATERIAL-DIGITAL.md](VINCULO-MATERIAL-DIGITAL.md) |
| Oracle minting | [ORACLE-MINTING-FLOW.md](ORACLE-MINTING-FLOW.md) |
| E2E arranque medido | [../AUDITORIA-ARRANQUE-MEDIDO-E2E.md](../AUDITORIA-ARRANQUE-MEDIDO-E2E.md) |
| Orquestador seguridad | `backend/biocoin/security_orchestrator.py` |
| Firma mint ↔ contrato | `backend/biocoin/mint_message.py` |
| Smart contract | `contracts/biocoin/BioCoinVault.sol` |
| Dashboard Evidence | `dashboard/biocoin_evidence_dashboard.py` |

## Contrato BioCoinVault (resumen)

- **Génesis:** `tokenId` 1–10.000, una unidad por id.
- **mintWithEvidence(to, tokenId, evidenceHash, manifestHash, qualityScore, doubleCountProtected, v,r,s):** paga `mintPriceWei`; **10 %** acumulado en `bioReserveWei`.
- **clausulaExpansion:** requiere `daoExpansionApproved` y `evidenceScoreStable` (timelock gobernanza off-chain).
- **EmergencyPause** + **Timelock 48 h** para `reserveRateBps` y `mintPriceWei`.

## EvidenceHash (Python)

```python
from backend.biocoin.security_orchestrator import (
    evidence_hash_hex,
    harvest_geolocation_digest,
    build_manifest_canonical,
    manifest_canonical_hash,
)
from backend.biocoin.mint_message import sign_mint_oracle

harvest_hash = harvest_geolocation_digest(39.18, -6.12)
eh = evidence_hash_hex("CASTUO-0421", nir_b64, harvest_hash, piezo_baseline_normalized="1.02e6")
manifest = build_manifest_canonical("CASTUO-0421", "Extremadura", 62.0, lca_co2_kg_snapshot=-1.1)
mh = manifest_canonical_hash(manifest)
v, r, s = sign_mint_oracle(eh, mh, 421, collector, vault, chain_id, ORACLE_KEY)
```

## Ejecución dashboard

```bash
streamlit run dashboard/biocoin_evidence_dashboard.py
```

---

*Serie Premium 10.000 — climáticamente positiva, forensemente auditable.*
