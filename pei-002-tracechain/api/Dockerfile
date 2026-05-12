FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Contexto de build: directorio api/ (docker build -f api/Dockerfile api)
COPY . .

RUN mkdir -p /app/data

ENV PEI002_STUB_BEARER_TOKEN=""

EXPOSE 8010
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
