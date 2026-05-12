# Despliegue CASTUO v6.0 en CTAEX (≈30 min)

Pasos optimizados para poner en marcha trazabilidad blockchain, control ambiental, certificación CTAEX y e-commerce Stripe.

## 1. Instalación de dependencias (2 min)

```bash
# Backend
cd backend
pip install -r requirements.txt   # incluye stripe, python-dotenv

# Frontend (si usas Node para build)
cd ../frontend
npm install
```

## 2. Variables de entorno

Crear `.env` en la raíz o en `backend/`:

```bash
GAIA_CHAIN_RPC_URL=          # opcional; si vacío se usa cliente stub
GAIA_API_KEY=                # opcional para CTAEX
STRIPE_SECRET=sk_test_...     # clave secreta Stripe (CTAEX)
POSTGRES_PASSWORD=ctaex_2026 # para Docker
```

## 3. Endpoints CTAEX (ya integrados en el backend)

| Ruta | Método | Uso |
|------|--------|-----|
| `/trazabilidad/gaia` | POST | Registrar datos en GaiaChain (product_id, batch_id, env_data) |
| `/microgreens/sensors` | GET | Datos sensores por cama (`?bed_id=mg1`) |
| `/certificacion/ctaex` | GET | Certificado CTAEX + QR (`?batch_id=MG-2026-03-14`) |
| `/ecommerce/create-checkout` | POST | Sesión Stripe (body: `batch_id`, opcional `success_url`, `cancel_url`, `unit_amount`) |

## 4. Dashboard e-commerce

- **Archivo:** `frontend/public/ecommerce.html`
- **URL:** Servir desde el frontend (puerto 3000) y apuntar la API con `?api=http://IP:8000` o configurando `window.API_BASE` antes de cargar el script.
- **Stripe:** En la página definir `window.STRIPE_PK = 'pk_test_...'` para habilitar el botón de pago.

## 5. Docker CTAEX

La imagen del backend se construye con **contexto en la raíz del repo** para incluir `blockchain`, `production`, `compliance`, `ecommerce` (ver `docker/Dockerfile`).

```bash
# Desde la raíz del repo
export STRIPE_SECRET=sk_test_...
export DB_PASSWORD=ctaex_2026
docker compose -f docker/docker-compose.ctaex.yml up -d --build
```

- Backend: http://localhost:8000  
- Frontend (nginx estático): http://localhost:3000 → abrir `http://localhost:3000/ecommerce.html?api=http://localhost:8000`

## 6. Verificación

```bash
# Trazabilidad
curl http://localhost:8000/trazabilidad/gaia -X POST -H "Content-Type: application/json" -d '{"product_id":"MG-2026-03-14"}'

# Sensores
curl "http://localhost:8000/microgreens/sensors?bed_id=mg1"

# Certificado
curl "http://localhost:8000/certificacion/ctaex?batch_id=MG-2026-03-14"
```

## 7. Checklist CTAEX

- [ ] GaiaChain trazabilidad: `POST /trazabilidad/gaia` devuelve `tx_hash`
- [ ] Sensores: `GET /microgreens/sensors?bed_id=mg1` devuelve JSON
- [ ] Certificación: `GET /certificacion/ctaex?batch_id=...` devuelve QR y normativas
- [ ] Stripe: `STRIPE_SECRET` configurado y checkout redirige a Stripe
- [ ] Dashboard: `ecommerce.html` carga y llama a la API (usar `?api=...` si API en otro puerto/host)

## 8. Valor CTAEX (referencia)

- Trazabilidad blockchain + certificados CTAEX  
- Control ambiental (sensores, ósmosis, ozono)  
- E-commerce Stripe + integración Shopify existente  
- Certificación CTAEX (ISO 22000, GlobalGAP, CTAEX TRL7)
