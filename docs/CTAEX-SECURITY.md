# Seguridad CTAEX — Roles, trazabilidad segura y confidencialidad

Guía para desplegar CASTUO-SYSTEM en CTAEX con credenciales por roles, **imposibilidad de extraer datos confidenciales** (incluso por personal CTAEX), auditoría y trazabilidad segura.

**Producción (IP whitelisting + backups):** ver [CTAEX-PRODUCTION-SECURITY-BACKUPS.md](CTAEX-PRODUCTION-SECURITY-BACKUPS.md).

## 0. Principio: ningún dato confidencial fuera del sistema

- **Las respuestas de la API** se sanitizan en middleware: cualquier clave considerada sensible (password, secret, token, api_key, etc.) se reemplaza por `***REDACTED***` antes de enviar la respuesta. Así, ni siquiera un miembro de CTAEX con acceso a la API puede obtener secretos vía respuestas JSON.
- **Los logs** utilizan `redact_secrets()` antes de escribir; las entradas de **auditoría** nunca incluyen cuerpos de petición ni valores sensibles, solo evento, ruta, método, rol, recurso e IP.
- **Secrets** solo se leen desde variables de entorno o archivos (Docker Secrets); no se exponen en documentación pública ni en mensajes de error.

## 1. Endpoints CTAEX protegidos por rol

| Endpoint | Método | Roles permitidos | Descripción |
|----------|--------|------------------|-------------|
| `/trazabilidad/gaia` | POST | **admin**, **blockchain** | Registrar datos en GaiaChain. Requiere Bearer token con valor de GAIA_ADMIN_KEY o GAIA_CHAIN_PRIVATE_KEY. |
| `/ecommerce/create-checkout` | POST | **admin**, **ecommerce** | Crear sesión de pago Stripe. Requiere Bearer token (STRIPE_SECRET_KEY / STRIPE_PUBLISHABLE_KEY según rol). |
| `/microgreens/sensors` | GET | Público | Datos de sensores (solo lectura). Sin autenticación obligatoria. |
| `/certificacion/ctaex` | GET | Público | Certificado y QR. Sin autenticación obligatoria. |
| `/ecommerce/webhook` | POST | Firma Stripe | Solo válido con firma HMAC de Stripe (STRIPE_WEBHOOK_SECRET). No usa Bearer. |

**Uso:** En las peticiones a `/trazabilidad/gaia` y `/ecommerce/create-checkout` enviar cabecera:

```http
Authorization: Bearer <valor_del_secret_del_rol>
```

Ejemplo: si `GAIA_ADMIN_KEY` en el servidor tiene valor `gk_prod_xxx`, la petición debe llevar `Authorization: Bearer gk_prod_xxx`.

## 2. Credenciales por roles (IAM)

El módulo `backend/auth_roles.py` mapea el **valor** de cada secret (no el nombre) al rol. Quien conoce el valor puede actuar con ese rol.

| Rol        | Uso                         | Variables (valor = token)        |
|-----------|-----------------------------|-----------------------------------|
| admin     | Acceso total                | GAIA_ADMIN_KEY, DB_ADMIN_PASSWORD, STRIPE_SECRET_KEY |
| tecnico   | Sensores IoT, ambiente, agua| MQTT_TECHNICIAN_PASSWORD, IOT_API_KEY |
| agricultor| Solo lectura cultivos       | FARMER_API_KEY                    |
| auditor   | Certificados y logs         | AUDITOR_API_KEY                   |
| ecommerce | Productos, pedidos, Stripe  | STRIPE_PUBLISHABLE_KEY            |
| blockchain| Trazabilidad GaiaChain      | GAIA_CHAIN_PRIVATE_KEY            |

Rutas permitidas por rol: `ROLE_PERMISSIONS` en `backend/auth_roles.py`. Para proteger otros endpoints: `Depends(require_role("admin", "tecnico"))`.

## 3. Seguridad interna (backend/security_internal.py)

- **Redacción de secretos:** `redact_secrets(obj)` recorre diccionarios/listas y sustituye el valor de cualquier clave sensible por `***REDACTED***` (claves que contienen password, secret, token, key, credential, etc.).
- **Sanitización de respuestas:** El middleware aplica `sanitize_response_body()` a todas las respuestas JSON. Así, si algún endpoint devolviera por error un campo `api_key` o `password`, el cliente nunca lo vería.
- **Auditoría:** En cada llamada a `/trazabilidad/gaia` y `/ecommerce/create-checkout` se registra: timestamp, evento, path, método, rol, resource_id, IP. Sin cuerpos de petición ni secretos. Si se define `AUDIT_LOG_PATH`, las entradas se escriben en ese archivo (una línea JSON por evento).
- **Rate limit:** Para `POST /trazabilidad/gaia` y `POST /ecommerce/create-checkout` se aplica un límite de 60 peticiones por IP y ruta por minuto. Si se supera, se responde 429 (Demasiadas peticiones).

Estas medidas refuerzan la **trazabilidad segura**: solo roles autorizados escriben en GaiaChain o crean pagos, y nadie puede usar la API para extraer secretos ni datos confidenciales.

## 4. Lectura de secrets (Docker Secrets)

El backend puede leer secrets desde **variables de entorno** o desde **archivos** (p. ej. Docker Secrets):

