# CASTUO-SYSTEM — Guía de despliegue (Hetzner CAX21)

CAX21 #118296333 | CTAEX 17/03 | Dronica + LoRaWAN | JEREMIE 605K€

---

## 1. Pre-requisitos (Hetzner Console)

- [x] **CAX21 #118296333** → Power ON
- [x] **Firewall** → TCP 80, 8000, 1883, 9001 (o solo 80 si todo va por Nginx proxy)
- [x] **IP**: 89.167.5.233 → SSH acceso
- [x] **docker-compose**: api:8000, mqtt:1883, n8n:5678 (n8n usa 5678, no 9001)

---

## 2. SSH + Git pull (Hetzner Console)

Hetzner Console → CAX21 → Console (terminal web):

```bash
# 1. Ir al proyecto (ajusta la ruta si usas otra)
cd /castuo-ctaex
# o: cd /frontend  según cómo hayas desplegado

git pull origin main

# 2. Verificar estructura
ls backend/dronica/           # __init__.py missions.py connection.py lora.py
ls frontend/public/           # dronica.html CASTUO-Dronica-v4.6.1.html
ls n8n/workflows/             # dronica_missions.json sabionda.json ...
```

---

## 3. Configurar .env (n8n, Notion, Dronica)

```bash
nano .env
```

Añade o verifica:

```env
# Dronica / LoRaWAN
DRONICA_MQTT_BROKER=mqtt://mqtt:1883
DRONICA_MQTT_TOPIC=dronica/missions

# n8n + Notion (sustituir por valores reales)
NOTION_API_KEY=secret_xxxxxxxx
NOTION_DATABASE_ID=tu_database_id_aqui
```

En los workflows de n8n (sabionda, dronica_missions) sustituye `YOUR_NOTION_DATABASE_ID` por el ID real de tu base de datos de Notion.

---

## 4. Verificar Nginx: /api → FastAPI 8000

La configuración está en **nginx/conf.d/default.conf** (no en frontend/):

```bash
cd /castuo-ctaex
grep -A10 "location /api/" nginx/conf.d/default.conf
```

Debe contener:

```nginx
location /api/ {
    proxy_pass http://api:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Así, `http://89.167.5.233/api/dronica/connection` → Nginx reenvía a `http://api:8000/dronica/connection`.

---

## 5. Build + Restart (docker-compose)

```bash
cd /castuo-ctaex

# Parar
docker-compose down

# Rebuild (api, frontend, n8n, mqtt)
docker-compose build api frontend n8n mqtt

# Arrancar en background
docker-compose up -d

# Verificar logs
docker-compose logs -f api
docker-compose logs -f n8n
```

En producción con **docker-compose.prod.yml** (solo nginx + api):

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 6. Test endpoints (desde el servidor)

```bash
# Conexión Dronica
curl http://localhost:8000/dronica/connection
# → {"status":"online","drones":["drone_001","drone_002"],"gateway":"CASTUO-Gate-001",...}

# Crear misión
curl -X POST http://localhost:8000/dronica/missions \
  -H "Content-Type: application/json" \
  -d '{"mission_id":"test_001","drone_id":"drone_001","waypoints":[{"lat":39.1,"lng":-6.0}]}'
```

Si usas Nginx en el mismo host:

```bash
curl http://localhost/api/dronica/connection
```

---

## 7. Deploy completo en 3 comandos

Hetzner Console → CAX21 → Terminal:

```bash
cd /castuo-ctaex

# 1. Código + opcional: usar v4.6.1 como dronica.html
git pull origin main
cp frontend/public/CASTUO-Dronica-v4.6.1.html frontend/public/dronica.html

# 2. Rebuild y arrancar
docker-compose down
docker-compose up -d --build

# 3. Ver logs
docker-compose logs -f api n8n frontend
```

**Comando 1-línea:**

```bash
cd /castuo-ctaex && git pull && cp frontend/public/CASTUO-Dronica-v4.6.1.html frontend/public/dronica.html && docker-compose down && docker-compose up -d --build && docker-compose logs -f api
```

---

## 8. Test desde fuera (Chrome / Torrijos)

| URL | Comprobación |
|-----|----------------|
| http://89.167.5.233/ | Menú con enlace "Dronica" |
| http://89.167.5.233/dronica.html | Dashboard v4.6.1, Status LIVE (refresh 5s) |
| http://89.167.5.233/api/dronica/connection | JSON: drones + gateway |
| POST http://89.167.5.233/api/dronica/missions | Misión lanzada 200 OK |

