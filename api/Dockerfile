# CASTÚO-SYSTEM API (JEREMIE + Mistral Adapter)
# Build desde raíz del repo: docker build -t castuo/mistral-api -f api/Dockerfile .

FROM python:3.11-slim

WORKDIR /app

# Dependencias API + Mistral Adapter (pandas, cryptography, requests)
COPY api/requirements-api.txt requirements-api.txt
RUN pip install --no-cache-dir -r requirements-api.txt

# Código API (main.py + mistral_castuo_adapter.py)
COPY api/ /app/api/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
