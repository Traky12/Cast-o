# Despliegue EU/OSS – CASTÚO-SYSTEM™

Arquitectura 100% europea y open-source: Keycloak, Vault, Traefik, Wazuh, OpenSearch, backend y sandbox de media.

## Requisitos

- Docker y Docker Compose
- Servidor con GPU (opcional, para media engines)
- Dominios configurados (ej. `api.castuo-system.eu`, `auth.castuo-system.eu`)

## 1. Configuración inicial

- Copiar `.env.example` a `.env` y configurar variables.
- Certificado Traefik (producción): `touch deploy/acme.json && chmod 600 deploy/acme.json`

## 2. Despliegue

### Opción A: Desarrollo (sin Keycloak/Vault)

```bash
AUTH_DISABLED=true docker-compose -f docker-compose.eu-oss.yml up -d backend
```

### Opción B: Producción (Keycloak + Vault)

### 2.1. Keycloak + Vault

```bash
# Desde la raíz del repo
export KEYCLOAK_ADMIN_PASSWORD=tu_password_seguro
docker-compose -f docker-compose.eu-oss.yml up -d keycloak vault
```

- Keycloak: http://localhost:8080 (crear realm `castuo-system`, roles `owner`, `dpo`, `admin`, `auditor`, clientes `dashboard` y `backend`).
- Inicializar Vault: `docker-compose -f docker-compose.eu-oss.yml up -d vault` y luego `./backend/scripts/init_vault.sh` (guardar claves Shamir en lugar seguro en producción).
- Configurar Keycloak: realm `castuo-system`, clientes `backend` y `dashboard`, roles `owner`, `dpo`, `admin`, `auditor`.
- Levantar todo: `docker-compose -f docker-compose.eu-oss.yml up -d`

### 2.2. Traefik (opcional)

```bash
docker-compose -f docker-compose.eu-oss.yml up -d traefik
```

Ajustar `deploy/dynamic.yml` y `deploy/traefik.yml` a tus dominios y certificados.

### 2.3. Backend

```bash
# Sin Vault en desarrollo
export AUTH_DISABLED=true
docker-compose -f docker-compose.eu-oss.yml up -d backend

# Con Vault (producción)
export VAULT_TOKEN=root-token
export AUTH_DISABLED=false
docker-compose -f docker-compose.eu-oss.yml up -d backend
```

## 3. Verificación

- Backend: `curl http://localhost:8000/api/health`
- Keycloak: http://localhost:8080 (o https://auth.castuo-system.eu)
- Traefik: dashboard en https://traefik.castuo-system.eu

## 4. Rotación de claves

```bash
./backend/scripts/rotate_keys.sh
```

## 5. Generación de informes de cumplimiento

Desde el directorio `backend/`:

```bash
PYTHONPATH=. python scripts/generate_compliance_report.py sd-eu-20260315-12345-67890 educational_video
```

Se genera `backend/compliance_report_<media_id>.json` para entregar a Junta/CTAEX.

## Estructura de configuración

- `deploy/traefik.yml` – Entrada TLS, Let's Encrypt, cifrados.
- `deploy/dynamic.yml` – Rutas backend/dashboard, rate-limit, headers EU.
- `backend/config/security.md` – Referencia de componentes y variables.
- `backend/security/master_key.md` – Modelo de claves maestras y derivadas.

## 6. Variables de entorno clave

| Variable | Descripción | Ejemplo (dev) |
|----------|-------------|---------------|
| `VAULT_TOKEN` | Token de acceso a Vault | `dev-token` |
| `KEYCLOAK_ADMIN_PASSWORD` | Contraseña admin Keycloak | `admin` |
| `AUTH_DISABLED` | Desactiva autenticación en desarrollo | `true` |
| `WAZUH_ENABLED` | Habilita envío de logs a Wazuh | `false` |

## Endpoints de media (EU sandbox)

- `POST /api/media/generate-educational-video`: genera vídeo educativo (Stable Diffusion EU). Parámetros: `prompt`, `style`, `resolution`, `duration`. Requiere JWT con rol `owner` y consentimiento para generación de media (GDPR Art. 6.1(a)).
