# Exporters Prometheus (CASTUO-SYSTEM™)

## extrusora_exporter.py

Expone métricas de la extrusora (temperatura boquilla/cámara, setpoint, salida PID) en formato Prometheus.

- **Puerto**: 9100 (configurable con `EXTRUSORA_EXPORTER_PORT`).
- **Origen de datos**: MQTT `castu/extrusora/pid/telemetry` (preferido) o Serial `EXTRUSORA_SERIAL` (ej. `/dev/ttyACM0`).
- **Métricas**: `castu_extrusora_temp`, `castu_extrusora_camara_temp`, `castu_extrusora_setpoint`, `castu_extrusora_pid_output`, `castu_extrusora_pid_kp/ki/kd`, `castu_extrusora_motor_speed`, etc.

### Uso

```bash
pip install -r requirements.txt
export MQTT_BROKER=localhost  # opcional
python extrusora_exporter.py
```

En Prometheus, configurar un job que haga scrape de `host:9100/metrics`. Ver `castu-monitoring/prometheus/prometheus.yml` (job `extrusora`).
