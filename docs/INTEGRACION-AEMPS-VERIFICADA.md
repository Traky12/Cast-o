# INTEGRACION AEMPS VERIFICADA (repo)

**Objetivo:** documentar la integracion AEMPS de forma verificable contra endpoints y evidencia que existen en el repo.

---

## 1) Certificacion AEMPS (endpoint existente)

Endpoint real:
- `POST /cannabis/certify_aemps`

Entrada (segun modelo real del repo):
- `batch_id` (string)
- `strain_id` (string)
- `thc_percentage` (float)
- `cbd_percentage` (float)
- `lab_results` (dict)

Salida (en este repo):
- `status: pending` (integracion externa por validar)
- `certification_id`
- `estimated_completion`

---

## 2) Receptor de Webhook AEMPS (endpoint nuevo, implementado)

Endpoint:
- `POST /api/aemps/webhook`

Cabeceras esperadas:
- `X-AEMPS-Signature`: sha256(payload_text + AEMPS_WEBHOOK_SECRET)
- `X-AEMPS-Event`: tipo del evento (si no llega, se intenta leer `event_type` del body)

Comportamiento (verificable):
- Verifica firma antes de procesar.
- Registra evidencia local en SQLite via `POST /agents/system/log-event` (internamente: `local_db.log_system_event`).
- Si GaiaChain esta disponible, registra un witness SHA256 en GaiaChain via la misma logica del repo (`backend/services/gaia_chain_witness.py`).

Requiere:
- variable de entorno `AEMPS_WEBHOOK_SECRET`

---

## 3) Verificacion soberana de certificados (endpoint real)

Para ver un TX de evidencia soberana:
- `GET /agents/certificates/verify/{tx_hash}`

Alias publico compatible:
- `GET /api/certificates/verify/{tx_hash}`

---

## 4) Auditoria end-to-end (script nuevo, endpoints reales)

Script:
- `scripts/Audit-CannabisTrial.ps1`

Usa SOLO endpoints reales del repo:
- `POST /cannabis/certify_aemps`
- `POST /agents/certificates/generate`
- `GET /agents/certificates/verify/{tx_hash}`
- (opcional) `scripts/Register-SecurityEvent.ps1` para witness + evidencia inmutable

Nota:
- La parte AEMPS en este repo devuelve `pending` (integracion externa por validar).

---

## 5) Dashboard de Grafana (verificado por origen de datos)

En Kubernetes, Grafana tiene provisionado datasource `Prometheus`.

Este dashboard se alimenta de metrics Prometheus derivadas de evidencia local:
- `cannabis_trial_status{trial_id,status}`
- `cannabis_trial_compliance{trial_id,standard}`

Estandares mapeados (segun normativas del certificado soberano del repo):
- `AEMPS` <-> `RD 903/2025`
- `GDPR` <-> `GDPR`
- `ISO_17025` <-> (si aparece; por defecto suele ser 0 en este repo)

---

## 6) Wrapper de validacion completa (staging)

Script:
- `scripts/Validate-Full-AEMPS-Flow.sh`

Encadena:
- `scripts/Generate-AEMPS-TrialCertificate.ps1`
- `scripts/Setup-AEMPS-Webhook-Staging.sh`
- `scripts/Audit-CannabisTrial-Detailed.ps1`
- `scripts/Verify-PublicCertificate.ps1`

