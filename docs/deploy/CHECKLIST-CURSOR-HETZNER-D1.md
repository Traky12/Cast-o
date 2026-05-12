# CHECKLIST CURSOR → HETZNER (D1)

## 📁 Estructura del Repositorio (Raíz)

```
Castuo-System/
├── .dockerignore
├── .env.production.example
├── Dockerfile
├── README.md
├── castuo.conf
├── castuo-https.auto.conf
├── deploy.sh
├── docker-compose.prod.yml
├── hetzner-init.sh
└── init-db/
    └── 001_init_schema.sql
```

---

## 🔧 CONFIGURACIÓN INICIAL

### 1.1. Preparación del Servidor Hetzner

```bash
# Conectar al servidor (ejemplo para CX22)
ssh root@your-hetzner-server

# Descargar y ejecutar script de inicialización
curl -fsSL https://raw.githubusercontent.com/tu-org/Castuo-System/main/hetzner-init.sh | bash
```

---

## 🐳 CONFIGURACIÓN DOCKER

### 2.1. Configuración del Stack

```bash
# Clonar repositorio
git clone https://github.com/tu-org/Castuo-System.git
cd Castuo-System

# Copiar y configurar entorno
cp .env.production.example .env.production
nano .env.production
```

**Variables clave**

- `CASTUO_DOMAIN=castuo.tudominio.eu`
- `SECRET_KEY=tu-secret-key`
- `N8N_PASSWORD=tu-contraseña-n8n`

---

## 📋 CONFIGURACIÓN DE ARCHIVOS

### 3.1. Configuración de Nginx

Editar `castuo.conf`:

```nginx
# Proxy reverso para API y n8n
upstream castuo_api {
    server api:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name castuo.tudominio.eu;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://castuo_api;
        proxy_set_header Host $host;
    }
}
```

**Nota:** Ver `castuo.conf` completo en el repositorio para configuración adicional (n8n, WebSocket, etc.).

---

## ⚙️ DESPLIEGUE DEL SISTEMA

### 4.1. Comandos de Despliegue

```bash
# Despliegue completo
./deploy.sh --full

# Componentes individuales
./deploy.sh --api      # API
./deploy.sh --n8n      # n8n
./deploy.sh --nginx    # Nginx

# Verificar estado
./deploy.sh --status

# Rollback
./deploy.sh --rollback
```

**Notas**

- Asegurar permisos: `chmod +x deploy.sh`
- Para despliegue remoto: `HETZNER_IP=... ./deploy.sh --remote`
- Rollback requiere imagen `castuo-api:previous`

---

## 🔒 CONFIGURACIÓN DE SEGURIDAD

### 5.1. Certbot (SSL)

```bash
# Certificados iniciales
docker-compose -f docker-compose.prod.yml --profile certbot run --rm certbot certonly --webroot -w /var/www/certbot -d castuo.tudominio.eu -d n8n.castuo.tudominio.eu

# Renovación automática
docker-compose -f docker-compose.prod.yml --profile certbot run --rm certbot renew
```

**Nota:** Para Docker Compose V2 usar `docker compose` (sin guión).

**Automatizado (DNS + TLS endurecido + cron renew):** [DNS-SSL-HETZNER-CX22.md](./DNS-SSL-HETZNER-CX22.md) y `deploy/setup-ssl.sh`.

---

## 📊 VERIFICACIÓN

### 6.1. Verificación de Servicios

```bash
# Estado de contenedores
docker-compose -f docker-compose.prod.yml ps

# Salud de la API
curl http://localhost/health

# Logs
docker-compose -f docker-compose.prod.yml logs -f
```

**PowerShell (desde tu PC):** `.\scripts\windows\verify-dns-ssl.ps1 -PrimaryDomain castuo.tudominio.eu -N8nDomain n8n.castuo.tudominio.eu -HetznerIP TU_IP`

---

## 🎯 GOBERNANZA

### 7.1. Registro en `system_admin_playbook.py`

```python
{
    "titulo": "Checklist Cursor → Hetzner D1 (CX22, TLS, comandos)",
    "ruta": "docs/deploy/CHECKLIST-CURSOR-HETZNER-D1.md"
},
{
    "titulo": "Deploy producción Hetzner CX22 (compose, nginx, n8n, postgres)",
    "ruta": "deploy/README.md"
},
```

---

## 📋 RECURSOS DEL SERVIDOR

| Recurso | CX22 (Recomendado) | CAX41 |
|---------|-------------------|--------|
| CPU | 2 vCPUs | 4 vCPUs |
| RAM | 4 GB | 8 GB |
| Almacenamiento | 40 GB SSD | 80 GB |
| Transferencia | 20 TB | 20 TB |

---

🚜 **Sistema listo para producción** 🌱💪

**Próximos pasos**

- Configurar monitoreo
- Configurar backups automáticos
- Optimizar rendimiento

**Documentación**

- [README.md](../../README.md)
- [Configuración de Vault](../../secrets/README.md)

**Nota:** Validado con `pytest tests/models/test_system_admin_playbook.py -q` → **2 passed**.
