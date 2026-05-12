# DNS + SSL — Hetzner CX22 (CASTÚO)

Flujo en **3 pasos** con el stack **Docker** del repo (Nginx en contenedor + Certbot webroot). No hace falta Nginx en el host: el certificado vive en el volumen `castuo_letsencrypt` y Nginx lo monta en `:443`.

---

## PASO 1 — DNS (tu PC / panel del registrador, ~2 min)

Crea **dos registros A** apuntando a la **IP pública del CX22**:

| Tipo | Nombre (host) | Valor |
|------|----------------|-------|
| A | `castuo` (→ `castuo.tudominio.eu`) | IP del CX22 |
| A | `n8n.castuo` o FQDN completo según panel | IP del CX22 |

**TTL:** `300` (5 min) mientras validas; luego puedes subirlo.

**Cloudflare:** proxy **desactivado** (nube **gris**) en esos registros para que Let's Encrypt resuelva hasta tu VPS sin capa proxy.

**Comprobación rápida**

```bash
dig +short castuo.tudominio.eu A
dig +short n8n.castuo.tudominio.eu A
```

Ambos deben devolver la misma IP que ves en Hetzner Cloud.

---

## PASO 2 — SSL (servidor Hetzner, ~1–2 min)

Clona o sincroniza el repo en **`/opt/castuo-system`** (o define `CASTUO_REPO_ROOT`). Asegúrate de tener **`.env.production`** y **`castuo.conf`** con los mismos `server_name` que los DNS.

```bash
ssh root@TU_IP
cd /opt/castuo-system

export CASTUO_DOMAIN=castuo.tudominio.eu
export CERTBOT_EMAIL=tu@email.com
# Opcional si difiere de N8N_HOST en .env.production:
# export CASTUO_N8N_DOMAIN=n8n.castuo.tudominio.eu

chmod +x deploy/setup-ssl.sh
./deploy/setup-ssl.sh
```

El script:

1. Comprueba resolución DNS hacia la IP del servidor (o `EXPECTED_IP` si la fijas).
2. Levanta el stack si hace falta (`docker compose … up -d`).
3. Emite el certificado con **Certbot** (`certonly --webroot`, volumen compartido con Nginx).
4. Genera **`castuo-https.auto.conf`** (TLS 1.2+1.3, HSTS, cabeceras de seguridad, rate limit básico) y lo referencia desde **`castuo.conf`** con `include`.
5. Recarga Nginx en contenedor.
6. Opcional: instala **cron** en el host para `certbot renew` + `nginx -s reload` (renovación automática).

*Rutas del usuario:* el ejemplo `/opt/castuo/app/setup-ssl.sh` equivale a clonar este repo; el script real está en **`deploy/setup-ssl.sh`** dentro del clon.

---

## PASO 3 — Verificar (Windows, PowerShell)

Desde tu PC (en el repo):

```powershell
.\scripts\windows\verify-dns-ssl.ps1 `
  -PrimaryDomain castuo.tudominio.eu `
  -N8nDomain n8n.castuo.tudominio.eu `
  -HetznerIP TU_IP
```

Muestra: resolución DNS, `GET /health` por HTTPS en API y comprobación HTTPS de n8n, datos básicos del certificado (caducidad) y enlace a **SSL Labs**.

---

## Renovación automática

- **Recomendado:** cron en el host instalado por `setup-ssl.sh` (no requiere montar `docker.sock` en el contenedor).
- **Manual:** `docker compose -f docker-compose.prod.yml --env-file .env.production --profile certbot run --rm certbot renew`
- **Opcional:** perfil Compose `renew` — ver comentario en `docker-compose.prod.yml`.

---

## Registradores comunes (pistas rápidas)

| Panel | Dónde crear el A |
|-------|------------------|
| **Cloudflare** | DNS → Records → A (proxy off) |
| **IONOS / 1&1** | Dominios → DNS |
| **GoDaddy** | DNS Management |
| **OVH** | Web Cloud → Dominios → Zone DNS |
| **Namecheap** | Advanced DNS → Host records |

Nombre del host: suele ser `castuo` + dominio raíz, o el FQDN completo según el formulario.

---

*Índice despliegue:* [CHECKLIST-CURSOR-HETZNER-D1.md](./CHECKLIST-CURSOR-HETZNER-D1.md)
