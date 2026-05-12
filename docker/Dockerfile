# docker/Dockerfile — Backend CASTUO con monorepo (production, compliance, ecommerce, blockchain)
# Construir desde la raíz del repo: docker build -f docker/Dockerfile .

FROM python:3.10-slim AS backend-builder

ENV PYTHONPATH=/app
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copiar todo el repositorio (raíz = contexto de build)
COPY . .

# Instalar dependencias Python del backend
RUN pip install --no-cache-dir -r backend/requirements.txt

# --- Imagen final ---
FROM python:3.10-slim
WORKDIR /app

# Copiar solo lo necesario desde el builder
COPY --from=backend-builder /app/backend /app/backend
COPY --from=backend-builder /app/blockchain /app/blockchain
COPY --from=backend-builder /app/production /app/production
COPY --from=backend-builder /app/compliance /app/compliance
COPY --from=backend-builder /app/ecommerce /app/ecommerce

# Opcional: descomentar si existe directorio iot en el repo
# COPY --from=backend-builder /app/iot /app/iot

# Instalar solo dependencias en imagen final (sin compilación pesada)
RUN pip install --no-cache-dir -r backend/requirements.txt
# curl para healthcheck Docker
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
