# Carbon Marketplace (frontend)

Frontend React para el marketplace de créditos de carbono (GaiaChain 2.0 + BioCoin).

## Build local

```bash
npm install
REACT_APP_MARKETPLACE_ADDRESS=0x... npm run build
```

## Desarrollo

```bash
REACT_APP_MARKETPLACE_ADDRESS=0x... npm start
```

## Docker

```bash
docker build -t ghcr.io/castuo-system/carbon-marketplace:latest .
```

## Despliegue en Kubernetes

Ver `kubernetes/marketplace/deployment.yaml`. Desplegar con ArgoCD creando una app que apunte al path `kubernetes/marketplace` (ver doc [Chainlink + Marketplace](docs/mistral-adapter/chainlink-marketplace.md)).
