# Dashboard hidropónico CTAEX (React + MUI + Keycloak)

## Requisitos

- Node 18+
- Backend CASTÚO con `hydro_remote` router y `AUTH_DISABLED=true` **o** Keycloak con cliente público PKCE para este front.

## Desarrollo

```bash
cd frontend/ctaex-hydro-dashboard
cp .env.example .env
npm install
npm run dev
```

Abre `http://127.0.0.1:5175/hidroponic/zone_cannabis_1`.

Registra en Keycloak un cliente `ctaex-hydro-dashboard` (público, PKCE, URL válidas de redirección para `localhost:5175`).

Las rutas `/api/*` se proxifican a `VITE_PROXY_TARGET` (por defecto backend 8000).

## Equivalencia de rutas

Los componentes solicitados como `frontend/src/pages/HidroponicControl.js` viven aquí en `src/pages/HidroponicControl.jsx` por ser la app empaquetable con dependencias (MUI, Recharts, Keycloak).
