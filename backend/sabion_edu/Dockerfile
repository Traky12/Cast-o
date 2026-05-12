# SABION EDU v5.0 — Protocolo educativo federado, puerto 9500
FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn pydantic httpx

COPY edu_models.py edu_enroll.py edu_progress.py edu_certificates.py app_edu.py ./

EXPOSE 9500

ENV SABIONDA_URL=http://localhost:9000

CMD ["uvicorn", "app_edu:app", "--host", "0.0.0.0", "--port", "9500"]
