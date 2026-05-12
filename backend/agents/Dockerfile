# CASTUO_IA_AGENTS_v2.0 — Anytype ↔ FastAPI. Puerto 8001.
FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn httpx

COPY anytype_webhook.py app_agents.py ./
COPY agente_auditoria.py agente_monitoreo.py agente_vault.py agente_campo.py ./

EXPOSE 8001

CMD ["uvicorn", "app_agents:app", "--host", "0.0.0.0", "--port", "8001"]
