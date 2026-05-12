# Orquestador CASTUO v6.0 — Deploy y n8n

## Resumen

- **Master Agent:** `POST /castuo/master-agent` — Mistral con function calling (sabionda_ia, n8n_workflow, notion_update, money_stripe). Ejecuta tool calls en paralelo.
- **Money Microgreens:** `POST /money/microgreens` — Verificación Mistral + Stripe Checkout + webhook n8n venta.
- **Dashboard:** `frontend/public/control-center.html` — Consultas al Master Agent y botón checkout microgreens.

---

## 1. Mistral Function Calling — Orquestador central

En `backend/routers/orchestrator.py`:

- **Endpoint:** `POST /castuo/master-agent`
- **Body:** `{"query": "Estado completo sistema CTAEX"}` (o cualquier pregunta en lenguaje natural).
- **Tools definidos:** sabionda_ia, n8n_workflow, notion_update, money_stripe.
- **Flujo:** Mistral devuelve `tool_calls` → se ejecutan en paralelo → respuesta `{ "orchestration": [...], "ctaex_ready": true }`.

Variables de entorno:

- `MISTRAL_API_KEY` — Obligatorio para usar tools.
- `MISTRAL_API_URL` — Opcional (por defecto `https://api.mistral.ai`).
- `MISTRAL_ORCHESTRATOR_MODEL` — Opcional (por defecto `mistral-large-latest`).
- `N8N_WEBHOOK_URL` — Para la tool `n8n_workflow` (trigger n8n).
- `N8N_WEBHOOK_SALE_URL` — Usado por `POST /money/microgreens` al completar sesión Stripe.

---

## 2. n8n Workflows — Mistral triggers

Workflow sugerido **"castuo-orchestrator"** en n8n:

1. **HTTP Trigger** — `POST /n8n/castuo-trigger` (o la URL que expongas como `N8N_WEBHOOK_URL`).
2. **Mistral Agent / Function calling** — Recibe el payload; si el master-agent ya ejecutó las tools, este paso puede ser opcional o usarse para un segundo nivel.
3. **Switch** — Por tipo: sabionda | money | notion | gaia.
4. **Ejecución en paralelo** — Llamadas a APIs (backend, Notion, etc.).
5. **Notion** — Actualizar CTAEX log y dashboard (page_id configurado).

En el backend, la tool `n8n_workflow` hace `POST` a `N8N_WEBHOOK_URL` con `{ "workflow_id": "<id>", "source": "castuo-master-agent" }`. Configura en n8n un webhook que reciba ese body y enrute al workflow correspondiente.

---

## 3. Notion — Sincronización en tiempo real

El dashboard `control-center.html` llama a `/castuo/master-agent`. Si Mistral decide usar la tool `notion_update`, el backend devuelve un stub (en producción se puede conectar a la API de Notion con `NOTION_API_KEY` y actualizar la página del roadmap).

Ejemplo de actualización (frontend o backend):

- Página Notion: `ctaex-roadmap-abc123`.
- Propiedades: Status (🟢 LIVE / 🔴 Pending), LER (número), Valor (rich_text).

La tool `notion_update` en el orquestador está como stub; se puede sustituir por una llamada real a `PATCH https://api.notion.com/v1/pages/{page_id}`.

---

## 4. Money / Stripe — Microgreens e-commerce

**Endpoint:** `POST /money/microgreens`  
**Body:** `{"batch_id": "MG-2026-03-14"}` (opcional, por defecto ese lote).

- Mistral verifica (en una frase) si el lote está certificado; si no hay `MISTRAL_API_KEY`, se asume OK.
- Se crea una sesión de Stripe Checkout (25 €/kg por defecto).
- Si existe `N8N_WEBHOOK_SALE_URL`, se envía `POST` con `{ "batch_id", "session_id", "source": "castuo-money" }` para registrar la venta en n8n.

Variables:

- `STRIPE_SECRET` — Obligatorio para crear la sesión.
- `CASTUO_SUCCESS_URL`, `CASTUO_CANCEL_URL` — URLs de retorno (por defecto 89.167.5.233).
- `N8N_WEBHOOK_SALE_URL` — Webhook “venta registrada”.

En el frontend, si se define `window.STRIPE_PK` (clave pública Stripe) antes de cargar el script, el botón “Money Microgreens” redirige a Stripe Checkout; si no, se muestra el `stripe_session` en pantalla.

---

## 5. Dashboard unificado (control-center.html)

- **Sección Mistral Master Agent:** input de consulta + botón “Ejecutar” → respuesta JSON en `#response`.
- **Cards:** Sabionda LER, n8n Workflows, Notion CTAEX, Money Microgreens — al hacer clic rellenan la consulta y ejecutan el master agent (o en “Money” llaman directamente a `POST /money/microgreens` y redirigen a Stripe si hay `STRIPE_PK`).

Para usar Stripe redirect en producción, en el HTML o en un `config.js` cargado antes:

```html
<script>window.STRIPE_PK = 'pk_live_...';</script>
<script src="https://js.stripe.com/v3/"></script>
```

---

## 6. Deploy total (5 min)

```bash
cd /castuo-ctaex   # o raíz del repo Castuo-System

# 1. Backend + integraciones (orquestador ya incluido)
docker-compose up -d --build backend
# Si usas n8n en el mismo compose:
# docker-compose up -d --build backend n8n

# 2. Frontend unificado (control-center ya está en frontend/public)
# Si tienes servicio frontend separado:
# docker-compose restart frontend
# Nginx sirve frontend/public; solo asegura que control-center.html esté incluido en el volumen.

# 3. Test master agent
curl -X POST http://localhost:8000/castuo/master-agent \
  -H "Content-Type: application/json" \
  -d '{"query": "Estado completo sistema CTAEX"}'

# 4. Verificar dashboard (si Nginx/proxy sirve estáticos en 3000 o 80)
curl -s http://localhost:3000/control-center.html | head -20
```

En producción (ej. 89.167.5.233):

```bash
curl -X POST https://89.167.5.233:8000/castuo/master-agent \
  -H "Content-Type: application/json" \
  -d '{"query": "Estado completo sistema CTAEX"}'

curl https://89.167.5.233/control-center.html
```

---

## Checklist

| Componente              | Variable / Acción                                      |
|-------------------------|--------------------------------------------------------|
| Mistral                 | `MISTRAL_API_KEY`                                      |
| Orquestador             | `POST /castuo/master-agent`                            |
| n8n trigger             | `N8N_WEBHOOK_URL`                                      |
| n8n venta               | `N8N_WEBHOOK_SALE_URL`                                 |
| Stripe                  | `STRIPE_SECRET`; en frontend `STRIPE_PK` para redirect |
| Dashboard               | `control-center.html` en `frontend/public`              |
| Notion (opcional)       | Implementar en tool `notion_update` con `NOTION_API_KEY` |
