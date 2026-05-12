"use strict";

const WebSocket = require("ws");

const port = Number(process.env.WS_METRICS_PORT || 3001);
const host = process.env.WS_METRICS_HOST || "0.0.0.0";

let metrics = {
  active_cores: 3,
  total_cores: 8,
  avg_latency: 62,
  integrity: 100,
};

const wss = new WebSocket.Server({ host, port });

wss.on("connection", (ws) => {
  ws.send(JSON.stringify({ type: "init", metrics }));

  const tick = setInterval(() => {
    metrics = {
      ...metrics,
      avg_latency: 55 + Math.floor(Math.random() * 20),
    };
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "update", metrics }));
    }
  }, 3000);

  ws.on("close", () => clearInterval(tick));
});

console.log(`[castuo-ws-metrics-stub] ws://${host === "0.0.0.0" ? "localhost" : host}:${port}`);
