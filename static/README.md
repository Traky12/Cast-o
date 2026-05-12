# Archivos estáticos — CASTÚO-SYSTEM

## Contenido

| Archivo | Rol |
|---------|-----|
| `favicon.ico` | Opcional; **prioridad** sobre SVG si existe. |
| `favicon.svg` | Icono vectorial (gota / territorio); usado vía `/favicon.ico` si no hay ICO. |

La plantilla del panel está en **`templates/dashboard.html`** (no en `static/`).

## Rutas (FastAPI)

1. **`/static/*`** — `StaticFiles` si existe el directorio `static/` en la raíz del repo.
2. **`/favicon.ico`** — ICO → SVG → `204` sin cuerpo (ver `backend/main.py`).
3. **`/dashboard`** — HTML leído desde `templates/dashboard.html` (sin Jinja2).
4. **`/`** — Si `Accept` incluye `text/html`, redirección **307** a `/dashboard`; si no, JSON con `endpoints`.

## Personalización

- Añadir `favicon.ico` en `static/` para clientes que no usen SVG.
- Editar `templates/dashboard.html` para enlaces o bloque SSE; el hub superior es HTML estático.

## Pruebas rápidas

```bash
curl -sI http://127.0.0.1:8000/favicon.ico
curl -sI http://127.0.0.1:8000/dashboard
curl -sI -H "Accept: text/html" http://127.0.0.1:8000/
curl -s http://127.0.0.1:8000/
```

Puerto según `uvicorn` (8000 / 8001).
