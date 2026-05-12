# Guía Cuentas Pro — CTAEX

Jerarquía de roles, permisos, moderación de contenido y gestión ética (AI Act UE, GDPR).

---

## 1. Modelos

- **ContentRestriction:** allowed_domains, blocked_keywords, max_content_length, allowed_file_types, moderation_level.
- **EthicalGuideline:** equity, transparency, privacy, sustainability, compliance (AI_Act_UE_2024_1689, GDPR, ISO_27001, ISO_9001), data_retention_days, audit_frequency.
- **ProAccountTier:** name (basic|advanced|enterprise|admin), max_agents, max_storage_gb, api_requests_per_minute, support_level, features.
- **ProUserProfile:** user_id, email, full_name, role (user|moderator|admin|auditor|data_protection_officer), tier, restrictions, ethics, status (active|suspended|banned|data_erased).
- **ProAccount:** account_id, owner, members, activity_log, compliance_reports, billing_info, status, **data_protection_officer** (opcional, GDPR Art. 37), **consent_records** (GDPR Art. 7: user_id, purpose, consent_date, recorded_by).

---

## 2. Permisos por rol

| Rol       | agents | content | settings | ethics | users | activity | compliance | billing |
|----------|--------|--------|----------|--------|-------|----------|------------|---------|
| user     | CRUD (propios) | create, read | read, update | read | — | — | — | — |
| moderator| read, update | CRUD + moderate | read | read, update | read, suspend | — | — | — |
| admin    | CRUD | CRUD + moderate | read, update | read, update | CRUD + suspend, ban | — | — | read, update |
| auditor  | read | read | read | read | read | read | read, generate | — |
| data_protection_officer | — | — | — | — | read | read | read, generate | — |

---

## 3. API (prefijo `/pro-accounts`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Lista cuentas Pro | — |
| POST | `/` | Crea cuenta Pro (body: email, full_name, tier, ethics, restrictions) | — |
| GET | `/{account_id}` | Obtiene cuenta (solo miembros) | Bearer / X-User-ID |
| POST | `/{account_id}/members` | Añade miembro (solo owner) | Bearer |
| GET | `/{account_id}/members` | Lista miembros | Bearer |
| PUT | `/{account_id}/members/{user_id}/role` | Cambia rol (solo owner) | Bearer |
| GET | `/{account_id}/activity` | Registro de actividad | admin/auditor |
| PUT | `/{account_id}/restrictions` | Actualiza restricciones de contenido | owner |
| GET | `/{account_id}/compliance` | Informes de cumplimiento | admin/auditor |
| POST | `/{account_id}/compliance` | Genera informe de cumplimiento | admin/auditor |
| POST | `/{account_id}/login` | Login (body: email, password) → access_token | — |
| POST | `/{account_id}/moderate` | Valida contenido (body: content dict) | Bearer |
| GET | `/{account_id}/audit` | Auditoría ética | admin/auditor |
| GET | `/{account_id}/transparency` | Informe transparencia GDPR | Bearer |
| POST | `/{account_id}/consent` | Registra consentimiento (GDPR Art. 7). Body: user_id, purpose | admin / data_protection_officer |
| DELETE | `/{account_id}/users/{user_id}/data` | Solicitud borrado datos (GDPR Art. 17) | admin / data_protection_officer |

**Autenticación:** `Authorization: Bearer <token>` (token devuelto por `/login`) o cabecera `X-User-ID` con `user_id` (desarrollo).

---

## 4. Tiers (ACCOUNT_TIERS)

- **basic:** 5 agentes, 10 GB, 100 req/min, soporte email.
- **advanced:** 20 agentes, 50 GB, 500 req/min, soporte prioritario.
- **enterprise:** 100 agentes, 500 GB, 2000 req/min, soporte 24/7.
- **admin:** Límites máximos, soporte dedicado.

---

## 5. Servicios

- **ContentModerator(restrictions):** moderate_text(text), moderate_url(url), moderate_file(filename, content_type).
- **ComplianceValidator:** validate_account(account), generate_compliance_report(account), **validate_data_retention(account)** (GDPR Art. 5).
- **TransparencyReport:** generate_report(account, user) — datos recogidos, finalidad, retención, derechos GDPR, **third_party_sharing** (partners, purpose, data_types), contacto DPO si existe.

---

## 6. Integración con SABIONDA

