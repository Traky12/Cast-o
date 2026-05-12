FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY docker/api-gateway/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY docker/api-gateway/api_gateway.py /app/api_gateway.py
COPY docker/api-gateway/auth_jwt.py /app/auth_jwt.py

EXPOSE 8000
CMD ["uvicorn", "api_gateway:app", "--host", "0.0.0.0", "--port", "8000"]
