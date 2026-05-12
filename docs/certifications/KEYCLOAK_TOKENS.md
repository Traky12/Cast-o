# Tokens Keycloak — Staging (uso interno, no versionar valores reales en git)

Uso: definir `STAGING_ADMIN_TOKEN` en entorno o en .env.staging para llamadas a `/api/admin/*`.

## Staging Admin (ejemplo)

```bash
STAGING_ADMIN_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

- **Rol:** admin  
- **Scope:** api:write, vault:seal  
- **Expira:** 30d  

Obtener token desde Keycloak (realm castuo, client consent-api) o usar token de servicio configurado en el backend para staging.

**Seguridad:** No commitear tokens reales. Este archivo puede contener placeholders; los valores reales en .env.staging o gestor de secretos.
