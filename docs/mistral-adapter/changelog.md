# Changelog — Mistral-CASTÚO Adapter

Cambios notables por versión. Formato inspirado en [Keep a Changelog](https://keepachangelog.com/es/).

---

## [1.7.0] — Marzo 2026 — NFTs dinámicos + OpenSea + Cannabis/Fresas

### Añadido

- **DynamicCropNFT.sol:** ERC721 con metadatos actualizables (growthStage 0-100, ipfsHash, lastUpdate). Campos opcionales: strain, thcCbdRatio, brixLevel para cannabis y fresas. `mintNFT(..., strain, thcCbdRatio, brixLevel)`, `updateGrowthStage(tokenId, newGrowthStage, newIpfsHash)`.
- **Scripts:** `deploy-dynamic-nft.js`; `update_dynamic_nft.py` (IPFS + updateGrowthStage); `iot_growth_monitor.py` (monitor por pasos con intervalo configurable); `list_on_opensea.py` (approve OpenSea Wyvern); `mint_cannabis_nft.py`, `mint_strawberry_nft.py`.
- **Red Polygon** en hardhat.config para despliegue en OpenSea.
- **metadata/cannabis_amnesia_haze.json:** ejemplo de metadatos OpenSea para cannabis.
- **Doc:** `dynamic-nft-opensea.md` (NFTs dinámicos, OpenSea, cannabis y fresas). Enlace en MkDocs.

---

## [1.6.0] — Marzo 2026 — CropNFT (NFTs de cultivos + Marketplace)

### Añadido

- **CropNFT (ERC-721):** contrato `blockchain/contracts/CropNFT.sol` (OpenZeppelin) con metadatos por token (cropType, farmId, location, co2Saved, ipfsHash). `mintNFT`, `getMetadata`, `tokenURI`. Scripts `deploy-crop-nft.js`, `generate_crop_metadata.py` (IPFS), `mint_crop_nft.py`, `get_nft_owner.py`.
- **CropNFTMarketplace:** contrato para listar y comprar NFTs con ETH (2,5% fee). `createListing(tokenId, price)`, `buyListing(listingId)` payable. Script `deploy-crop-nft-marketplace.js` (requiere CROP_NFT_ADDRESS).
- **Frontend:** `frontend/crop-nft-marketplace/` (React + Web3), ABIs CropNFT y CropNFTMarketplace, Dockerfile multi-stage, `kubernetes/marketplace/crop-nft-marketplace.yaml`. Doc `crop-nft-marketplace.md` y enlace en MkDocs.

### Estado

- ✅ 1 NFT = 1 cultivo con trazabilidad blockchain + mercado secundario

---

## [1.5.0] — Marzo 2026 — Piloto Extremadura + CompostToken + Pitch Deck

### Añadido

- **Piloto Extremadura:** overlay `kubernetes/overlays/extremadura/` (PAC_2040, AI_Act_2024, GDPR). Workflow global incluye `castuo-system-extremadura`; Prometheus federado con `prometheus-extremadura:9090`. Runbook: crear cluster Hetzner, registrar en ArgoCD, push y validación.
- **CompostToken:** contrato `blockchain/contracts/CompostToken.sol` (registro de batches: kg, temperature, humidity, ph, batchId). Script `deploy-compost-token.js` (red gaiachain en hardhat.config). Scripts backend: `register_compost.py` (registrar en GaiaChain), `sell_compost.py` (venta en Biofertilizantes.org con certificación GaiaChain).
- **Pitch Deck Extremadura:** `docs/mistral-adapter/pitch-deck-extremadura.md` (métricas, modelo de negocio, roadmap, tabla de fondos de impacto, plantilla de email). Enlace en MkDocs: "Pitch Deck Extremadura".

### Estado

- ✅ Despliegue global: EU, LATAM, Asia, África, Oceanía, **Extremadura**
- ✅ Tokenización de compost (1.000 kg) con CompostToken + venta Biofertilizantes.org
- ✅ Documentación para inversores verdes (fondos + email)

---

## [1.4.0] — Marzo 2026 — Verificación Salud 10/10

### Añadido

- **Verificación Salud automatizada:** script `salud-verificacion.sh` (Fases 1→5: Infraestructura, Hidroponía, MQTT IoT, ROOT MAESTRO, Documentación). Log y auditoría en `audit/salud-YYYYMMDD.log`.
- **Runbook production:** one-liner servidor Hetzner, SSH remoto, post-verificación (mkdocs gh-deploy, estado contenedores).
- **Docs públicas v1.4.0:** `mkdocs gh-deploy --message "v1.4.0: Verificación Salud 10/10 + Hidroponía Production"`.

### Estado

- ✅ Verificación Salud 10/10 automatizada
- ✅ Hidroponía NFT 288 lechugas/canal LIVE
- ✅ ROOT MAESTRO + Fail2Ban
- ✅ Docs MkDocs profesionales públicas — **Plataforma lista para cooperativas.**

---

## [1.3.2] — 2026 — Hidroponía Agrovoltaica

### Añadido

- **Hidroponía TRL7:** modelos `HidroponiaSensor` (EC, pH, DO, temp, timestamp), `HidroponiaSistema` (NFT, DWC, EbbFlow, Aeroponia), `CultivoHidroponico` en `backend/models/hidroponia.py`.
- **Router** `GET /hidroponia/sistemas`, `POST /hidroponia/sensores` (JSON), `GET /hidroponia/cultivos`, `GET /hidroponia/alertas` en backend (puerto 8001).
- **Sensores IoT:** `iot/hidroponia-sensors.yml` (ec_ph, temperatura, oxigeno_disuelto, alerta_sms).
- **Servicio** `rpi-hidroponia` (perfil `hidroponia`) en docker-compose.hetzner.yml.
- **Docs:** [Hidroponía Agrovoltaica](hidroponia.md) — ROI €79.5K/ha (+40%), comandos demo y deploy.

---

## [1.0.0] — 2026

### Añadido

- **APIKeyManager:** gestión de API keys con cifrado Fernet y lectura desde `MISTRAL_API_KEY` o `ENCRYPTED_MISTRAL_API_KEY`.
- **MistralDataManager:** carga de datasets CSV, JSON y Parquet; validación básica de cumplimiento GDPR (avisos).
- **MistralAPIClient:** cliente HTTP para Mistral API v1 (chat/completions), rate limiting configurable (por defecto 60 req/min), logging para GaiaChain.
- **Configuración regional:** perfiles ES, EU y GLOBAL con compliance (GDPR, AI Act 2024, PAC 2040).
- **Ejemplo Sabionda Educa:** función `ejemplo_completo()` y ejecución con `python api/mistral_castuo_adapter.py`.
- **Documentación:** estructura en `docs/mistral-adapter/` (Overview, Features, Installation, Usage, API Reference, Compliance, Examples, FAQ, Roadmap, Changelog) y soporte MkDocs Material (idioma es).

### Seguridad

- API keys nunca en log; solo clave cifrada o variable de entorno.
- Cifrado opcional con Fernet (clave en env por región).

### Notas

- `stream=True` en `query()` aún no implementado; se ignora con un aviso en log.
- Registro en GaiaChain es simulado (hash en log); integración real pendiente de backend GaiaChain 2.0.

---

[Volver a Introducción](index.md)
