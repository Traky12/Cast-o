# CASTUO_IA_AGENTS_v2.0 — Anytype ↔ FastAPI ↔ Agentes IA

**Arquitectura:** Anytype (Países Bajos) ↔ FastAPI Backend ↔ Vault PQC ↔ Docker Metrics → IA Bots/Agentes ↔ Workflows automáticos ↔ Métricas predeterminadas.

## Flujo

```
ANYTYPE OBJETOS → JSON API → AGENTES IA → SISTEMAS CASTÚO
Certificación(92%) → {health:✓, stage1:pass} → Bot Auditoría
Endpoint(8000)   → {cpu:23%, uptime:99.9%}   → Bot Monitoreo
Vault Key(Kyber) → {rotation:28d, seal:ready} → Bot Seguridad
Cliente(Agricultor) → {consent:✓, qr:scanned} → Bot Campo
```

## Métricas predeterminadas

| Agente      | Métrica       | Umbral crítico   | Acción auto    |
|------------|---------------|------------------|----------------|
| AUDITORÍA  | ISO 27001%    | < 95%            | Email Applus+  |
| VAULT      | Rotación días | < 30d            | Auto Kyber-768 |
| MONITOREO  | Uptime %      | < 99.5%          | Alert Telegram |
| CAMPO      | Consents GDPR | < 90% clientes   | QR reenvío     |

## Endpoints

- **POST /api/anytype** — Webhook: recibe JSON de objetos Anytype (type: Certificación, Endpoint, Vault Key, Cliente) y dispara los agentes según umbrales.
- **GET /api/anytype/metrics** — Métricas LIVE de los 4 agentes (dashboard).
- **GET /health** — Estado del servicio.

## Archivos

```
backend/agents/
├── anytype_webhook.py   # JSON → Objetos TRL8 → triggers
├── agente_auditoria.py  # ISO 27001 → alert Stage 2
├── agente_monitoreo.py  # Docker metrics → Telegram
├── agente_vault.py      # PQC Kyber-768 rotación
├── agente_campo.py      # QR + consents GDPR
├── app_agents.py       # FastAPI app (puerto 8001)
├── Dockerfile
└── README_AGENTS.md
```

## Docker

Desde la raíz del repo:

```bash
docker-compose -f docker-compose.agents.yml up -d
```

- **Ollama:** puerto 11434 (modelos locales para futura inferencia).
- **FastAPI Agents:** puerto 8001.

Variables opcionales: `BACKEND_URL`, `VAULT_URL`, `APPLUS_CERTIFICACION_EMAIL`, `SMTP_*`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALERT_CHAT_ID`, `AGENTE_*_UMBRAL`.

## Workflow P2P IA

1. **Campo** iPhone → Foto panel → Anytype QR Object.
2. P2P Sync WiFi → PC Gregorio → Export JSON.
3. **POST** a `http://localhost:8001/api/anytype` con el objeto.
4. FastAPI parsea → dispara **AGENTE_CAMPO** → Consent GDPR ✓.
5. Anytype Object → estado "Procesado IA" → Sync técnico Android.
6. Dashboard → **GET /api/anytype/metrics** → métricas LIVE.

## Ejemplo cuerpo POST /api/anytype o /api/anytype/webhook

```json
{
  "id": "cert-001",
  "type": "Certificación",
  "name": "ISO 27001 Stage 1",
  "properties": {"progress": 92},
  "relations": ["endpoint-001"]
}
```

Respuesta típica (incluye audit trail en `data_path`):

```json
{
  "status": "processed",
  "object_type": "Certificación",
  "agents_triggered": ["AGENTE_AUDITOR"],
  "agents_triggered_count": 1,
  "data_path": "backend/agents/data/anytype_20260316_123456.json",
  "results": { "auditoria": { "triggered": true, "action_result": "email_sent" } }
}
```

### cURL

```bash
# 1. Webhook con objeto Certificación
curl -X POST http://localhost:8001/api/anytype/webhook \
  -H "Content-Type: application/json" \
  -d '{"id":"cert-001","type":"Certificación","name":"ISO 27001 Stage 1","properties":{"progress":92},"relations":["endpoint-001"]}'

# 2. Dashboard métricas LIVE
curl http://localhost:8001/api/agents/metrics

# 3. Docker completo
docker-compose -f docker-compose.agents.yml up -d
```

### Workflow P2P IA completo

1. iPhone Campo → Anytype Foto → P2P WiFi 3s  
2. PC → JSON Export → POST /api/anytype/webhook  
3. FastAPI → Parse Object → Trigger 4 Agentes IA  
4. Ollama Llama3 (opcional) → Procesar → Update Anytype Object  
5. Android Técnico → Sync P2P → "Procesado IA" ✓  
6. Dashboard → GET /api/agents/metrics → Métricas LIVE
