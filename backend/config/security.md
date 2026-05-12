# Configuración de Seguridad (EU/OSS)

## 1. Variables de Entorno

| Variable | Descripción | Valor de ejemplo (dev) |
|---------|-------------|-------------------------|
| `VAULT_ADDR` | URL del servidor Vault (Opción B) | `http://vault:8200` |
| `VAULT_TOKEN` | Token Vault en env (evitar en `.env` git; preferir `VAULT_TOKEN_FILE`) | *(solo runtime efímero)* |
| `VAULT_TOKEN_FILE` | Ruta Docker secret con token Vault | `/run/secrets/vault_token` |
| `KEYCLOAK_URL` | URL de Keycloak | `http://keycloak:8080` |
| `KEYCLOAK_REALM` | Realm de Keycloak | `castuo-system` |
| `KEYCLOAK_CLIENT_ID` | Client ID para el backend | `backend` |
| `KEYCLOAK_CLIENT_SECRET` | Secreto del cliente | `dev-secret` |
| `AUTH_DISABLED` | Desactiva autenticación en desarrollo | `true` |
| `WAZUH_ENABLED` | Habilita envío de logs a Wazuh | `false` |
| `WAZUH_URL` | URL del servidor Wazuh | `http://wazuh:1515` |
| `WAZUH_API_KEY` | API Key para Wazuh | `dev-key` |
| `STABLE_DIFFUSION_EU_URL` | URL del servicio Stable Diffusion EU | `http://sd-eu:7860` |
| `SADTALKER_EU_URL` | URL del servicio SadTalker EU | `http://sadtalker-eu:8000` |
| `ANIMATEDIFF_EU_URL` | URL del servicio AnimateDiff EU | `http://animatediff-eu:7861` |
| `ENVIRONMENT` | Entorno (development/production) | `development` |
| `AUDIT_LOG_PATH` | Ruta del log de auditoría | `backend/logs/audit.log` |
| `CASTUO_ADMIN_GENERAL_BEARER` | Bearer del administrador general (CTAEX/IAM simplificado) | *(solo prod; ver `system_admin_playbook`)* |
| `CASTUO_ADMIN_GENERAL_BEARER_FILE` | Ruta a fichero con el token (Docker secret / sync) | `/run/secrets/castuo_admin_general_bearer` |
| `CASTUO_ROBOTICS_LAB_BEARER_TOKEN_FILE` | Ruta secret lab | `/run/secrets/robotics_lab_bearer` |

**Secretos — estado trazable (prod):** **Opción A** Docker secrets + `*_FILE` (recomendado) · **Opción B** Vault KV + `VAULT_ADDR` + `VAULT_TOKEN_FILE` (`vault.py`) · **no Opción C** tokens en `.env` commiteado. Detalle: `docs/deploy/robotics-lab-hetzner.env.example`, `backend/security/VAULT_KV_PATHS.md`, `docs/legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md`.

## 2. Políticas de Seguridad

### 2.1. Control de Acceso
- **Autenticación**: OIDC con Keycloak (Apache 2.0).
- **Autorización**: RBAC con roles `owner`, `dpo`, `admin`, `admin_general`, `auditor`. El playbook de coherencia/cifrado para `admin_general` está en `backend/models/system_admin_playbook.py`.
- **Auditoría**: Eventos registrados en fichero local y opcionalmente en Wazuh (GPL-2.0).

### 2.2. Gestión de Claves
- **Almacenamiento**: HashiCorp Vault (MPL-2.0). En desarrollo sin `VAULT_ADDR` se usan mocks.
- **Rotación**: Script `backend/scripts/rotate_keys.sh` (ejecutar cada 90 días en producción).
- **Cifrado**: AES-256 para datos en reposo (MinIO); TLS 1.2+ en tránsito (Traefik).

### 2.3. Redes
- **Aislamiento**: Media engines en red interna `media_network` (internal: true).
- **Perímetro**: Traefik (MIT) con TLS 1.2+ y rate-limiting.

### 2.4. Cumplimiento Normativo

| Normativa | Implementación |
|-----------|----------------|
| **GDPR** | Consentimientos granulares, derecho al olvido, registro de actividades (Art. 30). |
| **Ley 3/2023** | Gestión de subvenciones, consentimientos para media, educación forestal. |
| **AI Act** | Transparencia en IA generativa, evaluación de riesgos (Anexo III). |
| **ISO 27001** | Gestión de claves, control de acceso, registro de eventos. |

## 3. Procedimientos

### 3.1. Rotación de Claves
1. Ejecutar `backend/scripts/rotate_keys.sh`.
2. Actualizar secretos en servicios afectados.
3. Registrar en el log de auditoría.

### 3.2. Incidentes de Seguridad
1. **Contención**: Aislar sistemas afectados.
2. **Notificación**: DPO en &lt;24h (GDPR Art. 33); Junta de Extremadura si afecta a subvenciones.
3. **Recuperación**: Restaurar desde backups (OVH/Hetzner).

### 3.3. Auditorías
- **Internas**: Revisión de logs (Wazuh/OpenSearch).
- **Externas**: Anuales (certificación ISO 27001).

## 4. Evidencias para Auditores
- **Logs de auditoría**: `AUDIT_LOG_PATH` o `backend/logs/audit.log`.
- **Transacciones en GaiaChain**: Explorador en https://explorer.gaiachain.es.
- **Informes automáticos**: Generados por `backend/scripts/generate_compliance_report.py <media_id> [media_type]`.
