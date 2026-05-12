# Verra / Gold Standard + Oceanía + Tokenización de cultivos

Integración con mercados regulados de carbono (Verra), cluster Oceanía (Sydney/Auckland) y tokenización de cultivos en GaiaChain 2.0 (CropToken).

---

## Paso 1: Añadir Oceanía (Australia/Nueva Zelanda)

**Objetivo:** Escalar a Oceanía (Sydney o Auckland) siguiendo el mismo patrón que África.

### 1.1 Overlay para Oceanía

Ubicación: `kubernetes/overlays/oceania/`

- **kustomization.yaml:** resources `../../base`, configMapGenerator con `DB_URL=postgres-oceania`, `LEGAL_FRAMEWORK=Carbon_Farming_Initiative,Climate_Change_Act_2023`, `REGION=oceania`.
- **deployment-patch.yaml:** LEGAL_FRAMEWORK para normativas australianas/neozelandesas.

### 1.2 Registrar el cluster en ArgoCD

Ejemplo con DigitalOcean (Sydney):

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

- En `kubernetes/prometheus/prometheus-federated.yaml` está el target `prometheus-oceania:9090`.
- El workflow `.github/workflows/argocd-sync-global.yml` incluye `castuo-system-oceania` (sync y wait --health).

### 1.4 Desplegar

```bash
git add .
git commit -m "feat: añadir cluster de Oceanía (Sydney) para mercados de carbono"
git push origin main
```

---

## Paso 2: Integración con Verra / Gold Standard

**Objetivo:** Vender créditos de carbono generados por CASTÚO-SYSTEM™ en mercados regulados.

### 2.1 Registrar el proyecto en Verra

1. Crear cuenta en [Verra](https://verra.org).
2. Registrar el proyecto:
   - **Metodología:** VM0042 (Agriculture, Forestry, and Other Land Use).
   - **Datos:** CO₂ ahorrado (ej: 12 kg por 288 lechugas), metodología IPCC 2019, documentación (salud-verificacion.sh, datos GaiaChain).
3. Obtener el **Project ID** (ej: VCS-1234).

### 2.2 Generar informes para Verra

Script: `backend/scripts/generate_verra_report.py`

```bash
python3 scripts/generate_verra_report.py farm-eu-001 12 VCS-1234
```

Genera un JSON en `verra_reports/<farm_id>_<fecha>.json` con project_id, farm_id, co2_saved_kg, methodology VM0042, sensors_data y gaiachain_tx.

### 2.3 Subir a Verra

Subir el archivo generado en [registry.verra.org](https://registry.verra.org/) (manual o automatizar con su API).

### 2.4 Venta de créditos (Xpansiv / AirCarbon Exchange)

Ejemplo de integración con API (sustituir URL y API key por los reales):

```python
import json
import requests

def sell_carbon_credits(verra_report_path: str, api_key: str) -> dict:
    url = "https://api.xpansiv.com/v1/credits/sell"
    with open(verra_report_path) as f:
        report = json.load(f)
    response = requests.post(
        url,
        json={"report": report, "api_key": api_key},
        headers={"Content-Type": "application/json"},
    )
    return response.json()
```

---

## Paso 3: Tokenización de cultivos (CropToken)

**Objetivo:** Tokenizar lechugas, cannabis, tomates, fresas, etc. en GaiaChain 2.0 (no solo CO₂).

### 3.1 Contrato CropToken.sol

Ubicación: `contracts/CropToken.sol`

- **CropType:** Lettuce (0), Cannabis (1), Tomato (2), Strawberry (3).
- **tokenizeCrop(farmId, cropType, quantity, co2Saved, verraProjectId):** registra un cultivo tokenizado.
- **getCrop(tokenId):** devuelve el cultivo.

### 3.2 Desplegar en GaiaChain

```bash
npx hardhat compile
npx hardhat run scripts/deploy-crop-token.js --network gaiachain
```

### 3.3 Script desde castuo-backend

```bash
kubectl exec -it deploy/castuo-backend -n castuo-system -- python3 scripts/tokenize_crop.py farm-eu-001 lettuce 288 12 VCS-1234
```

Variables de entorno: `CROP_TOKEN_CONTRACT_ADDRESS`, `GAIA_CHAIN_RPC`, `PRIVATE_KEY`.

### 3.4 Alertas en Prometheus

Reglas en `kubernetes/prometheus/alert-rules-crops.yaml`: alerta **CropTokenized** cuando `crop_tokenized_total > 0` (exponer métrica desde el backend).

---

## Paso 4: Validación final

1. **ArgoCD:** `argocd app get castuo-system-oceania` → Synced/Healthy. `kubectl get pods -n castuo-system --context=castuo-oceania`.
2. **Tokenización:** Ejecutar `tokenize_crop.py`, verificar la tx en el explorador de GaiaChain.
3. **Verra:** Generar informe con `generate_verra_report.py`, subir a Verra (o API).
4. **Celebrar:**

```bash
echo "🎉 CASTÚO-SYSTEM™ AHORA VENDE CRÉDITOS DE CARBONO EN VERRA + TOKENIZA CULTIVOS EN GAIACHAIN 2.0! 🌍💰"
```

---

[Runbook despliegue global](runbook-despliegue-global.md) · [Mercados de carbono](carbon-credits-gaiachain.md) · [ArgoCD Multi-Cluster](argocd-multi-cluster.md)
