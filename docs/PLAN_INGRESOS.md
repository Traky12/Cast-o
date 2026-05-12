# Plan de acción para empezar a generar ingresos hoy

Pasos prácticos con comandos que coinciden con la API actual de CASTÚO-SYSTEM.

---

## 1. Configuración inicial (5 minutos)

### Dependencias

```bash
pip install reportlab qrcode[pil] python-dotenv
```

### Variables de entorno

Crear o editar `.env` en la raíz del proyecto (o exportar en la sesión):

```bash
# Empresa (facturas)
COMPANY_NAME="CASTÚO-SYSTEM S.L."
COMPANY_CIF="B12345678"
COMPANY_ADDRESS="Pol. Ind. La Dehesa, Cáceres"
COMPANY_EMAIL="facturacion@castuo-system.com"
COMPANY_IBAN="ESXX12345678901234567890"

# Opcional: trazabilidad
GAIA_CHAIN_CLI=/usr/local/bin/gaiachain

# Opcional: firma cualificada
EIDAS_PRIVATE_KEY_PATH=certs/eidas_private_key.pem
EIDAS_CERT_PATH=certs/eidas_cert.pem
```

En **PowerShell** (Windows):

```powershell
$env:COMPANY_NAME="CASTÚO-SYSTEM S.L."
$env:COMPANY_CIF="B12345678"
$env:COMPANY_ADDRESS="Pol. Ind. La Dehesa, Cáceres"
$env:COMPANY_EMAIL="facturacion@castuo-system.com"
```

### Arrancar la API

```bash
cd "C:\Users\traky\OneDrive - FCI\Castuo-System"
.\venv\Scripts\Activate.ps1
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

---

## 2. Ingresos con suscripciones (modelo SaaS)

### A. Crear suscripción

```bash
curl -X POST "http://localhost:8000/agents/subscriptions/create" -H "Content-Type: application/json" -d "{\"cliente\": {\"nombre\": \"Cooperativa Agricola Extremena\", \"cif_nif\": \"B87654321\", \"direccion\": \"Calle del Olivo 123, Badajoz\", \"email\": \"contabilidad@cooperativa.es\"}, \"plan\": \"premium\"}"
```

Planes: `basic` (99.99 €/mes), `premium` (299.99 €/mes), `enterprise` (999.99 €/mes).

Respuesta: `subscription_id`, `invoice` (numero_factura, pdf_path), `gaiachain_tx`. Enviar el PDF de `invoices/` al cliente.

### B. Consumir un análisis

Cuando el cliente use un análisis de yield/cannabinoides/clima:

```bash
curl -X POST "http://localhost:8000/agents/subscriptions/consume" -H "Content-Type: application/json" -d "{\"subscription_id\": \"SUB-20260316-54321\", \"analysis_type\": \"yield\"}"
```

### C. Renovación automática (cron)

Llamar cada día para renovar suscripciones con `end_date` vencida:

```bash
# Ruta correcta: /agents/automatic-billing/recurring (POST, sin cuerpo)
# Compatibilidad con plan: /agents/automatic-billing/process-recurring
curl -X POST "http://localhost:8000/agents/automatic-billing/recurring"
```

Ejemplo cron (Linux): `0 8 * * * curl -s -X POST "http://localhost:8000/agents/automatic-billing/recurring" >> /var/log/castuo/recurring.log 2>&1`

---

## 3. Venta de acceso a datos agronómicos

### A. Publicar producto de datos

```bash
curl -X POST "http://localhost:8000/agents/data-marketplace/publish" -H "Content-Type: application/json" -d "{\"lote_id\": \"CAN-2026-001\", \"product_type\": \"yield_data\"}"
```

Tipos: `yield_data`, `cannabinoid_data`, `climate_data`. Respuesta incluye `product_id` y `marketplace_url`.

### B. Vender acceso (comprador)

Usar el campo **`buyer`** (no `buyer_data`):

```bash
curl -X POST "http://localhost:8000/agents/data-marketplace/sell" -H "Content-Type: application/json" -d "{\"product_id\": \"DATA-CAN-2026-001-YIELD_DATA-20260316\", \"buyer\": {\"nombre\": \"Universidad de Extremadura - Dept. Agronomia\", \"cif_nif\": \"Q12345678\", \"direccion\": \"Av. de la Universidad 1, Caceres\", \"email\": \"agronomia@unex.es\"}}"
```

Respuesta: `invoice`, `license` (access_token, access_url). Enviar PDF y `access_url` al comprador.

---

## 4. Tokenizar lotes como NFTs (royalties)

### A. Tokenizar lote

```bash
curl -X POST "http://localhost:8000/agents/nft-monetization/tokenize" -H "Content-Type: application/json" -d "{\"lote_id\": \"CAN-2026-001\", \"royalty_percentage\": 5.0, \"list_price\": 1000}"
```

Respuesta: `nft.nft_tx`, `listing.marketplace_url`. Usar `nft_tx` para pagar royalties.

### B. Pagar royalties pendientes

El endpoint **calcula** el importe pendiente a partir del historial del NFT. Solo se envía `nft_id` (por query):

```bash
curl -X POST "http://localhost:8000/agents/nft-monetization/pay-royalties?nft_id=0xstub_CAN-2026-001_abc12345"
```

Para registrar un pago con importe y moneda concretos (sin cálculo interno), usar:

```bash
curl -X POST "http://localhost:8000/agents/nft/pay-royalties" -H "Content-Type: application/json" -d "{\"nft_id\": \"0xstub_CAN-2026-001_abc12345\", \"amount\": 50, \"currency\": \"MATIC\"}"
```

---

## 5. Automatizar facturación y declaraciones

### Informe mensual (GET y POST compatibles)

```bash
curl -X GET "http://localhost:8000/agents/automatic-billing/monthly-report?month=3&year=2026"
```

Compatibilidad con plan (POST):
```bash
curl -X POST "http://localhost:8000/agents/automatic-billing/monthly-report" \
  -H "Content-Type: application/json" \
  -d "{\"month\":3,\"year\":2026}"
