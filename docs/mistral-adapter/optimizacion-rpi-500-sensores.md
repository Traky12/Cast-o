# Optimización de RPi para 500+ sensores

Guía para escalar el nodo hidroponía a 500+ sensores (NFT, EC, pH, temperatura) con batches asíncronos, MQTT QoS 1 y límites de recursos.

---

## 1. Configuración de la Raspberry Pi

En la RPi, ejecutar:

```bash
sudo raspi-config
```

1. **Overclock** a 2.0 GHz (RPi 5) o 1.8 GHz (RPi 4).
2. **GPU memory** = 256 MB (para procesamiento de imágenes).
3. **Governor** = Performance.

Reiniciar la RPi:

```bash
sudo reboot
```

Verificar configuración tras el reinicio:

```bash
cat /boot/config.txt | grep "over_voltage"
vcgencmd measure_clock arm
```

---

## 2. Servicio `rpi-hidroponia` optimizado (Docker Compose)

Añadir o reemplazar el servicio en `docker-compose.hetzner.yml` (o en un override para 500+ sensores):

```yaml
services:
  rpi-hidroponia:
    image: castuo/rpi-hidroponia:optimized
    build:
      context: .
      dockerfile: Dockerfile.rpi
    networks:
      - castuo-network
    depends_on:
      - mqtt
      - backend
    environment:
      - MQTT_BROKER=${MQTT_BROKER:-mqtt}
      - HIDRO_SYSTEM_ID=1
      - SENSOR_LIMIT=500
      - MQTT_QOS=1
      - BUFFER_SIZE=1024
      - THREAD_POOL=8
    deploy:
      resources:
        limits:
          cpus: '3.0'
          memory: 2G
    volumes:
      - /dev/bus/usb:/dev/bus/usb
    privileged: true
    restart: always
    profiles:
      - hidroponia
```

---

## 3. Código: SensorManager para 500+ sensores

Procesamiento en batches asíncronos y envío a MQTT con QoS 1.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import paho.mqtt.client as mqtt

SENSOR_BATCH_SIZE = 50
MQTT_QOS = 1
THREAD_POOL = ThreadPoolExecutor(max_workers=8)

class SensorManager:
    def __init__(self):
        self.client = mqtt.Client(client_id="rpi-hidroponia-500", clean_session=False)
        self.client.qos = MQTT_QOS
        self.client.connect("mqtt-broker", 1883, 60)
        self.sensor_queue = asyncio.Queue(maxsize=SENSOR_BATCH_SIZE * 2)

    async def read_sensors(self):
        """Lee 500+ sensores en batches asíncronos."""
        while True:
            batch = []
            for _ in range(SENSOR_BATCH_SIZE):
                sensor_data = await self._read_sensor()
                batch.append(sensor_data)
                if len(batch) >= SENSOR_BATCH_SIZE:
                    await self._process_batch(batch)
                    batch = []

    async def _process_batch(self, batch):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(THREAD_POOL, self._send_to_mqtt, batch)

    def _send_to_mqtt(self, batch):
        """Envía datos a MQTT con QoS 1."""
        for data in batch:
            self.client.publish(
                f"hidroponia/sensores/{data['id']}",
                payload=data,
                qos=MQTT_QOS
            )

# Ejecutar
manager = SensorManager()
asyncio.run(manager.read_sensors())
```

---

## 4. Mosquitto optimizado para 500+ sensores

Ejemplo `mosquitto.conf`:

```conf
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
persistence true
persistence_location /mosquitto/data/
autosave_interval 300
max_queued_messages 10000
queue_qos0_messages true
per_listener_settings true

max_connections 1000
max_queued_messages 10000
max_inflight_messages 1000
max_queued_bytes 10000000
```

---

## 5. Benchmark y verificación

En la RPi:

```bash
sudo apt install stress-ng
stress-ng --cpu 4 --io 2 --vm 1 --vm-bytes 1G --timeout 60s --metrics-brief
```

Monitorizar en tiempo real:

```bash
docker stats rpi-hidroponia
docker logs mqtt-broker --tail 100
./salud-verificacion.sh
```

Salida esperada de salud:

- ✅ Fase 1: Health endpoint 200 OK
- ✅ Fase 2: Hidroponía → 500 sensores simulados (NFT 288 lechugas)
- ✅ Fase 4: ROOT MAESTRO (Fail2Ban activo)
- ✅ Fase 5: Documentación lista

---

## 6. Prueba de carga con k6

```bash
sudo apt install k6
```

Crear `load_test.js`:

```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 100,
  duration: '1m',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const res = http.get('http://localhost:8002/hidroponia/sistemas');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

Ejecutar:

```bash
k6 run load_test.js
```

---

## 7. Métricas de verificación

| Comando | Qué mide |
|--------|----------|
| `docker exec -it postgres psql -U user -d castuo_staging -c "SELECT * FROM pg_stat_activity;"` | Conexiones y queries PostgreSQL |
| `docker exec -it redis redis-cli info` | Memoria y keys Redis |
| `docker exec -it mqtt-broker mosquitto_ctrl dynsec listClients` | Clientes MQTT (requiere Mosquitto 2.x con dynsec) |

---

## 8. Tabla de métricas objetivo (500+ sensores)

| Métrica | Objetivo | Comando |
|---------|----------|---------|
| Latencia API | &lt; 500 ms (p95) | `k6 run load_test.js` |
| Uso de CPU (RPi) | &lt; 70% | `docker stats rpi-hidroponia` |
| Mensajes MQTT/segundo | 50–100 | `docker logs mqtt-broker --tail 50` |

---

## 9. Opciones de orquestación avanzada

- **K3s en RPi:** `curl -sfL https://get.k3s.io | sh -` y `kubectl apply -f rpi-cluster.yaml`
- **Balena:** `balena push castuo-rpi --source .`

---

## 10. Monitorización (Prometheus + Grafana)

Servicios en `docker-compose.hetzner.yml`:

```yaml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  depends_on:
    - prometheus
```

**Acceso:**

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (user: `admin`, pass: `admin`)

**Configurar dashboard en Grafana:**

1. Añadir data source: **Prometheus** → URL `http://prometheus:9090`
2. Importar dashboard: **"Docker and System Monitoring"** (ID: 10600)

Cambiar `.env` a valores de producción y repetir despliegue.

[Volver a Arquitectura](arquitectura-dehesas-edge.md) · [Deploy](deploy.md)