- **SabiondaMaster** (get_sabionda_master()): register_pro_account(account), get_user_permissions(user_id), validate_content(account_id, content).
- Al crear una cuenta Pro se registra en el core para permisos y validación de contenido en middleware o en endpoints que lo usen.

---

## 7. Nginx — Headers de seguridad

En `docker/nginx-ctaex-whitelist.conf` se añadieron:

- X-Frame-Options: SAMEORIGIN  
- X-Content-Type-Options: nosniff  
- X-XSS-Protection: 1; mode=block  
- Referrer-Policy: strict-origin-when-cross-origin  
- Content-Security-Policy (default-src 'self'; script-src/style-src con CDN permitidos; etc.)  
- **Strict-Transport-Security** (HSTS): max-age=63072000; includeSubDomains; preload  
- **Rate limiting** en `/api/`: zone=api_limit, 10r/s, burst=20 (definir `limit_req_zone` en bloque http de nginx.conf).

---

## 8. Ejemplos curl

```bash
# Crear cuenta Pro
curl -X POST http://localhost:8000/pro-accounts/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ctaex.es","full_name":"Admin CTAEX","tier":"enterprise","ethics":{"privacy":1.0,"transparency":1.0},"restrictions":{"blocked_keywords":["violencia","odio"],"moderation_level":"high"}}'

# Login (guardar access_token)
curl -X POST http://localhost:8000/pro-accounts/{account_id}/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ctaex.es","password":"cualquiera"}'

# Añadir miembro
curl -X POST http://localhost:8000/pro-accounts/{account_id}/members \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"email":"mod@ctaex.es","full_name":"Moderador","role":"moderator"}'

# Moderar contenido
curl -X POST http://localhost:8000/pro-accounts/{account_id}/moderate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content":{"message":"Texto de prueba","url":"https://ctaex.es/recursos"}}'

# Informe de transparencia
curl http://localhost:8000/pro-accounts/{account_id}/transparency \
  -H "Authorization: Bearer <token>"

# Auditoría ética
curl http://localhost:8000/pro-accounts/{account_id}/audit \
  -H "Authorization: Bearer <token>"

# Registrar consentimiento (GDPR Art. 7) — requiere admin o data_protection_officer
curl -X POST http://localhost:8000/pro-accounts/{account_id}/consent \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<user_id>","purpose":"marketing"}'

# Solicitar borrado de datos (GDPR Art. 17) — requiere admin o data_protection_officer
curl -X DELETE "http://localhost:8000/pro-accounts/{account_id}/users/{user_id}/data" \
  -H "Authorization: Bearer <token>"
```

---

## 9. Checklist

| Paso | Acción | Verificación |
|------|--------|--------------|
| 1 | Modelos pro_account y permissions | `from backend.models.pro_account import ProAccount` |
| 2 | Router pro_accounts | `curl http://localhost:8000/pro-accounts/` |
| 3 | Login y Bearer | POST login → usar token en Authorization |
| 4 | Moderación | POST `/{id}/moderate` con content |
| 5 | Auditoría y transparencia | GET `/{id}/audit`, GET `/{id}/transparency` |
| 6 | Nginx headers | Incluir snippet en sitio CTAEX |
| 7 | Documentar | Esta guía y referencias en docker/README |

---

## 10. Políticas de contenido y ética

- **Contenido bloqueado:** blocked_keywords, dominios no permitidos, tipos de archivo no permitidos.
- **Ética mínima (ComplianceValidator):** equity ≥ 0.8, transparency ≥ 0.9, privacy ≥ 0.95, sustainability ≥ 0.7.
- **Auditorías:** mensual o trimestral según audit_frequency del propietario.

Contacto privacidad: DPO de la cuenta si existe (`data_protection_officer`), si no dpo@ctaex.castu.system.

---

## 11. Troubleshooting

| Error | Causa probable | Solución |
|-------|-----------------|----------|
| `403 Forbidden` al acceder a un endpoint | Falta permiso en el rol | Verificar `ROLE_PERMISSIONS` en `permissions.py` o actualizar rol del usuario (admin/auditor/data_protection_officer según endpoint). |
| `401 Unauthorized` al hacer login | Token caducado o inválido | Generar nuevo token con `POST /{account_id}/login`. |
| `500 Internal Server Error` | Error en backend o base de datos | Revisar logs: `docker logs castuo-ctaex_backend_1` (o equivalente). |
| `429 Too Many Requests` | Límite de API excedido | Reducir frecuencia de peticiones o aumentar `api_requests_per_minute` del tier; en Nginx revisar rate limit (burst/rate). |
