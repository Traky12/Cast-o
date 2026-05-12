# CTAEX: Rearmadores (watchdogs), monitoreo y resiliencia

Sistema de rearmadores automáticos para detectar fallos y reiniciar servicios, más Prometheus/Grafana, logrotate y notificaciones Slack.

---

## 1. Rearmadores automáticos (watchdogs)

### 1.1 Scripts

| Script | Función | Intervalo |
|--------|--------|-----------|
| `scripts/docker_watchdog_ctaex.sh` | Comprueba backend, frontend, postgres, mqtt; reinicia si no están `running` | 60 s |
| `scripts/nginx_watchdog_ctaex.sh` | Comprueba que Nginx esté activo; `systemctl restart nginx` si no | 60 s |
| `scripts/postgres_watchdog_ctaex.sh` | `pg_isready` en contenedor postgres; reinicia servicio si no responde | 60 s |
| `scripts/mqtt_watchdog_ctaex.sh` | Comprueba proceso mosquitto en contenedor mqtt; reinicia si no | 60 s |
| `scripts/disk_watchdog_ctaex.sh` | Uso de disco; alerta si ≥ umbral (por defecto 90 %) | 300 s |

Variables de entorno opcionales:

- **Todos:** `LOG_FILE` (ej. `/var/log/castuo/docker_watchdog.log`), `NOTIFY_SCRIPT` (ej. `scripts/notify_slack_ctaex.sh`).
- **Docker/Postgres/MQTT:** `REPO_ROOT`, `COMPOSE_FILE`.
- **Disco:** `DISK_THRESHOLD` (default 90), `DISK_CHECK_INTERVAL` (default 300).

### 1.2 Servicios systemd

Copiar las unidades desde `scripts/systemd/` y ajustar rutas (`/root/castuo-ctaex` → tu ruta):

```bash
# Ajustar REPO y usuario (ej. /home/ubuntu/castuo-ctaex y User=ubuntu)
REPO="/root/castuo-ctaex"
sudo sed "s|/root/castuo-ctaex|$REPO|g" scripts/systemd/docker-watchdog-ctaex.service | sudo tee /etc/systemd/system/docker-watchdog-ctaex.service
# Repetir para nginx-watchdog-ctaex, postgres-watchdog-ctaex, mqtt-watchdog-ctaex, disk-watchdog-ctaex

sudo systemctl daemon-reload
sudo systemctl enable docker-watchdog-ctaex nginx-watchdog-ctaex postgres-watchdog-ctaex mqtt-watchdog-ctaex disk-watchdog-ctaex
sudo systemctl start docker-watchdog-ctaex nginx-watchdog-ctaex postgres-watchdog-ctaex mqtt-watchdog-ctaex disk-watchdog-ctaex
sudo systemctl status docker-watchdog-ctaex nginx-watchdog-ctaex
```

Los `.service` asumen que los scripts están en `$REPO/scripts/` y que `NOTIFY_SCRIPT` apunta a `$REPO/scripts/notify_slack_ctaex.sh`.

### 1.3 Notificaciones Slack

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
./scripts/notify_slack_ctaex.sh "Mensaje de prueba CASTUO-CTAEX"
```

En los watchdogs, definir `NOTIFY_SCRIPT` (o usar las variables en el `.service`) para que, ante fallo, se llame a este script con el mensaje de alerta.

### 1.4 Logs de los watchdogs

```bash
tail -f /var/log/castuo/docker_watchdog.log
tail -f /var/log/castuo/nginx_watchdog.log
tail -f /var/log/castuo/postgres_watchdog.log
tail -f /var/log/castuo/mqtt_watchdog.log
tail -f /var/log/castuo/disk_watchdog.log
```

---

## 2. Health checks en Docker

En `docker-compose.ctaex.yml`:

- **backend:** `GET http://localhost:8000/health` cada 30 s (timeout 10 s, 3 reintentos).
- **postgres:** `pg_isready -U castuo_admin` cada 30 s.

El backend expone `/health` (200 + `{"status":"ok"}`) y `/metrics` (Prometheus).

```bash
docker compose -f docker/docker-compose.ctaex.yml ps
# Estado "healthy" cuando los healthchecks pasan
```

---

## 3. Prometheus y Grafana

### 3.1 Arranque

Los servicios `prometheus` y `grafana` están definidos en `docker-compose.ctaex.yml`:

```bash
docker compose -f docker/docker-compose.ctaex.yml up -d prometheus grafana
```

- **Prometheus:** http://localhost:9090 (scrape de `backend:8000/metrics`).
- **Grafana:** http://localhost:3001 (usuario `admin`, contraseña por defecto `admin` o `GRAFANA_ADMIN_PASSWORD`).

### 3.2 Configuración Prometheus

En `docker/prometheus.yml` están definidos los jobs `prometheus` y `backend` (métricas del FastAPI vía Instrumentator).

### 3.3 Alertas en Grafana

