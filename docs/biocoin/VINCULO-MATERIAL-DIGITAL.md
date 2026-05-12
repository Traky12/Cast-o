# Vínculo material–digital (BioCoin Castuo)

## EvidenceHash vivo: `compute_evidence_hash`

El registro deja de ser un objeto inerte cuando se ancla a **firma espectral (NIR)** de la tinta y al **hash de geolocalización de la cosecha**. Ambos entran en un único digest SHA-256 reproducible en `backend/biocoin/security_orchestrator.py`:

| Entrada | Rol |
|---------|-----|
| `serial_id` | Identidad de serie / lote |
| `nir_spectral_fingerprint_b64` | Firma NIR de la tinta (coleccionable) |
| `harvest_geohash_or_coord_hash` | Ancla territorial de la biomasa cosechada |
| `piezo_baseline_ohm_normalized` *(opc.)* | Línea base piezo-resistiva post-acuñación |

**Geolocalización canónica:** `harvest_geolocation_digest(lat, lon)` en `security_orchestrator.py`.

## Capa piezo-resistiva — tamper-evident digital

La nanocapa piezo-resistiva actúa como **sello físico**: un intento de taladrar la moneda para extraer el Secure Element altera la red eléctrica de la capa. Esa desviación respecto a la línea base registrada en mint **invalida la coherencia** con `EvidenceHash` y debe reflejarse en **EvidenceScore** bajo umbral en el dashboard (Streamlit).

## PVD / ALD (200–800 nm)

No es solo acabado: la barrera atómica **protege la Chlorella microencapsulada** frente a degradación ambiental, manteniendo **coherencia cromática** verificable por la app móvil (colorimetría vs referencia de serie).

## Flujo oráculo ↔ contrato

Ver [ORACLE-MINTING-FLOW.md](ORACLE-MINTING-FLOW.md). Firma EIP-191 alineada con `mint_message.py` y `BioCoinVault.mintWithEvidence`.
