# ──────────────────────────────────────────────────────────────
# CASTÚO-SYSTEM™ API v3.1.1 — Dockerfile multi-stage (producción)
# ──────────────────────────────────────────────────────────────

# Stage 1: builder
FROM python:3.12-slim AS builder

RUN useradd -m castuo
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

# Stage 2: runtime mínimo sin caché de pip
FROM python:3.12-slim

RUN useradd -m castuo
WORKDIR /app

COPY --from=builder --chown=castuo:castuo /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=castuo:castuo . .
RUN chown -R castuo:castuo /app

USER castuo

ENV PYTHONPATH=/app
ENV VIRTUAL_ENV=/opt/venv

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import requests; requests.get('http://127.0.0.1:8000/health', timeout=2).raise_for_status()" || exit 1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
