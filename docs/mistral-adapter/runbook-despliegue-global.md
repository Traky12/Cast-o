# Runbook: Despliegue global (EU/LATAM/Asia/África/Oceanía)

Pasos para desplegar automáticamente con ArgoCD, configurar RPis con Ansible, tokenizar CO₂ y cultivos en GaiaChain 2.0, y escalar a 10K farms (incl. Oceanía y Verra).

---

## Paso 1: Ejecutar el workflow global (GitHub Actions)

**Objetivo:** Desplegar en EU/LATAM/Asia/África/Oceanía con un simple `git push`.

### 1.1 Confirmar rama main y cambios commitados

```bash
git status   # Sin cambios sin commit
git branch   # Estar en "main"
```

### 1.2 Push a main para activar el workflow

```bash
git add .
git commit -m "feat: despliegue global con ArgoCD + GaiaChain 2.0"
git push origin main
```

### 1.3 Verificar el workflow en GitHub Actions

1. Repositorio en GitHub → **Actions**.
2. Workflow **"Sync ArgoCD Global"**.
3. Esperar a que todos los pasos terminen en ✅.

Si hay errores, revisar los logs y ajustar `.github/workflows/argocd-sync-global.yml`.

---

## Paso 2: Desplegar RPis con Ansible

**Objetivo:** Configurar 500+ RPis para hidroponía/agrovoltaica en EU/LATAM/Asia con un solo comando.

### 2.1 Instalar Ansible (si no lo tienes)

```bash
sudo apt update
sudo apt install -y ansible
ansible --version   # 2.9+
```

### 2.2 Configurar el inventario de RPis

Editar `rpi-automation/ansible/inventory.ini`. Ejemplo:

```ini
[rpis_eu]
rpi-eu-001 ansible_host=192.168.1.101 ansible_user=pi
rpi-eu-002 ansible_host=192.168.1.102 ansible_user=pi

[rpis_latam]
rpi-latam-001 ansible_host=192.168.2.101 ansible_user=pi

[rpis_asia]
rpi-asia-001 ansible_host=192.168.3.101 ansible_user=pi
```

### 2.3 Ejecutar el playbook

Desde la raíz del proyecto:

```bash
cd rpi-automation/ansible
ansible-playbook -i inventory.ini playbook.yml --ask-become-pass
```

Te pedirá la contraseña de sudo de las RPis (por defecto en Raspberry Pi OS: `raspberry`; cámbiala por seguridad).

### 2.4 Verificar el despliegue en las RPis

```bash
ssh pi@192.168.1.101
docker ps                    # Contenedor rpi-hidroponia
docker logs rpi-hidroponia    # Logs en tiempo real
```

---

## Paso 3: Tokenizar CO₂ en GaiaChain 2.0

**Objetivo:** Registrar créditos de carbono ahorrados (ej: 12 kg CO₂ por 288 lechugas).

### 3.1 Desplegar el contrato CarbonCredit.sol

Con Hardhat en tu máquina local (desde el directorio del proyecto Hardhat, ej. `blockchain/` si el contrato está ahí, o raíz si usas `contracts/CarbonCredit.sol`):

```bash
npm install --save-dev hardhat
npx hardhat init
npx hardhat compile
npx hardhat run scripts/deploy-carbon-credit.js --network gaiachain
```

Si el contrato está en la raíz del repo: copia `contracts/CarbonCredit.sol` al proyecto Hardhat o configura `hardhat.config.js` con `paths: { sources: "contracts" }`. El script de despliegue está en `blockchain/scripts/deploy-carbon-credit.js`.

En `hardhat.config.js` configurar la red:

```javascript
networks: {
  gaiachain: {
    url: "https://gaiachain.castuo-system.com",
    accounts: [privateKey]
  }
}
```

### 3.2 Registrar créditos de CO₂ desde el pod de backend

```bash
kubectl exec -it deploy/castuo-backend -n castuo-system -- \
  python3 scripts/register_carbon_credits.py 0xDireccionDelComprador 12
```

Salida esperada: un `tx_hash`. Variables de entorno en el pod: `GAIA_CHAIN_RPC`, `CARBON_CREDIT_CONTRACT_ADDRESS`, `PRIVATE_KEY`.

### 3.3 Verificar en GaiaChain

Explorador: `https://explorer.gaiachain.castuo-system.com/tx/<tx_hash>`.

---

## Paso 3b: Tokenizar compost (CompostToken)

**Objetivo:** Registrar batches de compost en GaiaChain y vender en Biofertilizantes.org (ej: 1.000 kg en 10 batches de 100 kg).

### 3b.1 Desplegar CompostToken.sol

```bash
cd blockchain
export GAIA_CHAIN_RPC="https://gaiachain.castuo-system.com"
export PRIVATE_KEY="tu_private_key"
npx hardhat compile
npx hardhat run scripts/deploy-compost-token.js --network gaiachain
export COMPOST_TOKEN_ADDRESS="0x..."   # Salida del script
```

