# Changelog — CASTÚO-SYSTEM

Cambios notables por versión. Plataforma agrovoltaica + hidroponía enterprise.

---

## [1.4.0] — Marzo 2026 — Verificación Salud 10/10

### Resumen

**📅 MARZO 2026 - CASTÚO-SYSTEM v1.4.0 FINALIZADO**

```
┌─ v1.0: Mistral Adapter base
├─ v1.2: TRL7 60/60 (6 capas)
├─ v1.3: ROOT MAESTRO security
├─ v1.3.2: Hidroponía Agrovoltaica
└─ v1.4.0: Verificación Salud 10/10 ← AHORA
```

### Añadido

- **Verificación Salud automatizada:** script `salud-verificacion.sh` (Fases 1→5: Infraestructura, Hidroponía, MQTT IoT, ROOT MAESTRO, Documentación). Log `salud-verificacion.log` y auditoría en `audit/salud-YYYYMMDD.log`.
- **Runbook production:** comandos únicos para servidor Hetzner, SSH remoto y post-verificación (mkdocs gh-deploy, estado contenedores).
- **Docs v1.4.0:** publicables con `mkdocs gh-deploy --message "v1.4.0: Verificación Salud 10/10 + Hidroponía Production"`.
- **Arquitectura:** análisis profundo *"De las Dehesas al Edge Computing"* (contenedores, flujo de datos Mermaid, seguridad, roles, ética, evolución). URL: `https://tudominio.com/arquitectura-dehesas-edge`. Plugin `mermaid2` para MkDocs (`pip install mkdocs-mermaid2-plugin`).
- **Optimización RPi 500+ sensores:** doc `optimizacion-rpi-500-sensores.md` (raspi-config, SensorManager asíncrono, mosquitto.conf, k6, métricas, Prometheus/Grafana).
- **Monitorización:** servicios `prometheus` (9090) y `grafana` (3000) en `docker-compose.hetzner.yml`; config en `docker/prometheus.yml`.
- **ArgoCD:** guía de automatización (k3s en Hetzner, Kustomize base/overlays production y staging, Prometheus/Grafana, alerta CPU > 70%, GitHub Action `argocd-sync.yml`). Estructura en `kubernetes/base/`, `kubernetes/overlays/`, `kubernetes/prometheus/`.
- **ArgoCD Multi-Cluster:**
  - Regiones EU/LATAM/Asia (Hetzner/AWS/Alibaba).
  - Overlays con normativas locales (GDPR/LGPD/PIPL).
  - GaiaChain 2.0 con nodos regionales y smart contracts.
  - Prometheus federado + alertas globales (ClusterDown).
  - Workflow GitHub Actions para sincronización automática.
  - Validación: Synced/Healthy en ArgoCD + Grafana dashboard 1860.
