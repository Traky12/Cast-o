# Plan de despliegue en Staging + Certificación ISO 27001

**Duración estimada:** 2-3 semanas  
**Alcance:** CASTÚO-SYSTEM™ — Sistema de gestión de consentimientos forestales y trazabilidad agraria.

---

## FASE 1: Preparación del entorno Staging

### 1.1 Configuración inicial

```bash
# Desde la raíz del repositorio
cd /opt/castuo-staging   # o la ruta de tu servidor staging
git clone <repo> .
git checkout main

# Variables de entorno
cp .env.example .env.staging
# Editar .env.staging con valores reales (Vault, GaiaChain, ZAP, Slack, SMTP)
```

Contenido mínimo para `.env.staging` (referencia en raíz del repo):

- `ENVIRONMENT=staging`
- `VAULT_ADDR`, `VAULT_TOKEN`
- `GAIA_CHAIN_URL`, `GAIA_CHAIN_ADMIN_TOKEN`
- `ZAP_API_KEY`, `ZAP_PROXY_HOST`, `ZAP_PROXY_PORT`
- `SLACK_WEBHOOK_URL`, `SLACK_ALERT_CHANNEL`, `SLACK_API_TOKEN`
- `SMTP_SERVER`, `SMTP_USER`, `SMTP_PASSWORD` (opcional)

### 1.2 Docker Compose para Staging

Se usa `docker-compose.staging.yml` en la raíz del proyecto:

- **vault**: HashiCorp Vault 1.14 con configuración sin HSM (`backend/config/vault_staging.hcl`), sellado Shamir 5/3.
- **zap**: OWASP ZAP para pruebas de seguridad.
- **backend**: API FastAPI (build desde `./backend`).
- **auto-rotate**: mismo imagen que backend, comando `python scripts/auto_rotate_keys.py`.

```bash
docker-compose -f docker-compose.staging.yml --env-file .env.staging build
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d vault zap
```

### 1.3 Inicializar servicios

```bash
# Opción A: desde el host (con vault CLI y port-forward al contenedor vault:8200)
export VAULT_ADDR=http://127.0.0.1:8200
./scripts/staging/init_staging.sh

# Opción B: manual
# 1. Esperar a que Vault esté listo
until vault status -address=http://127.0.0.1:8200 2>/dev/null; do sleep 1; done

# 2. Inicializar (staging sin HSM)
vault operator init -key-shares=5 -key-threshold=3 > vault_init.json
vault operator unseal $(jq -r '.unseal_keys_b64[0]' vault_init.json)
vault operator unseal $(jq -r '.unseal_keys_b64[1]' vault_init.json)
vault operator unseal $(jq -r '.unseal_keys_b64[2]' vault_init.json)

# 3. Habilitar motores
export VAULT_TOKEN=$(jq -r .root_token vault_init.json)
vault secrets enable -path=secret kv-v2
vault secrets enable transit
vault secrets enable -path=pqc transit

# 4. Levantar backend y auto-rotate
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d backend auto-rotate
```

**Importante:** Guardar `vault_init.json` en lugar seguro; en `.env.staging` usar el `root_token` (o un token con políticas de backend) en `VAULT_TOKEN`.

---

## FASE 2: Validación de seguridad en Staging

### 2.1 Pruebas de penetración (ZAP)

```bash
# Escaneo baseline
python security-tests/zap/baseline_scan.py

# Escaneo de API
python security-tests/zap/api_scan.py

# O con el script unificado
./security-tests/scripts/run_zap_scan.sh api

# Analizar resultados (debe salir con exit code 0)
python security-tests/scripts/analyze_results.py
```

Salida esperada tipo:

```
Resumen de vulnerabilidades:
   - Críticas: 0/0
   - Altas: 2/5
   - Medias: 8/20
   - Bajas: 15/50
✅ Análisis completado. El escaneo cumple con los requisitos de seguridad.
```

### 2.2 Verificar rotación de claves

```bash
curl -X GET "http://localhost:8000/api/admin/rotation-status" \
  -H "Authorization: Bearer $STAGING_ADMIN_TOKEN"

# Prueba de rotación forzada
curl -X POST "http://localhost:8000/api/admin/rotate-key/K_gaiachain_sign?force=true" \
  -H "Authorization: Bearer $STAGING_ADMIN_TOKEN"
```

