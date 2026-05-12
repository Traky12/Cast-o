# Activación de agentes autónomos (100% legal, trazabilidad GaiaChain)

Variables de entorno, endpoints y checklist para poner en marcha los agentes sin romper nada.

---

## 1. Variables de entorno (`.env` o shell)

```ini
# GitLab (CodeAgent-X, MR automáticos)
GITLAB_TOKEN=glpat-tu_token
GITLAB_URL=https://gitlab.com
GITLAB_PROJECT_ID=12345

# Ollama (Sabionda, análisis IA)
OLLAMA_URL=http://localhost:11434

# GaiaChain (trazabilidad opcional)
GAIACHAIN_CLI=/usr/local/bin/gaiachain
GAIA_CHAIN_API_URL=https://gaiachain.castuo-system.com

# Scripts de análisis (opcionales)
CASTUO_ANALYZE_METRIC_SCRIPT=scripts/analyze_metric.py
CASTUO_ANALYZE_YIELD_SCRIPT=scripts/analyze_yield.py

# QuantumSentinel (solo Linux, activar bloqueo iptables)
QUANTUM_SENTINEL_ACTIVATE_PROTECTION=0
WEBCHECK_URL=http://localhost:3000/api/analyze

# Legal / cumplimiento (documentación)
LEGAL_JURISDICTIONS=EU,ES
COMPLIANCE_STANDARDS=GDPR,AI_Act_2024,RD_903/2025,ISO_27001
```

---

## 2. Endpoints de agentes

| Actividad | Método | Ruta | Body (ejemplo) |
|-----------|--------|------|----------------|
| Salud agentes | GET | `/agents/health` | — |
| Validar contexto legal | POST | `/agents/lexcheck-ue/validate` | `{"normativa":"GDPR","contexto":"contrato con cliente X"}` |
| Analizar yield | POST | `/agents/yield-master/analyze` | `{"metric":"yield","current_value":98.5,"crop":"cannabis_medicinal"}` |
| Mejora autónoma | POST | `/agents/autonomous-improvement` | `{"metric":"yield","current_value":98.5,"target_value":99.0}` |
| Optimizar yield | POST | `/agents/yield/optimize` | `{"cultivo":"cannabis_medicinal","lote_id":"CAN-001","metric":"yield","current_value":98.5,"target_value":99.5}` |
| DocuBot generar docs | POST | `/agents/docubot/generate` | `{"improvement_id":"yield_20260319","metric":"yield","before":98.5,"after":99.0,"jurisdiction":"ES","normativas":["RD_903/2025","GDPR"]}` |
| QuantumSentinel escanear | POST | `/agents/quantum-sentinel/scan` | `{"target_domain":"castuo-bunker.local"}` |
| Monitorear germinación | POST | `/agents/germination/monitor` | `{"cultivo":"cannabis_medicinal","lote_id":"CAN-2026-001","semillas":100}` |
| Registrar lote | POST | `/agents/traceability/register` | `{"lot_id":"CAN-2026-001","cultivo":"cannabis_medicinal","semillas":100,"fecha":"2026-03-19T12:00:00Z"}` |
| Informe AEMPS | POST | `/agents/traceability/report` | `{"lot_id":"CAN-2026-001","destino":"AEMPS"}` |
| Analizar cannabinoides | POST | `/agents/cannabis/analyze` | `{"lote_id":"CAN-2026-001","muestra":"MUE-001"}` |
| Cosecha (HarvestBot) | POST | `/agents/harvest/perform` | `{"cultivo":"cannabis_medicinal","lote_id":"CAN-2026-001"}` |
| Generar contrato legal | POST | `/agents/code-agent/generate-contract` | `{"contract_type":"BioCoin_Supply","parties":["CASTÚO-SYSTEM","Cliente X"],"terms":[{"clause":"Trazabilidad","requirement":"Lotes en GaiaChain con hash IPFS","normativa":"RD_903/2025"}],"jurisdiction":"EU"}` |
| **Certificado soberano** | POST | `/agents/certificates/generate` | `{"lote_id":"CAN-2026-001","cultivo":"cannabis_medicinal"}` |
| **Verificar certificado (QR)** | GET | `/agents/certificates/verify/{tx_hash}` | — |
| **Verificar certificado (QR, compatibilidad)** | GET | `/agents/certificates/verify?tx_hash=0xstu...` | — |
| **Verificación pública (QR)** | GET | `/verify/{tx_hash}` | — |

---

## 2.1. Certificados de valor soberano (eIDAS 2 + GaiaChain)

El flujo de certificación soberana genera un **documento con fuerza legal probatoria** (PDF o TXT, XML forense, QR de verificación):