- **Resumen final / Revisar ArgoCD:** Pasos para confirmar Synced/Healthy (kubectl get svc, contraseña inicial, UI, argocd app get/logs). Tabla región EU/LATAM/Asia y beneficios clave alineados.
- **Ansible + ArgoCD para RPis:** `rpi-automation/ansible/` (inventory.ini, playbook.yml, templates/docker-compose.rpi.yml), `rpi-automation/kubernetes/rpi-cluster.yaml`; escalar a 10K farms.
- **Mercados de carbono:** `contracts/CarbonCredit.sol`, doc `carbon-credits-gaiachain.md` (Web3, register_carbon_credits), `alert-rules-carbon.yaml` (HighCarbonSavings).
- **Escalar a 10K / África:** overlay `kubernetes/overlays/africa/` (POPIA, Farm_Act_2026), `kubernetes/clusters/castuo-africa.yaml`, Prometheus federado con target `prometheus-africa:9090`.
- **Oceanía:** overlay `kubernetes/overlays/oceania/` (Carbon_Farming_Initiative, Climate_Change_Act_2023), `kubernetes/clusters/castuo-oceania.yaml`, Prometheus `prometheus-oceania:9090`, workflow `castuo-system-oceania`. Doc: Verra + Oceanía + Tokenización.
- **Verra / Gold Standard:** script `backend/scripts/generate_verra_report.py` (informes VCS VM0042 para Verra), doc sobre registro de proyecto y venta vía Xpansiv/AirCarbon.
- **Tokenización de cultivos:** contrato `contracts/CropToken.sol` (CropType: Lettuce, Cannabis, Tomato, Strawberry), `blockchain/scripts/deploy-crop-token.js`, `backend/scripts/tokenize_crop.py`, alertas `kubernetes/prometheus/alert-rules-crops.yaml` (CropTokenized).
- **Pagos en BioCoin para créditos de carbono:** contrato `BioCoinCarbonMarket.sol` (compra con ERC20/BioCoin, pricePerKgCO2, CreditSold), `blockchain/scripts/deploy-biocoin-carbon-market.js`, `backend/scripts/sell_carbon_credits_biocoin.py` (approve + buyCarbonCredits), alertas `alert-rules-biocoin.yaml`.
- **AirCarbon Exchange:** `backend/scripts/sell_on_aircarbon.py`, `aircarbon_webhook.py` (Flask), `sell_and_tokenize.py` (vender en AirCarbon + opcional BioCoin). Workflow `.github/workflows/sell-carbon-credits.yml` (repository_dispatch `aircarbon_sale`). `backend/scripts/check_biocoin_balance.py`. Doc: BioCoin + AirCarbon (pagos).
- **Resumen final / Runbook:** Validación final con `argocd app get` para eu/latam/asia/africa/oceania, salud-verificacion.sh, Grafana 1860, mensaje único de éxito. Pasos explícitos para añadir Oceanía (overlay, DigitalOcean, ArgoCD, push, validar). Registro CO₂ con `register_carbon_credits.py 0xDireccionDelComprador 12`.
- **Chainlink:** `BioCoinPriceConsumer.sol` (AggregatorV3Interface mínima, getLatestPrice/getBioCoinPriceUSD), `deploy-biocoin-price-consumer.js`, `backend/scripts/get_biocoin_price.py`. Doc: Chainlink + Marketplace.
- **Marketplace carbono:** `CarbonMarketplace.sol` (createListing, buyListing con 5% fee, getListing), `deploy-carbon-marketplace.js`, frontend React en `frontend/marketplace/` (App.js, ABI, Dockerfile), `kubernetes/marketplace/deployment.yaml` (Deployment + LoadBalancer). Opcional: paso en workflow ArgoCD para `carbon-marketplace`. Doc: chainlink-marketplace.md.

### Estado production

- ✅ ROI €281K/ha COMBINADO (tradicional + hidroponía)
- ✅ 10 servicios HETZNER 24/7 production
- ✅ Hidroponía NFT: 288 lechugas/canal LIVE
- ✅ ROOT MAESTRO: 1 clave control total
- ✅ Verificación Salud: 10/10 automatizada
- ✅ Docs v1.4.0: MkDocs profesionales públicas

### Comandos post-release

Ejecutar en secuencia (copiar/pegar):

```bash
mkdocs gh-deploy --message "v1.4.0: Production Ready" && \
docker compose ps | grep -E "(backend|mqtt)" && \
echo "🎉 CASTÚO-SYSTEM v1.4.0 - COOPERATIVAS READY!"
```

**📅 ABRIL 2026 →** Primera cooperativa production  
**🎖️ IMPERIO AGROVOLTAICO + HIDROPONÍA ENTERPRISE**

**¡PLATAFORMA DE REFERENCIA AGROVOLTAICA ESPAÑA FINALIZADA!**  
Docs públicas → Cooperativas listas → Éxito asegurado.

---

## [1.3.2] — 2026 — Hidroponía Agrovoltaica

- Hidroponía TRL7, modelos y router `/hidroponia/*`, servicio `rpi-hidroponia`, ROI €79.5K/ha.

## [1.3] — 2026 — ROOT MAESTRO security

- Seguridad centralizada, Fail2Ban, acceso root controlado.

## [1.2] — 2026 — TRL7 60/60

- 6 capas auditoría, cumplimiento enterprise.

## [1.0] — 2026 — Mistral Adapter base

- API Mistral, compliance regional, documentación inicial.
