# Gestión de estáticos y dashboard

`backend/main.py` es la **aplicación completa** Castúo (routers, métricas, seguridad). No sustituir por un `main.py` mínimo de ejemplo: las rutas de favicon, `/dashboard` y `/` están integradas ahí con `Path` al repo (`_root`).

## Rutas implementadas

| Ruta | Comportamiento | HTTP |
|------|----------------|------|
| `/static/*` | Archivos bajo `static/` si el directorio existe | 200/404 |
| `/favicon.ico` | 1) `static/favicon.ico` 2) `static/favicon.svg` como `image/svg+xml` 3) **204** vacío | 200/204 |
| `/dashboard` | Contenido de `templates/dashboard.html` (hub de enlaces + SSE + cámara opcional) | 200 |
| `/agents/dashboard/stream` | SSE `event: metric_update` (~3 s) | 200 |
| `/agents/camera/stream` | SSE `event: camera_update` (métricas MotionEye; requiere env/config) | 200 |
| `/agents/camera/frame/latest` | Proxy snapshot JPEG | 200/502 |
| `/` | `Accept` con `text/html` → **307** a `/dashboard`; si no → JSON `status` + `endpoints` | 307/200 |

## JSON en `/` (clientes no HTML)

Ejemplo de forma:

```json
{
  "service": "sabionda",
  "status": "operational",
  "version": "2.0",
  "endpoints": {
    "dashboard": "/dashboard",
    "docs": "/docs",
    "redoc": "/redoc",
    "metrics": "/metrics",
    "health": "/agents/system/health"
  }
}
```

## Cómo probar

```bash
BASE=http://127.0.0.1:8000
curl -sI "$BASE/favicon.ico"
curl -sI "$BASE/dashboard"
curl -sI -H "Accept: text/html" "$BASE/"
curl -s "$BASE/"
curl -sI "$BASE/docs"
curl -sI "$BASE/agents/system/health"
```

## Validación rápida

| Prueba | Comando | Esperado |
|--------|---------|----------|
| Favicon con SVG | `curl -sI …/favicon.ico` | 200, `image/svg+xml` o ICO |
| Sin iconos | (sin ficheros en `static/`) | 204 |
| Dashboard | `curl -sI …/dashboard` | 200 |
| Raíz HTML | `Accept: text/html` | 307 → `/dashboard` |
| Raíz JSON | `curl -s …/` | JSON con `endpoints` |

## Notas

- **Sin Jinja2** en el dashboard: lectura directa del fichero.
- **Vegetal alloys:** rutas bajo `/vegetal-alloys/` en OpenAPI.
- **CORS** global se configura en `main.py` (no duplicar bloques `allow_origins=["*"]` en ejemplos aislados sin revisar política).

## Referencias

- `static/README.md`
- `scripts/systemd/README.md` (deploy servidor)
- [PRONTUARIO-MAESTRO-DEPLOY-REAL-HETZNER.md](./PRONTUARIO-MAESTRO-DEPLOY-REAL-HETZNER.md)