**Pruebas post-deploy:**

1. Abrir http://89.167.5.233/dronica.html → carga v4.6.1.
2. Status LIVE (cada 5s) → drone_001, drone_002, CASTUO-Gate-001.
3. Nueva misión: mission_badajoz, drone_001, waypoints Badajoz → Lanzar.
4. F12 → Network → `/api/dronica/missions` → 200 OK.
5. n8n logs → Notion page + MQTT `dronica/missions`.

---

## 9. Monitoreo Hetzner

Hetzner Console → CAX21 → Metrics:

- **CPU**: 4 ARM cores → &lt;10%
- **RAM**: 8GB → &lt;3GB uso
- **Puertos**: 80 (Nginx proxy); 8000 solo interno si usas proxy.
- **Traffic**: Dronica missions dentro del plan.

---

## 10. CTAEX 17/03 — Script demo (2 min)

1. Hetzner CAX21 metrics (console.hetzner.com).
2. http://89.167.5.233/dronica.html → Status LIVE.
3. Misión Badajoz: waypoints lat/lng → Lanzar.
4. n8n → Notion + MQTT `dronica/missions`.
5. Cierre: *"Dronica + LoRaWAN → JEREMIE 605K€ Compliant"*.

---

## 11. Troubleshooting

| Problema | Acción |
|----------|--------|
| 404 en /api/* | Revisar Nginx: `docker logs <frontend\|nginx>` y `nginx/conf.d/default.conf`. |
| API no responde | `docker-compose logs api \| grep dronica` |
| n8n / Notion | `docker-compose logs n8n \| grep -i notion`; revisar NOTION_DATABASE_ID en workflow. |
| Puerto 8000 | En producción no hace falta exponerlo; Nginx proxy (/api) es suficiente. |

---

## 12. HTTPS con Certbot (CAX21 Nginx)

**Requisito:** Un dominio (ej. castuo-system.com) apuntando a 89.167.5.233. Let's Encrypt no emite certificados solo para IP.

### 12.1 Estructura

- **nginx/conf.d/default.conf** está en modo **solo HTTP** (puerto 80). Nginx arranca siempre aunque no tengas certificados. Incluye `/.well-known/acme-challenge/` para Certbot.
- **nginx/conf.d/default-https.conf.example**: config completa con HTTP→HTTPS redirect y server 443. Se usa cuando ya tienes certificados.
- **scripts/obtener-certificado.sh**: script para generar el certificado la primera vez.

### 12.2 Primera vez: generar certificado

Con la config actual (solo HTTP), nginx ya está levantado. Genera el certificado:

**Opción A — Script (recomendado):**

```bash
cd /castuo-ctaex
bash scripts/obtener-certificado.sh castuo-system.com
# Sustituye castuo-system.com por tu dominio. Email: CERTBOT_EMAIL=tu@email.com si quieres otro.
```

**Opción B — Manual:**

```bash
cd /castuo-ctaex
mkdir -p certbot/conf certbot/www
docker-compose up -d frontend

docker-compose run --rm --entrypoint certbot certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email gregorio@castuo360.com \
  --agree-tos --no-eff-email \
  -d castuo-system.com
```

### 12.3 Activar HTTPS (tras tener certificados)

Sustituye la config de nginx por la que incluye 443 y redirect:

```bash
cp nginx/conf.d/default-https.conf.example nginx/conf.d/default.conf
docker-compose restart frontend
curl -I https://castuo-system.com
```

### 12.4 Comando 1-click (generar cert + activar HTTPS)

```bash
cd /castuo-ctaex && \
bash scripts/obtener-certificado.sh castuo-system.com && \
cp nginx/conf.d/default-https.conf.example nginx/conf.d/default.conf && \
docker-compose restart frontend && \
curl -I https://89.167.5.233
```

### 12.5 Auto-renovación (cron opcional)

El servicio `certbot` ya hace `certbot renew` cada 12h. Si prefieres cron:

```bash
crontab -e
# Añadir:
0 */12 * * * cd /castuo-ctaex && docker-compose exec certbot certbot renew --quiet && docker-compose restart frontend
```

### 12.6 Comprobar HTTPS (Chrome)

| URL | Comprobación |
|-----|----------------|
| http://89.167.5.233 | Redirect 301 a https |
| https://89.167.5.233 | Candado verde |
| https://89.167.5.233/dronica.html | v4.6.1, Status LIVE |
| https://89.167.5.233/api/dronica/connection | JSON 200 |

**CTAEX 17/03 — HTTPS LIVE:** *"HTTPS Certbot + Dronica → JEREMIE GDPR ✓"*

### 12.7 Checklist post-HTTPS

| Item | Estado |
|------|--------|
| Certbot service | `up -d` ✓ |
| nginx/conf.d/default.conf | return 301 + server 443 activo |
| docker-compose ports | 443:443 expuesto |
| Hetzner Firewall | TCP 443 abierto |
| https://89.167.5.233/dronica.html | Status LIVE |
| Auto-renew | 12h certbot loop |

**Comando 1-click HTTPS activo (tras tener certificados):**

```bash
cd /castuo-ctaex && docker-compose restart frontend && curl -I https://localhost
```

---

## 13. CASTUO-SYSTEM v5.0 — Landing y API unificada

### 13.1 Contenido

- **frontend/public/index.html** = **CASTUO-SYSTEM-v5.0.html**: landing v5.0 (Dashboard CAX21, HTTPS, Dronica, Hidroponía, Agrovoltaica, Auth, enlaces a dronica.html, sabionda-ia.html, qr-trazabilidad).
- **Backend** endpoints adicionales (stubs): `/auth/register`, `/auth/login`, `/auth/recover`, `/hidroponia/sensors`, `/agrovoltaica/yield`, `/trazabilidad/qr`, `/notifications/email`, `/usuarios/stats`.

### 13.2 Deploy completo v5.0 (HTTP → HTTPS)

Un solo comando: pull, build, certificado Certbot, activar HTTPS y comprobar:

```bash
cd /castuo-ctaex && git pull && docker-compose up -d --build && \
bash scripts/obtener-certificado.sh castuo-system.com && \
cp nginx/conf.d/default-https.conf.example nginx/conf.d/default.conf && \
docker-compose restart frontend && curl -I https://89.167.5.233
```

O usando el script (mismo flujo):

```bash
cd /castuo-ctaex
bash scripts/deploy-v5-https.sh
# Opcional: DOMAIN=midominio.com bash scripts/deploy-v5-https.sh
```

### 13.2.1 Deploy con monitorización (stack + Prometheus + Grafana)

```bash
cd /castuo-ctaex && \
git pull && \
docker-compose up -d --build && \
docker-compose -f docker-compose.monitor.yml up -d && \
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001
```

Grafana: http://localhost:3001 (o https://89.167.5.233:3001). Ver **[MONITORING.md](MONITORING.md)** y **[ESCALADO.md](ESCALADO.md)**.

### 13.3 CTAEX 17/03 — Demo 3 minutos

1. https://castuo-system.com/ → Candado + Dashboard v5.0  
2. CAX21 LIVE metrics + HTTPS status  
3. Dronica → 2 drones + misión Badajoz  
4. Hidroponía → Cama 1-12 sensors  
5. Agrovoltaica → Yield optimization  
6. Login → gregorio@castuo360.com  
7. Cierre: *"CASTUO-SYSTEM v5.0 → JEREMIE 605K€ TOTAL INTEGRADO"*

### 13.4 Checklist final v5.0

| Módulo | Estado |
|--------|--------|
| 🌱 Landing v5.0 | HTTPS + todas las funciones |
| 🚁 Dronica | 2 drones + LoRaWAN |
| 💧 Hidroponía | EC/pH + IoT control (API stub) |
| ☀️ Agrovoltaica | Paneles + Yield (API stub) |
| 🤖 IA Sabionda | Mistral + LondBot |
| 📦 Trazabilidad | QR + Blockchain (API stub) |
| 🔐 Auth | Login / Register / Recover (API stub) |
| 📧 Email | notifications/email (API stub) |
| 🔒 HTTPS | Certbot auto-renew |

---

## Resumen

- **Nginx**: `nginx/conf.d/default.conf` → `location /api/` con `proxy_pass http://api:8000/`.
- **HTTPS**: `default.conf` es solo HTTP para que nginx arranque sin certs. Certificado con `scripts/obtener-certificado.sh` o certbot; luego `cp default-https.conf.example default.conf` y `restart frontend`.
- **v5.0**: Landing unificada (index = CASTUO-SYSTEM-v5.0), API stubs auth/hidroponia/agrovoltaica/trazabilidad/usuarios.
- **API_BASE** en el frontend: en local `http://localhost:8000`, en producción `/api` (v4.6.1 ya lo usa).
- **Deploy rápido**: `git pull && docker-compose up -d` (o con `cp` de v4.6.1 a dronica.html y `--build`).
