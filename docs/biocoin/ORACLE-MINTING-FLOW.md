# Acuñación con prueba de existencia (Oracle Minting)

## Contrato `BioCoinVault.sol`

- **`mintPriceWei = 0` en el constructor:** primera fase sin barrera económica de entrada; el valor está en la **prueba cripto-física** (evidence + manifest + firma oráculo).
- **Timelock 48 h (`TIMELOCK_DELAY`):** cualquier cambio de precio pasa por `scheduleMintPriceChange` → espera → `executeMintPriceChange`. Mitiga **flash governance** y cambios relámpago de parámetros econónicos.
- **Reserva 10 % (`reserveRateBps = 1000`):** acumulado en `bioReserveWei`; modelo de **circularidad** y colchón para **recompra / retirada** si el EvidenceScore cae bajo umbral operativo (gobernanza off-chain documentada).

## Cadena Python

1. `harvest_location_digest(lat, lon)` → hash parcela.
2. `compute_evidence_hash(serial_id, nir_b64, harvest_hash, piezo_baseline?=...)` → `bytes32` evidence.
3. `build_manifest_canonical(...)` → `manifest_canonical_hash()` → `bytes32` manifest.
4. `sign_mint_oracle(...)` en `mint_message.py` → `(v, r, s)` para `mintWithEvidence`.

El contrato reconstruye `msgHash = keccak256(abi.encodePacked(evidenceHash, manifestHash, tokenId, to, this, chainid))` y valida `ecrecover` contra `oracleSigner`.
