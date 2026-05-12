# CASTÚO-SYSTEM™ v3.1 — FastAPI Dockerfile
# Multi-stage: dev (hot-reload) y prod (optimizado)

# ── Stage base ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage dev (hot-reload con uvicorn --reload) ───────────────────────────────
FROM base AS dev
# En dev el código se monta como volumen; no hace falta COPY
EXPOSE 8000
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]

# ── Stage prod ────────────────────────────────────────────────────────────────
FROM base AS prod
COPY . .
EXPOSE 8000
# Uvicorn sin --reload, sin --log-level debug
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