### 2.3 Procedimientos de emergencia

```bash
# Simular sellado
curl -X POST "http://localhost:8000/api/admin/emergency/seal" \
  -H "Authorization: Bearer $STAGING_ADMIN_TOKEN"

# Comprobar: vault status → Sealed: true

# Desbloquear (usar shares de vault_init.json)
curl -X POST "http://localhost:8000/api/admin/emergency/unseal" \
  -H "Authorization: Bearer $STAGING_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"shares": ["share1", "share2", "share3"]}'
```

### 2.4 Integración con GaiaChain

```bash
# Eventos de vulnerabilidades
curl -X GET "https://gaiachain-staging.castuo-system.eu/api/v1/events?action_type=vulnerability_detected" \
  -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_TOKEN"

# Registro de escaneo
curl -X GET "https://gaiachain-staging.castuo-system.eu/api/v1/events?action_type=security_scan_completed" \
  -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_TOKEN"
```

---

## FASE 3: Documentación para ISO 27001

### 3.1 Generar documentación de cumplimiento

```bash
# Región Extremadura (por defecto)
python compliance_docs/scripts/generate_compliance_docs.py extremadura

# Con media_id de prueba
python compliance_docs/scripts/generate_compliance_docs.py extremadura sd-eu-20260420-12345-67890
```

Archivos generados en `compliance_docs/generated/`:

- `02.01.01_Registro_Actividades_Tratamiento.md` (GDPR Art. 30)
- `02.02.03_Gestion_Consentimientos_Ley_3_2023_Extremadura.md`
- `02.03.03_AI_Act_Self-Assessment.md`
- `02.04.01_Declaracion_Aplicabilidad_ISO27001.md`
- `02.05.01_Procedimiento_SIGPAC_Extremadura.md`
- `04.03.01_Contrato_Propietario_Forestal_ES_Extremadura.md`
- `06.01.01_Checklist_Auditoria_Monthly_extremadura.md`
- `06.01.01_Checklist_Auditoria_Quarterly_extremadura.md`
- `compliance_report_<media_id>.md`

### 3.2 Declaración de Aplicabilidad ISO 27001

Contenido clave en `02.04.01_Declaracion_Aplicabilidad_ISO27001.md`:

- **A.5** Políticas de seguridad de la información
- **A.6** Organización (roles, contacto con autoridades)
- **A.7** Seguridad de los recursos humanos (Sabionda Educa Pro)
- **A.8** Gestión de activos (inventario en GaiaChain)
- **A.9** Control de accesos (Keycloak + Vault)
- **A.10** Criptografía (AES-256 + Kyber-768)
- **A.12** Operaciones (gestión de vulnerabilidades, ZAP + auto-rotate)
- **A.16** Gestión de incidentes (emergency.py)
- **A.17** Continuidad (backups IPFS/Arweave, SLA)
- Controles excluidos con justificación

### 3.3 Evidencias para auditoría

| Documento | Ubicación | Notas |
|-----------|-----------|--------|
| Declaración de Aplicabilidad ISO 27001 | `compliance_docs/generated/02.04.01_...` | Controles implementados |
| Registro de Actividades GDPR (Art. 30) | `02.01.01_Registro_Actividades_Tratamiento.md` | Actualizado por script |
| Self-Assessment AI Act | `02.03.03_AI_Act_Self-Assessment.md` | Anexo III |
| Procedimientos de emergencia | `backend/api/services/emergency.py` | Documentados en código |
| Informes de escaneo | `security-tests/reports/` | Últimos 30 días |
| Registros GaiaChain | Explorer staging | Últimos 3 meses |
| Rotación de claves | `backend/scripts/auto_rotate_keys.py` | Frecuencia y procedimientos |
| Contratos propietarios forestales | `04.03.01_Contrato_Propietario_Forestal_...` | Plantilla legal |

---

## FASE 4: Certificación ISO 27001

### 4.1 Entidades certificadoras (España/Extremadura)

| Entidad | Acreditación | Enfoque | Coste estimado | Plazo |
|---------|--------------|---------|----------------|-------|
| AENOR | ENAC | Presencial + remoto | €8.000–12.000 | 4–6 semanas |
| Bureau Veritas | Internacional | Cloud/sistemas críticos | €9.000–14.000 | 6–8 semanas |
| SGS | Internacional | Agritech | €7.000–11.000 | 5–7 semanas |
| Applus+ | ENAC | Flexibles con startups | €6.500–10.000 | 4 semanas |

