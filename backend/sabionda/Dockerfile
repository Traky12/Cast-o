# SABIONDA_MASTER_v4.0 — IA Suprema Kyber-1024, puerto 9000
FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic

COPY crypto_pqc.py byzantine_consensus.py agent_hierarchy.py merkle_auditor.py ml_oracle.py sabionda_master.py app_sabionda.py ./

EXPOSE 9000

ENV KYBER_MODE=1024
ENV PEERS_ENCRYPTED=true
ENV CONSENSUS_THRESHOLD=0.66
ENV ML_REVENUE_TARGET=150000

CMD ["uvicorn", "app_sabionda:app", "--host", "0.0.0.0", "--port", "9000"]