En Grafana: Alerting → Create alert rule. Ejemplos:

| Alerta | Condición (PromQL) | Acción |
|--------|--------------------|--------|
| Backend caído | `up{job="backend"} == 0` | Notificar + reinicio vía watchdog |
| Latencia API alta | `http_request_duration_seconds_bucket{job="backend", le="2"} / http_request_duration_seconds_count < 0.95` (ejemplo) | Revisar logs |
| Disco | Usar node_exporter si se instala | Notificar |

---

## 4. Logrotate

Evitar que los logs llenen el disco:

```bash
sudo cp etc/logrotate.d/docker-castuo-ctaex /etc/logrotate.d/docker-castuo-ctaex
# Ajustar ruta /var/log/castuo si hace falta
sudo logrotate -f /etc/logrotate.d/docker-castuo-ctaex
```

Configuración: rotación diaria, 14 días, compresión, creación 0640 root root.

---

## 5. Checklist CTAEX (watchdogs y monitoreo)

| Área | Acción | Comando / Verificación | Responsable |
|------|--------|------------------------|-------------|
| Watchdogs | Instalar y habilitar servicios systemd | `systemctl status docker-watchdog-ctaex nginx-watchdog-ctaex postgres-watchdog-ctaex mqtt-watchdog-ctaex disk-watchdog-ctaex` | DevOps |
| Prometheus + Grafana | Arrancar y comprobar scrape | Abrir http://IP:9090 y http://IP:3001; comprobar target `backend` up | DevOps |
| Logrotate | Configurar y probar | `sudo logrotate -f /etc/logrotate.d/docker-castuo-ctaex` | Admin |
| Notificaciones | Configurar Slack (o script alternativo) | `SLACK_WEBHOOK_URL=... ./scripts/notify_slack_ctaex.sh "Test"` | DevOps |
| Health checks | Comprobar estado de contenedores | `docker compose -f docker/docker-compose.ctaex.yml ps` (healthy) | DevOps |
| Backups | Comprobar scripts de backup | Ejecutar manualmente y revisar /backups/ | DBA |
| Firewall | Solo IPs/puertos necesarios | `sudo ufw status numbered` | Admin |
| Nginx | Whitelist y SSL | `nginx -t`, `curl -I https://ctaex...` desde IP no autorizada | Admin |

---

## 6. Comandos para activar todo (servidor CTAEX)

Sustituir `/root/castuo-ctaex` por la ruta real del proyecto (y el usuario si no es root).

```bash
# 1. Directorios y permisos
sudo mkdir -p /var/log/castuo
sudo chown -R "$USER:$USER" /var/log/castuo

# 2. Scripts ejecutables
chmod +x scripts/docker_watchdog_ctaex.sh scripts/nginx_watchdog_ctaex.sh \
  scripts/postgres_watchdog_ctaex.sh scripts/mqtt_watchdog_ctaex.sh \
  scripts/disk_watchdog_ctaex.sh scripts/notify_slack_ctaex.sh

# 3. Servicios systemd (ajustar REPO)
REPO="/root/castuo-ctaex"
for f in scripts/systemd/*.service; do
  name=$(basename "$f")
  sudo sed "s|/root/castuo-ctaex|$REPO|g" "$f" | sudo tee "/etc/systemd/system/$name" > /dev/null
done
sudo systemctl daemon-reload
sudo systemctl enable docker-watchdog-ctaex nginx-watchdog-ctaex postgres-watchdog-ctaex mqtt-watchdog-ctaex disk-watchdog-ctaex
sudo systemctl start docker-watchdog-ctaex nginx-watchdog-ctaex postgres-watchdog-ctaex mqtt-watchdog-ctaex disk-watchdog-ctaex

# 4. Logrotate
sudo cp etc/logrotate.d/docker-castuo-ctaex /etc/logrotate.d/docker-castuo-ctaex
sudo logrotate -f /etc/logrotate.d/docker-castuo-ctaex

# 5. Slack (opcional)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
# Añadir SLACK_WEBHOOK_URL a los .service o a /etc/environment / .env

# 6. Prometheus + Grafana
docker compose -f docker/docker-compose.ctaex.yml up -d prometheus grafana

# 7. Comprobar
curl -s http://localhost:8000/health
docker compose -f docker/docker-compose.ctaex.yml ps
sudo systemctl status docker-watchdog-ctaex
```

---

## Resumen

- **Rearmadores:** Docker, Nginx, PostgreSQL, MQTT y disco; scripts en `scripts/*_watchdog_ctaex.sh` y unidades en `scripts/systemd/`.
- **Health checks:** Backend (`/health`) y postgres en `docker-compose.ctaex.yml`.
- **Monitoreo:** Prometheus (backend `/metrics`) y Grafana en el mismo compose.
- **Logrotate:** `etc/logrotate.d/docker-castuo-ctaex`.
- **Notificaciones:** `scripts/notify_slack_ctaex.sh` con `SLACK_WEBHOOK_URL`.
