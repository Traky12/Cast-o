# Guía de Despliegue en Hetzner (Avanzado) — Sabionda Feedback Loop

Proceso detallado y automatizado para desplegar el `Castúo-System` en **Hetzner Cloud** con medidas de seguridad (GDPR, DSA, AI Act), incluyendo:

- `Feedback Loop` de Sabionda (telemetría + alertas)
- `Auditoría federada` (GaiaChain + consistencia)
- `Autenticación PQC (ML-DSA)` mediante firma por mensaje (headers)
- `Validación continua` (harden de workflows)

> Nota de interoperabilidad: en este repo, los endpoints de **cifrado/firma/auditoría** viven en el servicio `backend` (FastAPI) y se acceden desde n8n vía endpoints parametrizables por entorno (`CASTUO_*_URL`).

---

## 1) Requisitos Previos (Entorno)

### 1.1 Cuenta Hetzner Cloud

- Acceso a `console.hetzner.cloud` con tarjeta válida.
- Ubicación recomendada: **Frankfurt (DE)**.

### 1.2 Dominio

- Dominio registrado (ej: `castuo-system.eu`).
- DNS configurado hacia la IP del servidor.

### 1.3 Claves SSH

- Par de claves SSH (4096 bits): `id_rsa.pub`.

### 1.4 Variables de Entorno (mínimas)

Configura en `.env` o en el secrets manager (según el modo de despliegue).

#### Para n8n (firmas + salida cifrada)

- `N8N_ADMIN_JWT`: Bearer token (rol `admin`) usado por n8n para invocar endpoints locales de firma/auditoría.
- `ZERO_LEAK_OUT_URL`: destino externo para el ciphertext (debe aceptar `ciphertext_json` y `signature`).
- `CASTUO_ENCRYPT_URL`: endpoint de cifrado (default recomendado: `http://api:8000/encrypt`).
- `CASTUO_PQC_SIGN_URL`: endpoint de firma PQC (default: `http://api:8000/api/admin/pqc/sign`).
- `CASTUO_AUDIT_REGISTER_URL`: endpoint para registrar eventos de auditoría (default: `http://api:8000/api/audit/register-event`).
- `CASTUO_COMPLIANCE_LATEST_URL`: endpoint de consistencia (default: `http://api:8000/api/compliance/audit/latest?tokenId=0`).
- `CASTUO_MQTT_BROKER`: broker MQTT para telemetría/alertas (ej: `mqtt://mosquitto:1883`).

#### Para Backend (GaiaChain audit)

- `GAIA_CHAIN_AUDIT_CONTRACT`: address del contrato de auditoría en GaiaChain.
- `GAIA_CHAIN_AUDIT_ABI`: ABI del contrato (JSON).
- `GAIA_CHAIN_PRIVATE_KEY`: clave privada para registrar transacciones (opcional para pruebas; idealmente en Vault/HSM).

### 1.5 Dependencias del host (Ubuntu 22.04 típico)

- Docker `20.10+`
- Docker Compose
- (si corres utilidades del host) `curl`, `ufw`

---

## 1b) Esquema Parametrizado (sin URLs hardcodeadas)

El workflow `zero_leak_encrypt_forward_v2.json` está diseñado para evitar endpoints hardcodeados. Usa:

- `CASTUO_ENCRYPT_URL` (node `Crypto_PQC_Encrypt_Lacre_CifradoReal`)
- `CASTUO_PQC_SIGN_URL` (node `Crypto_PQC_Sign_Ciphertext`)
- `CASTUO_AUDIT_REGISTER_URL` (node `ZeroLeak_Register_Audit_Event`)
- `CASTUO_COMPLIANCE_LATEST_URL` (node `ZeroLeak_Compliance_Audit_Latest`)
- `ZERO_LEAK_OUT_URL` (node `ZeroLeak_External_Send_CiphertextOnly`)
- `CASTUO_MQTT_BROKER` (nodes MQTT de salida)

## 2) Arquitectura de Despliegue (con Feedback Loop)

