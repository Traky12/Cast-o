# Panel administrativo Water / CTAEX (HTMX + Alpine)

Interfaz estática que habla con el **FastAPI** existente (`/water/ctaex/...`).

## Configuración inicial (~5 min)

Desde la raíz del repositorio (ajusta la URL del clon a tu fork):

```bash
git clone https://github.com/Traky12/Castuo-system.git
cd Castuo-system
cp .env.example .env
# Editar .env con credenciales reales (WATER_USAGE_REPORT_KEY, AI_INTEGRATION_KEY, etc.)
pip install -r backend/requirements.txt
```

## Arranque (~10 min)

**Terminal 1 — API** (hay que ejecutarlo con el paquete `backend` en el path; la raíz del repo suele ser el cwd correcto):

```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — panel estático** (sirve `frontend/public`, no solo una carpeta suelta):

```bash
python scripts/serve_water_admin.py --port 3000
```

Abre el panel: [http://127.0.0.1:3000/water-admin/](http://127.0.0.1:3000/water-admin/)  
(En Windows puedes usar `start http://127.0.0.1:3000/water-admin/` en lugar de `open`.)

## Verificar conexión

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/water/ctaex/health
```

En el panel → **Dashboard** → botón **Cargar Health CTAEX** (HTMX contra `GET /water/ctaex/health`, sin claves).

Si el API ya está levantado (p. ej. con Docker), solo ejecuta `python scripts/serve_water_admin.py` y abre la misma URL del panel.

## Producción (Docker / nginx)

Tras `docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build`, el panel queda en la **misma origen** que el API detrás de nginx:

`https://TU_DOMINIO/water-admin/`

Define en `.env.production` las claves `WATER_USAGE_REPORT_KEY` y `AI_INTEGRATION_KEY`; en el navegador, **Configuración** → pega las mismas en X-USAGE-REPORT-KEY y X-AI-KEY. Deja **API base** vacío para usar el origen actual (recomendado). Opcional: `CASTUO_CORS_ALLOW_WILDCARD=false` y `CASTUO_EXTRA_CORS_ORIGINS` si sirves el front en otro dominio.

## Configuración (obligatoria)

En el panel → **Configuración**:

| Campo | Uso |
|--------|-----|
| API base | Ej. `http://127.0.0.1:8000` o `https://api.castuo-system.es` |
| X-USAGE-REPORT-KEY | Misma clave que `WATER_USAGE_REPORT_KEY` en el servidor |
| X-AI-KEY | Misma clave que `AI_INTEGRATION_KEY` (roles IA) |

Se guardan en **localStorage** del navegador; no las commitees.

## Endpoints usados

- `GET /water/ctaex/subscription/billing-summary` — dashboard y clientes
- `GET /water/ctaex/subscription/usage-report` — trazas recientes
- `GET /water/ctaex/subscription/certification` — tabla de facturas e informe JSON
- `POST /water/ctaex/subscription/generate-invoices` — generar borradores del mes actual
- `GET /water/ctaex/subscription/ai/monitoring|health|enterprise-blueprint` — cabecera `X-AI-KEY`
- `GET /water/ctaex/health` — público (botón y demo HTMX)

## CORS

`backend/main.py` incluye `http://localhost:3000`, `http://127.0.0.1:3000` y más orígenes; si cambias puerto u origen, ajusta CORS en el API.

## Guion demo CTAEX (referencia)

1. **Mensaje inicial**: automatización de informes/facturación vía API, parámetros en vivo donde haya sensores integrados, trazabilidad alineada con política CTAEX/EU.
2. **Panel**: Configuración → API base `http://127.0.0.1:8000` (o `http://localhost:8000`) + claves; Dashboard → **Cargar Health CTAEX**; pestañas Facturación / Informes / Roles IA con las claves adecuadas.
3. **API en terminal**: usar [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) para enseñar endpoints reales del despliegue. Rutas tipo `POST /api/v1/siex/...` del guion genérico pueden no existir en esta rama: no las cites como probadas sin comprobarlas en `/docs`.

## Checklist demo

| Item | Notas |
|------|--------|
| Backend en :8000 | `uvicorn backend.main:app --reload --port 8000` desde la raíz del repo |
| Panel en :3000 | `python scripts/serve_water_admin.py` |
| CORS | Orígenes 3000 permitidos en `backend/main.py` |
| HTMX | Botón **Cargar Health CTAEX** → `GET /water/ctaex/health` |
| Claves | Panel → Configuración (localStorage); coherente con `.env` del servidor |
