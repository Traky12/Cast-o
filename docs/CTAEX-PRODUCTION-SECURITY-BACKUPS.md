# CTAEX Producción: IP Whitelisting y Backups

Sistema 100% seguro y con backups para CASTUO-SYSTEM en CTAEX: IP whitelisting (Nginx, UFW, Docker, Backend), políticas de backup (PostgreSQL, GaiaChain, archivos) y checklist de activación.

**Rearmadores y monitoreo:** ver [CTAEX-WATCHDOGS-MONITORING.md](CTAEX-WATCHDOGS-MONITORING.md) (watchdogs, Prometheus, Grafana, logrotate, Slack).

---

## 1. IP Whitelisting

### 1.1 Nginx

Permitir solo IPs de CTAEX, oficinas y socios.

**Configuración:** usar el archivo `docker/nginx-ctaex-whitelist.conf`.

```bash
# Copiar a sites-available y enlazar
sudo cp docker/nginx-ctaex-whitelist.conf /etc/nginx/sites-available/castuo-ctaex
sudo ln -sf /etc/nginx/sites-available/castuo-ctaex /etc/nginx/sites-enabled/
# Editar y sustituir las IPs por las autorizadas
sudo nginx -t
sudo systemctl reload nginx
```

En el archivo se definen:
- **`/api/`**, **`/trazabilidad/`**, **`/microgreens/`**, **`/certificacion/`**, **`/ecommerce/`**: `allow` a redes/IPs CTAEX y socios, `deny all`.
- **`/`** (dashboard): solo CTAEX y oficina.
- **`/static/`**: `allow all` para recursos públicos (certificados, etc.).

**Probar:**

```bash
# Desde IP no autorizada → 403 Forbidden
curl -I https://ctaex.castu.system/api/microgreens/sensors

# Desde IP autorizada (ej. 89.167.5.100) → 200
curl -I https://ctaex.castu.system/api/microgreens/sensors
```

### 1.2 UFW (Firewall)

Restringir acceso a puertos sensibles.

```bash
# IPs específicas a puertos críticos
sudo ufw allow from 89.167.5.0/24 to any port 8000   # Backend (solo red CTAEX)
sudo ufw allow from 195.235.100.123 to any port 8000
sudo ufw allow from 89.167.5.0/24 to any port 3000   # Frontend
sudo ufw allow from 195.235.100.123 to any port 3000

# Puertos públicos
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8883/tcp   # MQTT TLS

sudo ufw default deny incoming
sudo ufw enable
sudo ufw status numbered
```

### 1.3 Docker (producción)

Backend y frontend solo en localhost; Nginx en el host hace de proxy.

```bash
# Usar el override de producción (puertos 127.0.0.1 + redes)
docker compose -f docker/docker-compose.ctaex.yml -f docker/docker-compose.ctaex-production.yml up -d
```

En `docker-compose.ctaex-production.yml`:
- `backend`: `127.0.0.1:8000:8000`
- `frontend`: `127.0.0.1:3000:80`
- Redes: `internal_network` (backend, postgres, mqtt), `public_network` (frontend).

### 1.4 Backend (GaiaChain / endpoints sensibles)

Si defines **`ALLOWED_IPS`** en el entorno del backend, las rutas sensibles solo aceptan esas IPs.

**Variable:** lista separada por comas, con IPs o CIDR (ej. `/24`).

```bash
# En .env o entorno del contenedor
ALLOWED_IPS=89.167.5.0/24,195.235.100.123,127.0.0.1,203.0.113.45,203.0.113.46
```

Rutas afectadas: `/trazabilidad/gaia`, `/ecommerce/create-checkout`, `/money/microgreens`. Si la IP no está permitida → **403 IP no autorizada**.

---

## 2. Políticas de Backup

### 2.1 PostgreSQL

**Script:** `scripts/backup_postgres_ctaex.sh`

```bash
chmod +x scripts/backup_postgres_ctaex.sh
BACKUP_DIR=/backups/postgres ./scripts/backup_postgres_ctaex.sh
```

Variables opcionales: `REPO_ROOT`, `COMPOSE_FILE`, `DB_NAME`, `DB_USER`, `BACKUP_DIR`, `RCLONE_REMOTE` (ej. `b2:castuo-ctaex-backups`).

**Cron (diario 2:00):**

```bash
0 2 * * * /ruta/al/repo/scripts/backup_postgres_ctaex.sh >> /var/log/castuo/backup_postgres.log 2>&1
```

Retención local: 30 días. Opcional: subida a Backblaze B2 con `RCLONE_REMOTE=b2:castuo-ctaex-backups`.

### 2.2 GaiaChain

**Script:** `scripts/backup_gaiachain_ctaex.sh`

Si tienes un volumen o directorio con datos del nodo, define `GAIA_CHAIN_DATA` o ajusta el script (contenedor/volumen).

```bash
chmod +x scripts/backup_gaiachain_ctaex.sh
BACKUP_DIR=/backups/gaiachain ./scripts/backup_gaiachain_ctaex.sh
```

**Cron (diario 3:00):**

```bash
0 3 * * * /ruta/al/repo/scripts/backup_gaiachain_ctaex.sh >> /var/log/castuo/backup_gaiachain.log 2>&1
```

### 2.3 Archivos críticos

**Script:** `scripts/backup_files_ctaex.sh`

Respalda `docker/`, `/etc/nginx/sites-available`, etc. Ajustar `CRITICAL_DIRS` en el script si hace falta.

```bash
chmod +x scripts/backup_files_ctaex.sh
BACKUPS_FILES_DIR=/backups/files ./scripts/backup_files_ctaex.sh
```

