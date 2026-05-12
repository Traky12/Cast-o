FROM python:3.12-slim

WORKDIR /app

COPY backend/integrations/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/integrations/mqtt_bridge.py /app/mqtt_bridge.py

CMD ["python", "/app/mqtt_bridge.py"]