1. **POST `/agents/certificates/generate`** — Ejecuta: datos de cosecha (HarvestBot), análisis de yield, CannabisLab, sello eIDAS 2, registro AI Act, pseudonimización GDPR y generación del certificado (PDF+XML+QR) en `docs/certificates/`.
2. **GET `/verify/{tx_hash}`** — Verificación pública (para el enlace del QR). Devuelve `status`, `certificate_hash`, `legal_seals` y `verification_url`.

Variables útiles: `EIDAS_PRIVATE_KEY_PATH`, `EIDAS_CERT_PATH`, `GAIACHAIN_CLI`. Sin GaiaChain el flujo sigue; `gaiachain_tx` será `gaiachain-no-cli`.

---

## 3. Checklist de puesta en marcha

- [ ] **1. Gemelos / agentes operativos**  
  `curl http://localhost:8000/agents/health` → `status: "OK"`

- [ ] **2. Variables legales**  
  `.env` con `LEGAL_JURISDICTIONS` y `COMPLIANCE_STANDARDS` (o equivalentes en tu despliegue)

- [ ] **3. Contratos base en GaiaChain**  
  Si usas CLI: `gaiachain query --type legal_contract --limit 1` devuelve algo coherente

- [ ] **4. Webhook legal en GitLab**  
  Job `legal_validation` en `.gitlab-ci.yml` que llame a `POST /agents/lexcheck-ue/validate` con los cambios del MR

- [ ] **5. Alertas (n8n/Slack)**  
  Flujo que escuche `/agents/lexcheck-ue/alert` o el webhook que expongas para alertas legales

- [ ] **6. Primera mejora autónoma**  
  `curl -X POST .../agents/autonomous-improvement` con body de ejemplo y comprobar MR en GitLab (si hay token)

- [ ] **7. Documentación generada**  
  Revisar `docs/canvas2040/improvements/` y `docs/improvements/` tras una mejora o tras `POST /agents/docubot/generate`

- [ ] **8. Trazabilidad GaiaChain**  
  Si está configurado: `gaiachain query --type autonomous_improvement --limit 1` (o equivalente en tu API)

---

## 4. Pruebas rápidas (PowerShell)

```powershell
$base = "http://localhost:8000"

# Salud
Invoke-RestMethod -Uri "$base/agents/health" -Method GET

# LexCheck
Invoke-RestMethod -Uri "$base/agents/lexcheck-ue/validate" -Method POST -ContentType "application/json" -Body '{"normativa":"GDPR","contexto":"contrato con cliente X"}'

# Yield analyze
Invoke-RestMethod -Uri "$base/agents/yield-master/analyze" -Method POST -ContentType "application/json" -Body '{"metric":"yield","current_value":98.5,"crop":"cannabis_medicinal"}'

# Mejora autónoma (simulada si no hay GITLAB_TOKEN)
Invoke-RestMethod -Uri "$base/agents/autonomous-improvement" -Method POST -ContentType "application/json" -Body '{"metric":"yield","current_value":98.5,"target_value":99.0}'

# DocuBot
Invoke-RestMethod -Uri "$base/agents/docubot/generate" -Method POST -ContentType "application/json" -Body '{"improvement_id":"yield_20260319","metric":"yield","before":98.5,"after":99.0,"jurisdiction":"ES","normativas":["RD_903/2025","GDPR"]}'

# QuantumSentinel
Invoke-RestMethod -Uri "$base/agents/quantum-sentinel/scan" -Method POST -ContentType "application/json" -Body '{"target_domain":"castuo-bunker.local"}'

# Registrar lote
Invoke-RestMethod -Uri "$base/agents/traceability/register" -Method POST -ContentType "application/json" -Body '{"lot_id":"CAN-2026-001","cultivo":"cannabis_medicinal","semillas":100}'

# Informe AEMPS
Invoke-RestMethod -Uri "$base/agents/traceability/report" -Method POST -ContentType "application/json" -Body '{"lot_id":"CAN-2026-001","destino":"AEMPS"}'
```

---

## 5. Normativas referenciadas

- **GDPR** (protección de datos UE)  
- **AI Act 2024** (transparencia y explicabilidad)  
- **RD 903/2025** (cannabis medicinal, agricultura, trazabilidad)  
- **eIDAS** (firma electrónica y GaiaChain)  
- **ISO 27001** (gestión de la información)  
- **NIST CSF** (QuantumSentinel / seguridad)

Todos los agentes están pensados para trabajar en modo stub o con integraciones opcionales (GaiaChain, Ollama, GitLab, WebCheck) para no bloquear el arranque del sistema.
