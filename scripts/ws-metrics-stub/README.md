# WebSocket stub — métricas de demo

Sirve JSON `{ type, metrics }` cada ~3 s para probar un dashboard HTML **en la misma máquina** que el navegador.

**No uses `ws://localhost` en HTML servido a inversores remotos:** su `localhost` no es tu servidor. Expón `wss://` con TLS y auth en producción.

```bash
cd scripts/ws-metrics-stub
npm install
node server.js
```

Variables opcionales: `WS_METRICS_PORT` (default 3001), `WS_METRICS_HOST` (default `0.0.0.0`).

Contexto: [docs/architecture/SABIONDA-N8N-WEB-FRONTEND.md](../../docs/architecture/SABIONDA-N8N-WEB-FRONTEND.md).
