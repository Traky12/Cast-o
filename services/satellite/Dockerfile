FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/satellite/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/satellite /app

# Default process: API endpoint for NDVI stats.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