Recomendación: **Applus+** (equilibrio coste/plazo y experiencia con proyectos innovadores).

### 4.2 Proceso de certificación

- **Preparación:** revisión documental interna, corrección de no conformidades.
- **Stage 1:** auditoría documental.
- **Stage 2:** auditoría de implementación.
- **Emisión del certificado.**
- **Mantenimiento:** auditoría de seguimiento anual.

### 4.3 Checklist Stage 1 (documentos en PDF)

- Declaración de Aplicabilidad
- Política de Seguridad de la Información
- Procedimiento de Gestión de Riesgos
- Procedimientos de Emergencia (emergency.py + documentación)
- Registros de rotación de claves
- Informes de escaneo (últimos 3)
- Evidencia de formación (Sabionda Educa Pro)
- Contratos con terceros

### 4.4 Preparación Stage 2 (pruebas típicas del auditor)

- Control de accesos: Keycloak + Vault (logs).
- Gestión de claves: auto_rotate_keys.py + HSM/Vault logs.
- Cifrado: TLS 1.2+ en Traefik, AES-256 en Vault.
- Respuesta a incidentes: emergency.py + Slack/GaiaChain.
- Gestión de vulnerabilidades: security-tests/ + GaiaChain.
- Continuidad: backups Vault, IPFS/Arweave.
- Cumplimiento legal: Registro de actividades (GDPR Art. 30).

---

## FASE 5: Mantenimiento post-certificación

### 5.1 Auditorías internas trimestrales

```bash
# Generar checklist trimestral
python compliance_docs/scripts/generate_compliance_docs.py extremadura
# Mover checklist a carpeta de auditorías, p.ej. audits/2026-Q2/

# Escaneo de seguridad
python security-tests/zap/baseline_scan.py
python security-tests/zap/api_scan.py

# Estado de rotación
curl -X GET "http://localhost:8000/api/admin/rotation-status" \
  -H "Authorization: Bearer $ADMIN_TOKEN" > audits/2026-Q2/rotation_status.json
```

### 5.2 Revisión anual de riesgos

- Cambios en el sistema (APIs, arquitectura, normativas, proveedores).
- Tabla de riesgos: probabilidad, impacto, mitigación, acciones propuestas.
- Acciones correctivas y próxima fecha de revisión.

### 5.3 Actualización de documentación

```bash
# Regenerar documentación de cumplimiento
python compliance_docs/scripts/generate_compliance_docs.py extremadura
python compliance_docs/scripts/generate_compliance_docs.py andalucia
python compliance_docs/scripts/generate_compliance_docs.py portugal
```

---

## Resumen ejecutivo

- **Seguridad:** cifrado post-cuántico (Kyber-768), rotación automática, procedimientos de emergencia validados.
- **Cumplimiento:** ISO 27001, GDPR (Art. 30, 33, 34), Ley 3/2023, AI Act (Art. 52, Anexo III).
- **Detección:** escaneos ZAP, sin críticas; altas mitigadas; cobertura de controles auditables.
- **Auditoría:** documentación generada para varias regiones; evidencias en GaiaChain y en código.

### Acciones inmediatas recomendadas

```bash
# 1. Desplegar staging
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d

# 2. Pruebas de seguridad
./security-tests/scripts/run_zap_scan.sh api

# 3. Documentación para auditoría
python compliance_docs/scripts/generate_compliance_docs.py extremadura
```

Revisar y corregir vulnerabilidades altas (p. ej. headers de seguridad/CSP en Traefik). Contactar a la entidad certificadora con la Declaración de Aplicabilidad, informes de seguridad y procedimientos de emergencia.

---

## Inversión estimada

| Concepto | Coste | Notas |
|----------|--------|--------|
| Certificación ISO 27001 | €8.000–10.000 | Stage 1 + Stage 2 + certificado |
| Auditorías de seguimiento | €2.000/año | 1 auditoría anual |
| Mantenimiento HSM | €1.500/año | Soporte Thales Luna 9 (producción) |
| **Total año 1** | **€9.500–11.500** | Incluye certificación inicial |
| **Total año 2+** | **€3.500/año** | Solo mantenimiento |
