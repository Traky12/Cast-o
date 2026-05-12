FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir paho-mqtt==2.1.0
COPY bridge.py .
HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD python -c "import socket; s=socket.create_connection(('mosquitto-dev',1883),timeout=3); s.close()"
CMD ["python", "-u", "bridge.py"]