**Cron (diario 4:00):**

```bash
0 4 * * * /ruta/al/repo/scripts/backup_files_ctaex.sh >> /var/log/castuo/backup_files.log 2>&1
```

Retención local: 7 días para archivos.

### 2.4 Rclone (Backblaze B2)

```bash
sudo apt update && sudo apt install -y rclone
rclone config   # Crear remote "b2" con credenciales Backblaze
export RCLONE_REMOTE=b2:castuo-ctaex-backups
rclone ls "$RCLONE_REMOTE"
```

---

## 3. Checklist final CTAEX

| Área | Acción | Comando / Verificación | Responsable |
|------|--------|------------------------|-------------|
| IP Whitelisting | Nginx, UFW y Docker con IPs autorizadas | `sudo ufw status numbered`, `curl -I https://ctaex.castu.system/api/...` desde IP no autorizada → 403 | Admin Sistemas |
| Backups PostgreSQL | Comprobar script y directorio | Ejecutar `./scripts/backup_postgres_ctaex.sh` y revisar `/backups/postgres/` | DBA |
| Backups GaiaChain | Comprobar script | Ejecutar `./scripts/backup_gaiachain_ctaex.sh` y revisar `/backups/gaiachain/` | Blockchain Admin |
| Backups archivos | Comprobar script | Ejecutar `./scripts/backup_files_ctaex.sh` y revisar `/backups/files/` | DevOps |
| Rclone | Configurar y probar B2 | `rclone ls b2:castuo-ctaex-backups/` | DevOps |
| Cron | Verificar tareas de backup | `crontab -l`, `grep CRON /var/log/syslog` | Admin Sistemas |
| Firewall | Solo puertos necesarios abiertos | `sudo ufw status numbered` | Admin Sistemas |
| Nginx | Comprobar whitelist y SSL | `sudo nginx -t`, `curl -I https://ctaex.castu.system` desde IP no autorizada | Admin Sistemas |
| Backend ALLOWED_IPS | Opcional segunda capa | Definir `ALLOWED_IPS` en env del backend y probar 403 desde IP no permitida | Backend |
| Stripe | Webhooks y pagos en producción | `stripe listen --forward-to ...` en desarrollo; en prod configurar URL y secret | E-commerce |
| MQTT | Broker operativo y seguro | `docker logs <mqtt_container>`, `mosquitto_pub` de prueba | IoT |

---

## 4. Comandos para activar todo (servidor CTAEX)

Ejecutar en el servidor (ej. 89.167.5.233), sustituyendo `/ruta/al/repo` por la ruta real del proyecto.

```bash
# 1. Directorios de backup
sudo mkdir -p /backups/postgres /backups/gaiachain /backups/files
sudo mkdir -p /var/log/castuo
sudo chown -R "$USER:$USER" /backups /var/log/castuo

# 2. Rclone (opcional)
sudo apt update && sudo apt install -y rclone
rclone config   # configurar remote 'b2'

# 3. Scripts de backup ejecutables
chmod +x scripts/backup_postgres_ctaex.sh scripts/backup_gaiachain_ctaex.sh scripts/backup_files_ctaex.sh

# 4. Crontab
crontab -e
# Añadir:
# 0 2 * * * /ruta/al/repo/scripts/backup_postgres_ctaex.sh >> /var/log/castuo/backup_postgres.log 2>&1
# 0 3 * * * /ruta/al/repo/scripts/backup_gaiachain_ctaex.sh >> /var/log/castuo/backup_gaiachain.log 2>&1
# 0 4 * * * /ruta/al/repo/scripts/backup_files_ctaex.sh >> /var/log/castuo/backup_files.log 2>&1

# 5. Nginx con whitelist
sudo cp docker/nginx-ctaex-whitelist.conf /etc/nginx/sites-available/castuo-ctaex
# Editar IPs si es necesario
sudo ln -sf /etc/nginx/sites-available/castuo-ctaex /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 6. UFW
sudo ufw allow from 89.167.5.0/24 to any port 8000
sudo ufw allow from 195.235.100.123 to any port 8000
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8883/tcp
sudo ufw default deny incoming
sudo ufw enable
sudo ufw status numbered

# 7. Docker producción (redes + puertos localhost)
docker compose -f docker/docker-compose.ctaex.yml -f docker/docker-compose.ctaex-production.yml up -d --build

# 8. Backend con whitelist (opcional)
export ALLOWED_IPS=89.167.5.0/24,195.235.100.123,127.0.0.1
# Incluir ALLOWED_IPS en el env del contenedor backend en tu compose o .env

# 9. Pruebas de backup
BACKUP_DIR=/backups/postgres ./scripts/backup_postgres_ctaex.sh
BACKUP_DIR=/backups/gaiachain ./scripts/backup_gaiachain_ctaex.sh
BACKUPS_FILES_DIR=/backups/files ./scripts/backup_files_ctaex.sh

# 10. Logs
tail -f /var/log/castuo/backup_postgres.log
```

---

## Resumen

- **IP Whitelisting:** Nginx (whitelist por location), UFW (puertos por IP), Docker (127.0.0.1 + redes), Backend (`ALLOWED_IPS` en rutas sensibles).
- **Backups:** PostgreSQL diario 2:00 (30 días), GaiaChain 3:00 (30 días), archivos 4:00 (7 días); opcional subida a Backblaze B2 con rclone.
- **Credenciales:** Docker Secrets en producción; Stripe con webhooks verificados.
- **Acceso:** HTTPS (Let's Encrypt), MQTT TLS (8883).