### 3b.2 Registrar batches de compost

Desde el backend (local o pod):

```bash
export GAIA_CHAIN_RPC="https://gaiachain.castuo-system.com"
export COMPOST_TOKEN_ADDRESS="0x..."
export PRIVATE_KEY="tu_private_key"
# 10 batches de 100 kg (1.000 kg total)
for i in 1 2 3 4 5 6 7 8 9 10; do
  python3 scripts/register_compost.py 100 60 50 7 "extremadura-farm-batch-$i"
done
```

Variables: `GAIA_CHAIN_RPC`, `COMPOST_TOKEN_ADDRESS`, `PRIVATE_KEY`.

### 3b.3 Vender en Biofertilizantes.org

```bash
export BIOFERTILIZANTES_API_KEY="tu_api_key"
# Opcional: BIOFERTILIZANTES_API_URL, GAIA_EXPLORER_URL
python3 scripts/sell_compost.py compost-extremadura-batch-1 100 0.8
```

Verificar en el panel de Biofertilizantes.org y en el explorador de GaiaChain los `tx_hash` de registro.

---

## Paso 3c: CropNFT (NFTs de cultivos)

**Objetivo:** Mintar un NFT por cultivo (lechuga, etc.) con metadatos en IPFS y listarlo en el marketplace.

### 3c.1 Desplegar CropNFT y Marketplace

```bash
cd blockchain
npx hardhat run scripts/deploy-crop-nft.js --network gaiachain
export CROP_NFT_ADDRESS="0x..."
npx hardhat run scripts/deploy-crop-nft-marketplace.js --network gaiachain
export CROP_NFT_MARKETPLACE_ADDRESS="0x..."
```

### 3c.2 Generar metadatos y mintear

```bash
ipfs_hash=$(python3 scripts/generate_crop_metadata.py lettuce extremadura-farm-001 "39.4769°N, 6.3706°W" 12 images/lettuce.jpg)
python3 scripts/mint_crop_nft.py 0xAgricultor lettuce extremadura-farm-001 "39.4769°N, 6.3706°W" 12 "$ipfs_hash"
```

### 3c.3 Listar y comprar en el marketplace

En el frontend (`frontend/crop-nft-marketplace`) o vía contrato: el vendedor debe aprobar el marketplace en CropNFT (`approve(CROP_NFT_MARKETPLACE_ADDRESS, tokenId)`), luego `createListing(tokenId, priceWei)`. El comprador llama `buyListing(listingId)` con `value: price`.

### 3c.4 Verificar propietario

```bash
python3 scripts/get_nft_owner.py 1
```

Detalle completo: [CropNFT Marketplace](crop-nft-marketplace.md).

---

## Paso 4: Añadir África/Oceanía (escalar a 10K farms)

**Objetivo:** Añadir el cluster de África siguiendo el mismo patrón.

### 4.1 Overlay para África

El overlay está en `kubernetes/overlays/africa/` con:

- `kustomization.yaml`: resources `../../base`, configMapGenerator (DB_URL=postgres-africa, LEGAL_FRAMEWORK=POPIA,Farm_Act_2026, REGION=africa).
- `deployment-patch.yaml`: LEGAL_FRAMEWORK=POPIA,Farm_Act_2026.

### 4.2 Registrar el cluster de África en ArgoCD

```bash
kubectl config use-context castuo-africa
argocd cluster add castuo-africa

argocd app create castuo-system-africa \
  --repo https://github.com/tu-usuario/castuo-system.git \
  --path kubernetes/overlays/africa \
  --dest-namespace castuo-system \
  --dest-server https://kubernetes.default.svc \
  --sync-policy automated
```

### 4.3 Prometheus federado

En `kubernetes/prometheus/prometheus-federated.yaml` el target `prometheus-africa:9090` ya está incluido.

### 4.4 Workflow de GitHub Actions

El workflow `.github/workflows/argocd-sync-global.yml` ya incluye `castuo-system-africa` (sync y wait --health).

### 4.5 Push para desplegar en África

```bash
git add .
git commit -m "feat: añadir cluster de África para escalar a 10K farms"
git push origin main
```

---

## Paso: Añadir Oceanía (Sydney/Auckland)

Repetir el mismo patrón que África para escalar a Oceanía.

### 1.1 Overlay para Oceanía

Ya existe en `kubernetes/overlays/oceania/kustomization.yaml` (DB_URL=postgres-oceania, LEGAL_FRAMEWORK=Carbon_Farming_Initiative,Climate_Change_Act_2023, REGION=oceania).

### 1.2 Registrar el cluster de Oceanía en ArgoCD

