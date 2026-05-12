# Guía de acceso remoto (técnicos)

**Versión:** 1.0  
**Ámbito:** plantilla CASTÚO-SYSTEM (`docker-compose/remote-access.yml`).

## 1. API con JWT

1. Obtén un **access_token** desde Keycloak del realm configurado (por defecto `castuo-system`).
2. Incluye cabecera `Authorization: Bearer <token>`.
3. Las rutas bajo `/api/*` pasan por el **api-gateway** y se reenvían al backend, salvo `/api/lora/*` que requiere `LORA_UPSTREAM`.

Ejemplo de token (password grant; sustituye valores):

```bash
curl -s -X POST "https://auth.ejemplo.local/realms/castuo-system/protocol/openid-connect/token" \
  -d "client_id=api-gateway" \
  -d "client_secret=TU_SECRETO" \
  -d "grant_type=password" \
  -d "username=tecnico1" \
  -d "password=TU_PASSWORD"
```

Consulta de información MQTT publicada por el gateway (no sustituye conexión MQTT):

```bash
curl -sk "https://api.ejemplo.local/api/iot/broker-info" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## 2. Límites

- El gateway **no** convierte HTTP en MQTT.
- Para SSO solo navegador delante de NGINX, hace falta **oauth2-proxy** (u otro) además de esta plantilla.

## 3. Referencias

- `docs/deploy/ARQUITECTURA-ACCESO-REMOTO-CTAEX.md`
- `docker/remote-access/.env.remote-access.example`
