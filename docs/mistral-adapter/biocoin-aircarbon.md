# Pagos en BioCoin + AirCarbon Exchange

Permitir que los compradores paguen por créditos de carbono con BioCoin (GaiaChain 2.0) y automatizar la venta en AirCarbon Exchange.

---

## Paso 1: Integrar pagos en BioCoin para créditos de carbono

### 1.1 Contrato BioCoinCarbonMarket.sol

Ubicación: `blockchain/contracts/BioCoinCarbonMarket.sol` (y `contracts/BioCoinCarbonMarket.sol` en la raíz)

- **bioCoin:** dirección del token ERC20 (BioCoin). El token debe implementar `approve` y `transferFrom`.
- **pricePerKgCO2:** precio por kg de CO₂ en unidades de BioCoin (18 decimales). Por defecto 1 BioCoin = 1 kg CO₂.
- **buyCarbonCredits(kgCO2):** el comprador aprueba y transfiere BioCoin al owner; emite `CreditSold(buyer, kgCO2, totalBioCoin)`.
- **setPricePerKgCO2(newPrice):** solo owner.

### 1.2 Desplegar en GaiaChain

```bash
cd blockchain
export BIOCOIN_ADDRESS=0x...   # Dirección del contrato BioCoin
npx hardhat compile
npx hardhat run scripts/deploy-biocoin-carbon-market.js --network gaiachain
```

Si BioCoin no está desplegado: `npx hardhat run scripts/deploy_biocoin.js --network gaiachain`.

### 1.3 Comprar créditos con BioCoin (script)

Variables de entorno: `GAIA_CHAIN_RPC`, `BIOCOIN_CARBON_MARKET_ADDRESS`, `BIOCOIN_ADDRESS`, `PRIVATE_KEY` (cuenta compradora).

```bash
python3 scripts/sell_carbon_credits_biocoin.py 100
```

Esto aprueba el gasto de BioCoin y llama a `buyCarbonCredits(100)` (100 kg CO₂).

### 1.4 Alertas Prometheus

Reglas en `kubernetes/prometheus/alert-rules-biocoin.yaml`: **BioCoinCarbonSale** cuando `bio_coin_carbon_sold_total > 0`.

---

## Paso 2: Conectar con AirCarbon Exchange

### 2.1 Cuenta y API

- Registrar cuenta en AirCarbon Exchange.
- Obtener API Key (panel de desarrollador).
- Opcional: configurar webhooks para notificaciones de ventas.

### 2.2 Vender créditos en AirCarbon

Script: `backend/scripts/sell_on_aircarbon.py`

```bash
python3 scripts/sell_on_aircarbon.py VCS-1234 100 15
```

Variables: `AIRCARBON_API_KEY`, `AIRCARBON_API_URL` (opcional).

### 2.3 Webhook para ventas completadas

Servidor Flask: `backend/scripts/aircarbon_webhook.py`

```bash
python3 scripts/aircarbon_webhook.py   # Escucha en puerto 5000
```

Exponer con Ngrok: `ngrok http 5000` y configurar en AirCarbon la URL `https://xxx.ngrok.io/webhook`. En `credit_sale_completed` se puede llamar a `tokenize_crop.py`.

### 2.4 Integración BioCoin + AirCarbon

Script: `backend/scripts/sell_and_tokenize.py` — vende en AirCarbon y, si está configurado `BIOCOIN_CARBON_MARKET_ADDRESS`, ejecuta la compra con BioCoin.

```bash
python3 scripts/sell_and_tokenize.py VCS-1234 100 15
```

---

## Paso 3: Automatizar con GitHub Actions

Workflow: `.github/workflows/sell-carbon-credits.yml`

- **Trigger:** `repository_dispatch` con tipo `aircarbon_sale`.
- **Payload:** `verra_project_id`, `kg_co2`, `price_per_kg_usd`.
- **Secrets:** `GAIACHAIN_PRIVATE_KEY`, `AIRCARBON_API_KEY`, opcionalmente `BIOCOIN_CARBON_MARKET_ADDRESS`, `GAIA_CHAIN_RPC`.

Disparar manualmente (o desde webhook de AirCarbon):

```bash
curl -X POST \
  -H "Authorization: token TU_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/tu-usuario/castuo-system/dispatches \
  -d '{"event_type":"aircarbon_sale","client_payload":{"verra_project_id":"VCS-1234","kg_co2":100,"price_per_kg_usd":15}}'
```

---

## Paso 4: Validación final

### 4.1 Transacciones en GaiaChain

- Explorador: `https://explorer.gaiachain.castuo-system.com/tx/<tx_hash>`.
- Saldo BioCoin del comprador:

```bash
kubectl exec -it deploy/castuo-backend -n castuo-system -- \
  python3 scripts/check_biocoin_balance.py 0xComprador
```

Variables en el pod: `GAIA_CHAIN_RPC`, `BIOCOIN_ADDRESS`.

### 4.2 Ventas en AirCarbon

- Revisar el panel de AirCarbon.
- Si usas webhook, revisar logs del servidor Flask/Ngrok.

### 4.3 Celebrar

```bash
echo "🎉 CASTÚO-SYSTEM™ AHORA VENDE CRÉDITOS DE CARBONO EN AIRCARBON + PAGOS EN BIOCOIN! 🌍💰"
```

---

[Verra + Oceanía + Tokenización](verra-oceania-tokenizacion.md) · [Mercados de carbono](carbon-credits-gaiachain.md) · [Runbook](runbook-despliegue-global.md)