```mermaid
graph TD
  subgraph Hetzner Cloud [Hetzner Cloud]
    N8N[n8n] -->|1) Telemetría local| ZLW[Zero-Leak v2]
    ZLW -->|2) Cifrado| ENC[Backend: POST /encrypt]
    ZLW -->|3) Firma ML-DSA (PQC)| SIGN[Backend: POST /api/admin/pqc/sign]
    ZLW -->|4) Destino cifrado| OUT[ZERO_LEAK_OUT_URL]
    SIGN -->|5) Registro auditoría| AUD[Backend: POST /api/audit/register-event]
    AUD -->|6) Consistencia| CONS[Backend: GET /api/compliance/audit/latest]
    ZLW -->|7) Métricas anonimas| MQTT1[sabionda/telemetry_anon]
    CONS -->|8) Discrepancia?| ALERT[MQTT: tierra-firme/alert]
  end
```

---

## 3) Despliegue Paso a Paso

### 3.1 Paso 1 — Preparar servidor

- Ubicación: Frankfurt (DE)
- Tipo: CX31 (ejemplo)
- Volúmenes: añade uno adicional cifrado para datos sensibles
- Red privada: `castuo-internal` (ejemplo `10.0.0.0/24`)

Comando CLI (opcional):

```bash
hcloud server create \
  --name castuo-production-01 \
  --server-type cx31 \
  --image ubuntu-22.04 \
  --ssh-key ~/id_rsa.pub \
  --location fsn1 \
  --firewall castuo-firewall \
  --backups \
  --network castuo-internal
```

---

### 3.2 Paso 2 — Firewall (GDPR Art. 32)

Puertos recomendados:

- `22/tcp`: SSH (solo IPs permitidas; 2FA donde aplique)
- `80/tcp`: HTTP (redirigir a HTTPS)
- `443/tcp`: HTTPS (TLS 1.3)
- `1883/tcp`: MQTT (telemetría/alertas)
- `5678/tcp`: UI n8n (con auth)
- `8080/tcp`: Keycloak (si instalas local)

Ejemplo con UFW:

```bash
apt update && apt install -y ufw
ufw allow 22/tcp comment 'SSH (solo desde IPs conocidas)'
ufw allow 80/tcp comment 'HTTP (redirige a HTTPS)'
ufw allow 443/tcp comment 'HTTPS (TLS 1.3)'
ufw allow 1883/tcp comment 'MQTT (telemetría)'
ufw allow 5678/tcp comment 'n8n UI'
ufw allow 8080/tcp comment 'Keycloak'
ufw --force enable
```

---

### 3.3 Paso 3 — Backend (FastAPI + GaiaChain Audit)

Este repo ya contiene el backend FastAPI. Asegura que el contenedor del backend reciba:

- `GAIA_CHAIN_AUDIT_CONTRACT`
- `GAIA_CHAIN_AUDIT_ABI`
- `GAIA_CHAIN_PRIVATE_KEY` (si necesitas registrar en cadena)

Endpoints críticos (prefijos reales del backend):

- `POST /api/admin/pqc/sign`
- `POST /api/audit/register-event`
- `GET  /api/compliance/audit/latest?tokenId=0`
- `POST /encrypt`

---

### 3.4 Paso 4 — Keycloak (roles admin/dpo/owner)

Si usas el esquema OAuth2 de Keycloak:

- Realm: `castuo-system`
- Roles: `admin`, `dpo`, `owner`
- Client: `n8n-admin` con `client_credentials`

Genera `N8N_ADMIN_JWT` y guárdalo como variable de entorno.

---

### 3.5 Paso 5 — n8n con Workflow Zero-Leak v2 (100% funcional)

#### 5.1 Instala/levanta n8n

Ejemplo (contenedor):

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=[PLACEHOLDER] \
  -e N8N_HOST=0.0.0.0 \
  --network castuo-internal \
  n8nio/n8n
