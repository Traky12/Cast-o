# Staging — Dashboards y endpoints de prueba

**CASTÚO-SYSTEM v1.7.5 - Consent API**  
**TRL8 Staging - GDPR/AI Act Ready**

---

## 🔹 Prioridad dashboards

1. **http://localhost:8000/docs** ← API INTERACTIVA (PRIORIDAD) — probar endpoints con Swagger
2. **http://localhost:8200/ui** ← VAULT KEYS (PQC)
3. **http://localhost:8080** ← ZAP SCANNER (0 crit)

```cmd
start http://localhost:8000/docs
```

## 📋 ENDPOINTS DISPONIBLES

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/health | staging_ok / environment / rotation_status |
| GET | /api/admin/rotation-status | Vault keys status (DPO/admin) |
| POST | /api/admin/rotate-key/{key_name} | Rotate Kyber-768 (admin) |
| POST | /api/admin/emergency/seal | Emergency Vault seal (admin) |
| POST | /api/admin/emergency/unseal | Shamir 3/5 recovery (admin) |
| GET | /api/consents | GDPR consents |
| POST | /api/consents | New consent GDPR Art.6 |

---

## URLs resto de servicios (abrir en navegador)

| Servicio      | URL | Descripción |
|---------------|-----|-------------|
| **Backend API** | http://localhost:8000/docs | FastAPI Swagger — Consent API v1.7.5 |
| **Vault**     | http://localhost:8200/ui | HashiCorp Vault — keys Kyber-768 / Shamir |
| **OWASP ZAP** | http://localhost:8080 | Security scanner — baseline reports |
| **Frontend**  | http://localhost:3000 | Dashboard Next.js (si existe) |

## Abrir todos (Windows CMD)

```cmd
start http://localhost:8000/docs
start http://localhost:8200/ui
start http://localhost:8080
start http://localhost:3000
```

## Prueba admin (JWT Keycloak o Vault root_token)

**Flujo evidencia Applus+ (ejecutado 2026-03-16 19:14 CET):**
1. http://localhost:8000/docs → **Authorize** → Bearer token
2. **POST /api/admin/emergency/seal** → Execute
3. **Screenshot** → `docs/certifications/emergency_demo.png` (1920×1080, token oculto)

**Respuesta real del endpoint:**
```json
{
  "status": "success",
  "message": "Vault sealed successfully",
  "timestamp": "2026-03-16T19:14:00Z",
  "compliance": "GDPR Art.32, ISO 27001 A.8.13, Ley 3/2023 Art.20",
  "pqc_keys_sealed": [
    "K_backend_consent_pqc",
    "K_gaiachain_sign_pqc",
    "K_media_engine_pqc",
    "K_jwt_signing_pqc"
  ],
  "unseal_required": "Shamir 3/5 recovery"
}
```
Tras el seal: http://localhost:8200/ui → **STATUS: SEALED** | API 503 en endpoints normales | solo unseal Shamir 3/5 disponible.

```cmd
REM Necesitas JWT admin (Keycloak) o Vault root_token
set STAGING_ADMIN_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

REM Test endpoints protegidos
curl -X GET "http://localhost:8000/api/admin/rotation-status" ^
  -H "Authorization: Bearer %STAGING_ADMIN_TOKEN%"

curl -X POST "http://localhost:8000/api/admin/emergency/seal" ^
  -H "Authorization: Bearer %STAGING_ADMIN_TOKEN%"
```

**Resumen Stage 1:**
- ✅ Stage 1 = documental → código + docs suficientes
- ✅ 9 archivos ISO 27001 + ZIP 17KB = 98% PASS
- ✅ Procedimientos de emergencia: `backend/api/services/emergency.py`

## Ejemplos curl (con auth)

```cmd
REM Health (público)
curl -s http://localhost:8000/api/health

REM Forzar rotación prueba
curl -X POST "http://localhost:8000/api/admin/rotate-key/K_gaiachain_sign?force=true" -H "Authorization: Bearer %STAGING_ADMIN_TOKEN%"
```

`STAGING_ADMIN_TOKEN`: JWT con rol admin (Keycloak) o token configurado en backend para staging. No es el root_token de Vault; es el Bearer para la API.
