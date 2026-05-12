Los componentes React + MUI + Recharts + Keycloak para control hidropónico CTAEX están en:

`frontend/ctaex-hydro-dashboard/src/pages/HidroponicControl.jsx`

(junto con `SensorHistoryChart.jsx` y `ParameterControl.jsx` en `src/components/`).

Motivo: ese directorio incluye `package.json` y Vite para resolver dependencias; `frontend/src/` del monorepo no tiene bundler propio en la raíz.