```

#### 5.2 Importa workflow

- `n8n` -> `Workflows` -> `Import`
- `n8n/workflows/zero_leak_encrypt_forward_v2.json`

#### 5.3 Configura variables en n8n

Además de `N8N_ADMIN_JWT` y `ZERO_LEAK_OUT_URL`, configura los endpoints con:

- `CASTUO_ENCRYPT_URL`
- `CASTUO_PQC_SIGN_URL`
- `CASTUO_AUDIT_REGISTER_URL`
- `CASTUO_COMPLIANCE_LATEST_URL`
- `CASTUO_MQTT_BROKER`

Ejemplo para entornos Docker donde el backend se llama `backend`:

```bash
CASTUO_ENCRYPT_URL=http://backend:8000/encrypt
CASTUO_PQC_SIGN_URL=http://backend:8000/api/admin/pqc/sign
CASTUO_AUDIT_REGISTER_URL=http://backend:8000/api/audit/register-event
CASTUO_COMPLIANCE_LATEST_URL=http://backend:8000/api/compliance/audit/latest?tokenId=0
```

---

### 3.6 Paso 6 — MQTT (telemetría + alertas)

Instala Mosquitto:

```bash
apt install -y mosquitto mosquitto-clients
```

Configura `/etc/mosquitto/mosquitto.conf` (ejemplo):

```ini
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
```

Crear usuario:

```bash
mosquitto_passwd -c /etc/mosquitto/passwd n8n-user
systemctl restart mosquitto
```

Topics esperados:

- `sabionda/telemetry_anon`
- `tierra-firme/alert`

---

## 4) Validación Paso a Paso (Ciclo Completo)

### 4.1 Prueba de Feedback Loop (telemetría)

En un terminal:

```bash
mosquitto_sub -h localhost -t "sabionda/telemetry_anon" -u n8n-user -P [contraseña_mqtt] -v
```

Ejecuta el workflow `zero_leak_encrypt_forward_v2` con una carga de prueba (desde n8n).

### 4.2 Validación de firma + auditoría + consistencia

Verifica que el workflow:

- firma PQC del ciphertext
- registra evento en auditoría federada
- llama a `/api/compliance/audit/latest`

### 4.3 Prueba de discrepancia (cierre en cuarentena lógica)

En entorno de prueba, fuerza inconsistencia para que el workflow active `tierra-firme/alert`.

---

## 5) Hardening y Validación Continua

Ejecuta el hardener:

```bash
python scripts/harden_n8n_flow.py --input n8n/workflows/zero_leak_encrypt_forward_v2.json
```

Programa validación continua (cada 5 minutos):

```cron
*/5 * * * * /usr/bin/python3 /opt/castuo-system/scripts/harden_n8n_flow.py >> /var/log/n8n_hardening.log 2>&1
```

---

## 6) Checklist de Lanzamiento

- Firewall activo con puertos mínimos
- Keycloak con roles y `N8N_ADMIN_JWT`
- backend con `GAIA_CHAIN_AUDIT_*`
- n8n importado y `ZERO_LEAK_OUT_URL` configurado
- MQTT autenticado: `CASTUO_MQTT_PASS` definido (compose genera `passwords.txt` vía `mosquitto-setup`)
- MQTT publicando en `sabionda/telemetry_anon`
- el workflow pasa el hardener TRL9

---

## 7) Próximos pasos (30 días)

- Monitorizar 72h y ajustar umbrales de alertas
- Optimizar latencia de `zero_leak_encrypt_forward_v2`
- Registrar casos de uso reales y hardening incremental

---

### Comprobación automatizada (recomendada)

Antes de activar producción, ejecuta:

```bash
python scripts/harden_n8n_flow.py --input n8n/workflows/zero_leak_encrypt_forward_v2.json --fail-on-violation
```

---

## Anexo

- [Anexo TRL9 — Parametrización sin Hardcode (Zero-Leak v2)](Hetzner-Avanzado-Parametrizacion-TRL9-ZeroLeakV2.md)

---

## Stack Copy/Paste

- Archivo: `docker-compose.hetzner.zero-leak.yml`

---

## Paso 0 y 1-click (recomendado)

```bash
chmod +x generate_credentials.sh generate_n8n_admin_jwt.sh deploy_zero_leak_hetzner_1click.sh
./deploy_zero_leak_hetzner_1click.sh
```

El script:
- genera `.env` (incluye `CASTUO_MQTT_PASS` para MQTT autenticado)
- levanta Keycloak/Postgres/backend
- genera automáticamente `N8N_ADMIN_JWT` via `generate_n8n_admin_jwt.sh`
- levanta n8n y valida TRL9 con `harden_n8n_flow.py`.