```

### Procesar pagos pendientes

```bash
curl -X POST "http://localhost:8000/agents/automatic-billing/process-payments"
```

### Generar declaraciones 303 y 390

```bash
curl -X POST "http://localhost:8000/agents/automatic-billing/declarations"
```

Genera 303 del mes actual y, si es diciembre, el resumen anual 390 (envío a AEAT simulado).

### Ignición comercial diaria (todo en uno)

Un solo endpoint ejecuta: recurrencias, pagos pendientes, declaraciones 303/390, publicación de un producto de datos (lote configurable) y devuelve el estado del dashboard. Ideal para cron al arranque del día:

```bash
# Ejecutar cada día a las 8:00 (o al iniciar el servidor)
curl -X POST "http://localhost:8000/agents/market-ignition"
```

Desde línea de comandos (sin API):

```bash
cd "C:\Users\traky\OneDrive - FCI\Castuo-System"
.\venv\Scripts\Activate.ps1
python -m backend.agents_autonomous.market_ignition
```

Variables opcionales: `LOTE_MARKET_IGNITION` (ej. CAN-2026-003), `TIPO_PRODUCTO_IGNITION` (ej. cannabinoid_data).

### Cron ejemplo (declaraciones mensuales)

```bash
# Día 1 de cada mes a las 9:00
0 9 1 * * curl -s -X GET "http://localhost:8000/agents/automatic-billing/monthly-report?month=$(date +\%m)&year=$(date +\%Y)" >> /var/log/castuo/aeat.log 2>&1
```

---

## 6. Monitorizar ingresos

### Últimas 24 h

```bash
curl -s "http://localhost:8000/agents/dashboard/realtime"
```

### Mensual (mes y año)

```bash
curl -s "http://localhost:8000/agents/dashboard/monthly?month=3&year=2026"
```

### Agregado por periodo (facturas)

```bash
curl -s "http://localhost:8000/agents/dashboard/revenue?period=month"
```

### Proyección a 6 meses

```bash
curl -s "http://localhost:8000/agents/dashboard/projection?months=6"
```

---

## Resumen rápido

| Acción                 | Método y ruta                                                                 | Nota                          |
|------------------------|-------------------------------------------------------------------------------|-------------------------------|
| Crear suscripción      | `POST /agents/subscriptions/create`                                          | body: `cliente` + `plan`      |
| Consumir análisis     | `POST /agents/subscriptions/consume`                                         | body: `subscription_id`, `analysis_type` |
| Renovar suscripciones | `POST /agents/automatic-billing/recurring`                                    | sin cuerpo                    |
| Publicar datos        | `POST /agents/data-marketplace/publish`                                      | body: `lote_id`, `product_type` |
| Vender acceso datos   | `POST /agents/data-marketplace/sell`                                          | body: `product_id`, **`buyer`** |
| Tokenizar lote        | `POST /agents/nft-monetization/tokenize`                                     | body: `lote_id`, `royalty_percentage`, `list_price` |
| Pagar royalties (NFT) | `POST /agents/nft-monetization/pay-royalties?nft_id=...`                     | importe calculado por sistema |
| Pagar royalties (fijo)| `POST /agents/nft/pay-royalties`                                              | body: `nft_id`, `amount`, `currency` |
| Informe mensual       | `GET /agents/automatic-billing/monthly-report?month=&year=`                    | query params                  |
| Declaraciones AEAT     | `POST /agents/automatic-billing/declarations`                                  | 303 + 390 si diciembre        |
| Dashboard 24 h        | `GET /agents/dashboard/realtime`                                             |                               |
| Dashboard mensual     | `GET /agents/dashboard/monthly?month=&year=`                                  |                               |

---

## Normativa de referencia

- **Ley 37/1992** (IVA), **Orden HFP/112/2023** (modelo 390).
- **GDPR**, **AI Act 2024**, **eIDAS 2**, **RD 903/2025** (cannabis medicinal), **MiCA** (criptoactivos).

Documentación de componentes opcionales: `docs/COMPONENTES_OPCIONALES.md`.