- `STRIPE_SECRET` o `STRIPE_SECRET_FILE` (ruta al archivo)
- `STRIPE_WEBHOOK_SECRET` o `STRIPE_WEBHOOK_SECRET_FILE`
- Cualquier otra clave usando la función `read_secret("NOMBRE")` en `backend/auth_roles.py`.

Ejemplo con archivos en `docker/secrets/`:

```bash
echo -n "sk_live_..." > docker/secrets/stripe_secret
echo -n "whsec_..."  > docker/secrets/stripe_webhook_secret
chmod 600 docker/secrets/*
```

En `docker-compose` montar los secrets y pasar las rutas:

```yaml
services:
  backend:
    environment:
      - STRIPE_SECRET_FILE=/run/secrets/stripe_secret
      - STRIPE_WEBHOOK_SECRET_FILE=/run/secrets/stripe_webhook_secret
    secrets:
      - stripe_secret
      - stripe_webhook_secret
secrets:
  stripe_secret:
    file: ./docker/secrets/stripe_secret
  stripe_webhook_secret:
    file: ./docker/secrets/stripe_webhook_secret
```

## 5. Stripe en producción

- **Clave secreta:** `STRIPE_SECRET` o `STRIPE_SECRET_KEY` (nunca en frontend).
- **Webhook:** `POST /ecommerce/webhook`. Configurar en [Stripe Dashboard](https://dashboard.stripe.com/webhooks):
  - URL: `https://ctaex.castu.system/ecommerce/webhook` (o tu dominio).
  - Eventos: `checkout.session.completed`, opcionalmente `payment_intent.succeeded`.
- **Secreto del webhook:** `STRIPE_WEBHOOK_SECRET` (whsec_...) en backend para validar la firma.

Probar localmente con Stripe CLI:

```bash
stripe listen --forward-to localhost:8000/ecommerce/webhook
```

## 6. Puertos y firewall (UFW)

En el servidor CTAEX (ej. 89.167.5.233):

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (Nginx)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw default deny incoming
sudo ufw enable
```

Backend y frontend pueden escuchar solo en `127.0.0.1` y exponerse mediante Nginx (proxy inverso).

## 7. Nginx como proxy inverso

Ejemplo de sitio en `docker/nginx-ctaex.conf`. Pasos típicos:

```bash
sudo cp docker/nginx-ctaex.conf /etc/nginx/sites-available/castuo-ctaex
sudo ln -s /etc/nginx/sites-available/castuo-ctaex /etc/nginx/sites-enabled/
# Ajustar server_name y rutas de certificados SSL
sudo nginx -t
sudo systemctl reload nginx
```

Certificados SSL con Let's Encrypt:

```bash
sudo certbot --nginx -d ctaex.castu.system
```

## 8. Puntos críticos reforzados (trazabilidad segura)

| Punto crítico | Medida |
|---------------|--------|
| Escritura en GaiaChain | Solo roles **admin** o **blockchain**; auditoría en cada escritura. |
| Creación de pagos Stripe | Solo roles **admin** o **ecommerce**; auditoría; rate limit. |
| Webhook Stripe | Validación de firma con `STRIPE_WEBHOOK_SECRET`; no se confía en cabeceras sin firma. |
| Fuga de secretos en respuestas | Middleware sanitiza todo JSON; claves sensibles reemplazadas por `***REDACTED***`. |
| Fuga de secretos en logs | Uso de `redact_secrets()` antes de cualquier log que incluya datos de usuario o config. |
| Abuso por fuerza bruta | Rate limit 60 req/min por IP en rutas sensibles; 429 si se supera. |
| Acceso sin autorización | 401 si falta token en rutas protegidas; 403 si el rol no tiene permiso para la ruta. |

## 9. Checklist de seguridad

| Área        | Acción                                      | Verificación                    |
|------------|---------------------------------------------|---------------------------------|
| Firewall   | UFW: 22, 80, 443                            | `sudo ufw status verbose`       |
| Stripe     | Webhook configurado y secreto en backend    | Dashboard Stripe + logs backend |
| Secrets    | Claves en .env o Docker Secrets, no en código| Revisar .gitignore               |
| PostgreSQL | Acceso solo desde backend (red interna)     | No exponer 5432 al público       |
| MQTT       | Autenticación y, si es posible, TLS (8883)  | `mosquitto.conf` + passwords    |
| SSL        | HTTPS obligatorio en producción             | `certbot certificates`           |
| Backups    | Copias automáticas de BD y secrets          | crontab / scripts de backup     |

## 10. Referencias

- `backend/auth_roles.py`: roles, `read_secret`, `require_role`.
- `backend/security_internal.py`: `redact_secrets`, `sanitize_response_body`, `audit_log`, `check_rate_limit`, `get_client_ip`.
- `backend/routers/ctaex.py`: endpoints CTAEX con `require_role` y `audit_log` en trazabilidad y checkout.
- `backend/main.py`: middleware de rate limit y sanitización de respuestas JSON.
- `docker/nginx-ctaex.conf`: ejemplo Nginx.
- `docs/OPERATIONS-MANUAL-CTAEX.md`: operaciones y Docker.

**Variable de entorno opcional:** `AUDIT_LOG_PATH` — si está definida, los eventos de auditoría se escriben en ese archivo (una línea JSON por evento).
