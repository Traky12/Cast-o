# Arquitectura Multi-Cluster para CASTÚO-SYSTEM™

*Objetivo: Despliegue global con alta disponibilidad y cumplimiento local*

**Resumen ejecutivo:** De "local a global" en 7 pasos — ArgoCD en cluster central, overlays por región (EU/LATAM/Asia), GaiaChain 2.0, Prometheus federado, workflow global y validación Synced/Healthy.

---

## Resumen por región

| Región | Cluster | Proveedor | Normativas |
|--------|---------|-----------|------------|
| **EU** | castuo-eu | Hetzner | GDPR, AI Act, PAC 2040 |
| **LATAM** | castuo-latam | AWS São Paulo | LGPD, Lei Agro 2026 |
| **Asia** | castuo-asia | Alibaba HK | PIPL, AgriTech 2030 |

**Pasos para escalar:**

1. ArgoCD en cluster central (castuo-eu).
2. Estructura del repo: `base/`, `overlays/eu|latam|asia/`, `clusters/`.
3. Aplicaciones en ArgoCD: castuo-system-eu, castuo-system-latam, castuo-system-asia.
4. GaiaChain 2.0: nodos regionales + smart contracts por normativa.
5. Prometheus federado: métricas globales + alertas.
6. Workflow GitHub Actions: sincronización automática en `main`.
7. Validación: Synced/Healthy en ArgoCD + Grafana dashboard 1860.

---

## Paso 1: Configurar ArgoCD para múltiples clusters

*Gestión centralizada desde un único ArgoCD*

### 1.1 Instalar ArgoCD en un cluster central

Usar el cluster **castuo-eu** como control plane:

```bash
# En el cluster central (ej: castuo-eu):
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
```

### 1.2 Registrar los clusters remotos en ArgoCD

Añadir **castuo-latam** y **castuo-asia**:

```bash
# Obtener el kubeconfig de cada cluster y añadirlo a ArgoCD:
argocd cluster add <nombre-context> --name castuo-latam
argocd cluster add <nombre-context> --name castuo-asia
```

*(Los manifiestos de clusters en `argoproj/argo-cd` son ejemplos; en la práctica se usa `argocd cluster add` con el context del kubeconfig.)*

---

## Paso 2: Estructura del repositorio para multi-cluster

```
kubernetes/
├── base/                  # Configuración base (común a todos los clusters)
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── deployment.yaml
│   └── service.yaml
├── overlays/
│   ├── eu/
│   │   ├── kustomization.yaml
│   │   └── deployment-patch.yaml
│   ├── latam/
│   │   ├── kustomization.yaml
│   │   └── deployment-patch.yaml
│   └── asia/
│       ├── kustomization.yaml
│       └── deployment-patch.yaml
└── clusters/              # Configuración específica (ej: GaiaChain por región)
    ├── castuo-eu.yaml
    ├── castuo-latam.yaml
    └── castuo-asia.yaml
```

La **base** es común; cada overlay define `configMapGenerator` y parches por región (DB_URL, MQTT, REGION, LEGAL_FRAMEWORK).

**Overlays por región:**

