# CASTUO_FEDERATED_IA_v3.0 — 3 nodos P2P + consenso + blockchain audit
FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic

COPY federated_coordinator.py blockchain_auditor.py agent_federation.py ml_predictor.py app_federated.py ./

EXPOSE 8001

CMD ["uvicorn", "app_federated:app", "--host", "0.0.0.0", "--port", "8001"]
