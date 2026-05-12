# CASTÚO API — producción (contexto = raíz del repo). Ver docs/deploy/CHECKLIST-CURSOR-HETZNER-D1.md
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -r backend/requirements.txt

COPY backend/ ./backend/
COPY frontend/public/ ./frontend/public/
COPY agrotech/ ./agrotech/
COPY static/ ./static/
COPY templates/ ./templates/
COPY iot/ ./iot/
COPY production/ ./production/
COPY compliance/ ./compliance/
COPY ecommerce/ ./ecommerce/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
