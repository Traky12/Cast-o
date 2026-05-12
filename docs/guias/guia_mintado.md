# Guía Rápida de Mintado — ForestOwnershipToken

Pasos para tokenizar una parcela forestal en GaiaChain (Junta de Extremadura).

---

## 1. Requisitos previos

- Python 3.10+ con `web3` instalado (`pip install web3`).
- Variables de entorno configuradas:
  - `FOREST_OWNERSHIP_TOKEN_ADDRESS`: dirección del contrato desplegado.
  - `PRIVATE_KEY` o `JUNTA_PRIVATE_KEY`: clave del minter.
  - `GAIA_CHAIN_RPC`: URL del RPC (p. ej. `https://gaiachain.castuo-system.com`).

## 2. Mintado básico (sin certificaciones)

```bash
python3 backend/scripts/mint_forest_property.py \
  0xDIRECCION_PROPIETARIO \
  "XT-12345-001" \
  "39.4769°N, 6.3706°W" \
  10000 \
  "Quercus ilex, Pinus pinea" \
  5000 \
  false \
  "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"
```

## 3. Mintado con certificaciones (PEFC/FSC/Red Natura 2000)

Añadir al final el flag `-c` y los códigos de certificación:

```bash
python3 backend/scripts/mint_forest_property.py \
  0xDIRECCION_PROPIETARIO \
  "XT-12345-001" \
  "39.4769°N, 6.3706°W" \
  10000 \
  "Quercus ilex, Pinus pinea" \
  5000 \
  true \
  "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco" \
  -c PEFC FSC "Red Natura 2000"
```

## 4. Flujo certificado (SIGPAC + IPFS opcional)

Para validación previa con SIGPAC y subida de metadatos a IPFS:

```bash
export SIGPAC_API_KEY="tu_api_key"   # opcional
python3 backend/scripts/mint_certified_forest_property.py \
  0xPROPIETARIO XT-12345-001 \
  --certifications PEFC FSC "Red Natura 2000" \
  --upload-ipfs
```

## 5. Verificación

- Dashboard: introducir el Token ID en `https://dashboard-test.castuo-system.com` (o URL de producción).
- CLI: `python3 backend/scripts/calculate_subsidies_forest.py <TOKEN_ID> -v`

---

*Versión PDF: exportar desde este Markdown para distribución oficial.*
