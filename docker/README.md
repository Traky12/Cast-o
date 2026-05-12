# Docker para CASTUO-SYSTEM en CTAEX

- **Despliegue Hetzner/ARSYS (Sabionda, Nginx):** [DEPLOY-HETZNER-ARSYS.md](../docs/DEPLOY-HETZNER-ARSYS.md)
- **Producción CTAEX (IP whitelist + backups):** [CTAEX-PRODUCTION-SECURITY-BACKUPS.md](../docs/CTAEX-PRODUCTION-SECURITY-BACKUPS.md)
- **Watchdogs y monitoreo CTAEX:** [CTAEX-WATCHDOGS-MONITORING.md](../docs/CTAEX-WATCHDOGS-MONITORING.md)
- **Agentes personalizables SABIONDA:** [AGENTS-GUIDE.md](../docs/AGENTS-GUIDE.md)
- **Cuentas Pro (jerarquía, permisos, ética):** [PRO-ACCOUNTS-GUIDE.md](../docs/PRO-ACCOUNTS-GUIDE.md)

## Estructura del proyecto

El backend necesita los módulos de la raíz del repo. La imagen se construye con **contexto en la raíz**:

```
castuo-ctaex/
├── backend/          # FastAPI (main.py, routers, etc.)
├── blockchain/       # GaiaChain (gaia_chain.py)
├── production/       # Control ambiental, microgreens, agua
├── compliance/       # Certificaciones CTAEX, AEMPS
├── ecommerce/        # Connector Shopify, WooCommerce, Stripe
├── iot/              # Opcional (hidroponía)
├── frontend/
│   └── public/       # ecommerce.html, estáticos
└── docker/
    ├── Dockerfile    # Backend con monorepo
    ├── docker-compose.ctaex.yml
    ├── docker-compose.production.yml
    ├── mosquitto.conf
    └── README.md
```

## Construcción y despliegue

### 1. Construir imágenes (desde la raíz del proyecto)

```bash
docker compose -f docker/docker-compose.ctaex.yml build
```

### 2. Iniciar servicios

```bash
docker compose -f docker/docker-compose.ctaex.yml up -d
```

### 3. Variables de entorno (.env en la raíz, no versionado)

```env
GAIA_API_KEY=tu_clave_gaia_ctaex
STRIPE_SECRET=sk_test_...
DB_PASSWORD=ctaex_2026_segura
GAIA_CHAIN_RPC_URL=          # opcional
SHOPIFY_API_KEY=             # opcional
WOOCOMMERCE_API_KEY=         # opcional
```

### 4. Verificación

```bash
curl http://localhost:8000/docs
curl "http://localhost:8000/microgreens/sensors?bed_id=mg1"
curl -X POST http://localhost:8000/trazabilidad/gaia -H "Content-Type: application/json" -d '{"product_id":"MG-2026-03-14"}'
```

- **API:** http://localhost:8000  
- **Dashboard:** http://localhost:3000/ecommerce.html?api=http://localhost:8000  

## Despliegue en servidor CTAEX (ej. 89.167.5.233)

```bash
git clone https://github.com/tu-repo/castuo-ctaex.git
cd castuo-ctaex

# Crear .env
echo "GAIA_API_KEY=tu_clave_gaia_ctaex" >> .env
echo "STRIPE_SECRET=sk_test_..." >> .env
echo "DB_PASSWORD=ctaex_2026_segura" >> .env

# Construir y levantar
docker compose -f docker/docker-compose.ctaex.yml build
docker compose -f docker/docker-compose.ctaex.yml up -d
```

- Dashboard: http://89.167.5.233:3000/ecommerce.html?api=http://89.167.5.233:8000  
- API Docs: http://89.167.5.233:8000/docs  

## Desarrollo vs producción

- **Producción:** Sin volúmenes en `docker-compose.ctaex.yml`; se usa solo la imagen construida.
- **Desarrollo:** Descomentar los `volumes` del servicio `backend` en el compose para montar código local (backend, blockchain, production, compliance, ecommerce) y recargar sin reconstruir.

## Mosquitto

Si se usa autenticación, crear `docker/passwords.txt`:

```bash
# Ejemplo con mosquitto_passwd (dentro del contenedor o con imagen mosquitto)
docker run -it --rm -v $(pwd)/docker:/data eclipse-mosquitto mosquitto_passwd -b /data/passwords.txt castuo_iot castuo_password_123
```

Y en `mosquitto.conf` tener `password_file /mosquitto/config/passwords.txt`.

## Stripe y webhook CTAEX

- Definir `STRIPE_SECRET` (y opcionalmente `STRIPE_WEBHOOK_SECRET`) en `.env`.
- En Stripe Dashboard → Webhooks, añadir endpoint `https://tu-dominio/ecommerce/webhook` y evento `checkout.session.completed`; copiar el *Signing secret* a `STRIPE_WEBHOOK_SECRET`.
- El backend puede leer secrets desde archivos: `STRIPE_SECRET_FILE`, `STRIPE_WEBHOOK_SECRET_FILE`. Ver `docs/CTAEX-SECURITY.md`.

## BookStack (Knowledge Base) ✅ LISTO

- **castuo-bookstack/:** Knowledge Base integrada con Hetzner, n8n, Sabionda IA, Mistral y Notion. Producción con bind mounts `./data`, `./db`; healthchecks; seguridad enterprise (UFW, MFA, roles).
- **Contenido**: `docker-compose.yml`, `.env.example`, `README.md`, `test-bookstack.sh`, `n8n-workflow-sabionda-bookstack.json`.
- **Levantar**: `cd docker/castuo-bookstack && cp .env.example .env && docker compose up -d` (editar `.env` con contraseñas; opcional: `openssl rand -base64 32` / `openssl rand -base64 48`).
- **Verificación**: `./test-bookstack.sh` (script en el mismo directorio).
- **Acceso**: https://tu-ip:8080 — Usuario inicial `admin@castuo.local`. Ver [castuo-bookstack/README.md](castuo-bookstack/README.md) y [docs/operations/BookStack-Integration.md](../docs/operations/BookStack-Integration.md).

## Otros compose

- **docker-compose.production.yml:** Producción completa (Ganache, Prometheus, Grafana, etc.).
- **docker-compose.ctaex.yml:** Stack mínimo CTAEX (backend, frontend estático, postgres, mqtt).
- **nginx-ctaex.conf:** Ejemplo de proxy inverso para CTAEX (HTTPS, rutas API y frontend).