```bash
doctl kubernetes cluster create castuo-oceania --region syd1 --node-pool "name=worker-pool;size=s-2vcpu-4gb;count=2"
doctl kubernetes cluster kubeconfig save castuo-oceania
argocd cluster add castuo-oceania

argocd app create castuo-system-oceania \
  --repo https://github.com/tu-usuario/castuo-system.git \
  --path kubernetes/overlays/oceania \
  --dest-namespace castuo-system \
  --dest-server https://kubernetes.default.svc \
  --sync-policy automated
```

### 1.3 Prometheus y workflow

En `kubernetes/prometheus/prometheus-federated.yaml` está el target `prometheus-oceania:9090`. El workflow `.github/workflows/argocd-sync-global.yml` ya incluye `castuo-system-oceania`.

### 1.4 Push para desplegar en Oceanía

```bash
git add .
git commit -m "feat: añadir cluster de Oceanía (Sydney) para mercados de carbono"
git push origin main
```

### 1.5 Validar el despliegue

```bash
argocd app get castuo-system-oceania   # Debe estar Synced/Healthy
kubectl get pods -n castuo-system --context=castuo-oceania
```

---

## Paso: Piloto Extremadura (agrovoltaica + hidroponía)

**Objetivo:** Desplegar el piloto en Extremadura (PAC 2040, AI Act 2024, GDPR) con el mismo patrón que Oceanía.

### 1.1 Overlay para Extremadura

Ya existe en `kubernetes/overlays/extremadura/`:

- `kustomization.yaml`: DB_URL=postgres-extremadura, LEGAL_FRAMEWORK=PAC_2040,AI_Act_2024,GDPR, REGION=extremadura.
- `deployment-patch.yaml`: LEGAL_FRAMEWORK=PAC_2040,AI_Act_2024,GDPR.

Para Hetzner Cloud usar un Secret o variables de entorno del cluster para `HETZNER_CLOUD_TOKEN` (no incluir en ConfigMap).

### 1.2 Crear el cluster (Hetzner)

```bash
hcloud server create --name castuo-extremadura --type cx21 --image ubuntu-22.04
# Configurar kubeconfig según tu instalación de Kubernetes en Hetzner
# Ejemplo con Hetzner Cloud Kubernetes:
hcloud kubernetes create-cluster --name castuo-extremadura --region eu-central --node-pool "name=worker-pool;type=cx21;count=2"
hcloud kubernetes get-kubeconfig castuo-extremadura
```

### 1.3 Registrar el cluster en ArgoCD

```bash
argocd cluster add castuo-extremadura

argocd app create castuo-system-extremadura \
  --repo https://github.com/tu-usuario/castuo-system.git \
  --path kubernetes/overlays/extremadura \
  --dest-namespace castuo-system \
  --dest-server https://kubernetes.default.svc \
  --sync-policy automated
```

### 1.4 Prometheus y workflow

En `kubernetes/prometheus/prometheus-federated.yaml` está el target `prometheus-extremadura:9090`. El workflow `.github/workflows/argocd-sync-global.yml` ya incluye `castuo-system-extremadura`.

### 1.5 Push para desplegar en Extremadura

```bash
git add .
git commit -m "feat: añadir cluster de Extremadura para piloto agrovoltaico"
git push origin main
```

### 1.6 Validar el despliegue

```bash
argocd app get castuo-system-extremadura   # Synced/Healthy
kubectl get pods -n castuo-system --context=castuo-extremadura
kubectl exec -it deploy/castuo-backend -n castuo-system --context=castuo-extremadura -- ./scripts/salud-verificacion.sh
```

---

## Validación final

```bash
# 1. Revisar ArgoCD (todas las apps Synced/Healthy)
argocd app get castuo-system-eu
argocd app get castuo-system-latam
argocd app get castuo-system-asia
argocd app get castuo-system-africa
argocd app get castuo-system-oceania
argocd app get castuo-system-extremadura

# 2. Ejecutar salud-verificacion.sh en cada cluster
kubectl exec -it deploy/castuo-backend -n castuo-system -- ./scripts/salud-verificacion.sh

# 3. Revisar Grafana (dashboard 1860)
# Acceder a http://<IP_GRAFANA>:3000 e importar dashboard 1860 ("Node Exporter Full")

# 4. Mensaje de éxito
echo "🎉 DESPLIEGUE GLOBAL COMPLETADO: EU, LATAM, ASIA, ÁFRICA, OCEANÍA, EXTREMADURA + RPis + GaiaChain! 🌍"
```

---

[ArgoCD Multi-Cluster](argocd-multi-cluster.md) · [Verra + Oceanía](verra-oceania-tokenizacion.md) · [BioCoin + AirCarbon](biocoin-aircarbon.md) · [Chainlink + Marketplace](chainlink-marketplace.md) · [CropNFT Marketplace](crop-nft-marketplace.md) · [Mercados de carbono](carbon-credits-gaiachain.md) · [Deploy](deploy.md)