| Overlay | configMapGenerator | LEGAL_FRAMEWORK (deployment-patch) |
|---------|--------------------|-----------------------------------|
| **eu/** | PORT_HIDRO=8001, DB_URL=postgres-eu | GDPR, AI_Act, PAC_2040 |
| **latam/** | DB_URL=postgres-latam, MQTT_USER=latam_user | LGPD, Lei_Agro_2026 |
| **asia/** | DB_URL=postgres-asia, REGION=asia | PIPL, AgriTech_2030 |

Ejemplo `deployment-patch.yaml` (LATAM):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: castuo-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        env:
        - name: LEGAL_FRAMEWORK
          value: "LGPD,Lei_Agro_2026"
```

---

## Paso 3: Aplicaciones en ArgoCD por región

En ArgoCD, **New App** para cada región:

| Application Name | Path | Cluster | Namespace |
|------------------|------|---------|-----------|
| castuo-system-eu | kubernetes/overlays/eu | castuo-eu (o in-cluster) | castuo-system |
| castuo-system-latam | kubernetes/overlays/latam | castuo-latam | castuo-system |
| castuo-system-asia | kubernetes/overlays/asia | castuo-asia | castuo-system |

- **Sync Policy:** Automatic  
- **Repository URL:** https://github.com/tu-usuario/castuo-system.git  
- **Revision:** HEAD  

---

## Paso 4: GaiaChain 2.0 multi-cluster

Desplegar nodos de GaiaChain por región (ver `kubernetes/clusters/castuo-eu.yaml`, `castuo-latam.yaml`, `castuo-asia.yaml`). Cada nodo usa `REGION` y `BOOTNODES` para P2P global.

Ejemplo de smart contract por normativa (LATAM: LGPD, Lei Agro 2026):

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CastuoLatam {
    string public legalFramework = "LGPD,Lei_Agro_2026";
    address public regionalAuthority;

    constructor(address _authority) {
        regionalAuthority = _authority;
    }

    function registerYield(uint256 amount, string memory crop) public {
        emit YieldRegistered(amount, crop, block.timestamp);
    }

    event YieldRegistered(uint256 amount, string crop, uint256 timestamp);
}
```

---

## Paso 5: Monitorización global (Prometheus federado)

- **Prometheus federado** en el cluster central: scrape de `prometheus-latam:9090` y `prometheus-asia:9090` (ver `kubernetes/prometheus/prometheus-federated.yaml`).
- **Alertas globales** (ej: ClusterDown cuando API server no responde) en `kubernetes/prometheus/alert-rules-global.yaml`.

---

## Paso 6: GitHub Actions para multi-cluster

El workflow `.github/workflows/argocd-sync-global.yml`:

- Se dispara en **push a main**.
- Hace login en ArgoCD y ejecuta **sync** y **wait --health** para:
  - castuo-system-eu  
  - castuo-system-latam  
  - castuo-system-asia  

---

## Paso 7: Validar y escalar

1. **ArgoCD:** Todas las aplicaciones en **Health: Healthy** y **Sync: Synced**.
2. **Salud por cluster:** Ejecutar el script de verificación (vía `kubectl exec` en el backend o desde un job).
3. **Grafana global:** URL `http://<EXTERNAL-IP-GRAFANA>:3000`. Importar dashboard **1860** ("Node Exporter Full").

---

## Pasos finales para probar y escalar

*(Copiar/pegar en terminal o Cursor)*

### 1. Probar el workflow de GitHub Actions

```bash
git push origin main
# Verificar en GitHub → Actions → "Sync ArgoCD Global".
```

### 2. Revisar ArgoCD (UI)

Ver sección [Pasos para Revisar ArgoCD (Synced/Healthy)](#pasos-para-revisar-argocd-y-confirmar-syncedhealthy) más abajo.

### 3. Validar con salud-verificacion.sh

```bash
kubectl exec -it deploy/castuo-backend -n castuo-system -- ./scripts/salud-verificacion.sh
# Esperar: ✅ Fase 1: Health endpoint 200 OK, ✅ Fase 2: Hidroponía → 500 sensores (NFT 288 lechugas)
```

### 4. Acceder a Grafana (dashboard 1860)

```bash
# Abrir http://<EXTERNAL-IP-GRAFANA>:3000 (admin/admin). Importar dashboard 1860.
```

### 5. Integración BioCoin (opcional)

```bash
npx hardhat run scripts/deploy-biocoin.js --network gaiachain
```

---

## Pasos para Revisar ArgoCD y Confirmar Synced/Healthy

*(Copiar/pegar en tu terminal)*

### 1. Acceder a la UI de ArgoCD

```bash
# Obtener la IP/URL de ArgoCD (LoadBalancer):
kubectl get svc -n argocd
# Ejemplo de salida:
# NAME            TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)
# argocd-server   LoadBalancer   10.43.123.123   123.123.123.123  80:30080/TCP
#
# Acceder a: http://123.123.123.123:80
# Usuario: admin
# Contraseña (obtener con):
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### 2. Verificar el estado de las aplicaciones

En la UI de ArgoCD:

- **Aplicaciones:** castuo-system-eu, castuo-system-latam, castuo-system-asia.
- **Sync Status:** Synced.
- **Health Status:** Healthy.
- **Pods:** Todos en Running (castuo-backend, gaiachain-node).

### 3. Revisar logs de sincronización

```bash
argocd app get castuo-system-eu
argocd app logs castuo-system-eu
```

---

## Beneficios clave

| Área | Beneficio |
|------|-----------|
| **Despliegue** | Multi-cluster automático (EU/LATAM/Asia). |
| **Cumplimiento** | Normativas locales integradas (GDPR/LGPD/PIPL). |
| **Blockchain** | GaiaChain 2.0 con nodos regionales. |
| **Monitorización** | Prometheus federado + Grafana dashboard 1860. |
| **Escalabilidad** | De 500 a 500K sensores sin cambios. |
| **Documentación** | Guía completa en MkDocs. |

---

## Automatizar el despliegue de RPis con Ansible + ArgoCD

*Escalar a 10K farms con RPis gestionadas como código*

Estructura recomendada:

```
rpi-automation/
├── ansible/
│   ├── inventory.ini       # Inventario de RPis por región
│   ├── playbook.yml        # Playbook para configurar RPis
│   └── templates/
│       └── docker-compose.rpi.yml
└── kubernetes/
    └── rpi-cluster.yaml    # Opcional: aplicación ArgoCD para el repo
```

- **Inventario:** grupos `[rpis_eu]`, `[rpis_latam]`, `[rpis_asia]` con `ansible_host`.
- **Playbook:** instalar Docker, desplegar plantilla docker-compose (rpi-hidroponia con SENSOR_LIMIT=500, MQTT_QOS=1, REGION).
- **Ejecución:** `ansible-playbook -i ansible/inventory.ini ansible/playbook.yml`.

Los archivos de ejemplo están en `rpi-automation/` en el repo. ArgoCD puede trackear el repositorio de configuración; el playbook se ejecuta desde tu máquina o desde CI.

---

## Integración con mercados de carbono

*Tokenizar el CO₂ ahorrado en GaiaChain 2.0*

- **Smart contract:** `CarbonCredit.sol` (issueCredits, getCredits). Ver [Mercados de carbono (GaiaChain)](carbon-credits-gaiachain.md) y `contracts/CarbonCredit.sol`.
- **Backend:** script Python que conecta a GaiaChain (Web3), firma y envía `issueCredits(farm_id, kg_co2)` (ej: 12 kg por 288 lechugas).
- **Grafana:** alertas en `kubernetes/prometheus/alert-rules-carbon.yaml` (HighCarbonSavings cuando carbon_credits_total > 1000).

---

## Escalar a 10K farms: clusters adicionales (ej. África)

1. **Crear cluster** (Hetzner/AWS) y registrar en ArgoCD: `argocd cluster add castuo-africa`.
2. **Crear aplicación:** `argocd app create castuo-system-africa --repo <repo> --path kubernetes/overlays/africa --dest-namespace castuo-system --sync-policy automated`.
3. **Overlay africa:** `kubernetes/overlays/africa/` con configMapGenerator (DB_URL=postgres-africa, LEGAL_FRAMEWORK=POPIA,Farm_Act_2026).
4. **GaiaChain:** `kubernetes/clusters/castuo-africa.yaml` con REGION=africa y BOOTNODES.
5. **Prometheus federado:** añadir target `prometheus-africa:9090` en `kubernetes/prometheus/prometheus-federated.yaml`.

---

Para seguir los pasos en orden (workflow, Ansible, CO₂, África, validación): [Runbook despliegue global](runbook-despliegue-global.md).

[Volver a ArgoCD (un solo cluster)](argocd-automation.md) · [Deploy](deploy.md)
