# Barreras de Protección Sabionda v7.1 — NUNCA VIOLAR

Reforzadas para SABIONDA_MASTER v7.1: autonomía global, Cursor CI/CD, HSM, contingencia AEMPS/GlobalGAP.

---

## Resumen ejecutivo

Las barreras v7.1 extienden la v6.1 con **integración Cursor** (workflows de certificación automática AEMPS/GlobalGAP) y alineación con el **propósito supremo 2026–2031** (9.100 farms, €82M valuation, cumplimiento 100 %).

---

## Tabla de barreras v7.1

| Barrera | Nivel | Detalles | Herramienta |
|---------|--------|----------|-------------|
| Rate Limiting | Enterprise | 200 req/min + geobloqueo (Rusia/China) + Cloudflare WAF | Cloudflare |
| Input Validation | Hardened | JSON Schema + Regex + IA (Isolation Forest) | FastAPI Middleware |
| Output Sanitization | Military | 20+ patrones bloqueados (SQLi, XSS, PII) | Python + middleware |
| GDPR/PII Masking | Legal | 7 tipos enmascarados (NIF, IBAN, email) + registro AEPD | AEPD API |
| Emergency Stop | Critical | 7 triggers (temp>30°C, CO₂>500 ppm, yield drop>3 %) + protocolos con Cursor | Cursor Workflows |
| Human Review | Governance | 4 niveles (SMS, video call, aprobación triple) + RPA (UiPath) | UiPath + Twilio |
| Blockchain Audit | Immutable | GS1 EPCIS v2.0 + IPFS + Zero Trust + HSM (Thales) | GaiaChain + Thales HSM |
| Model Guardrails | Ethical | 4 capas (física, datos, ética, legal) + AI Act | SHAP Values |
| Día Cero Protection | Critical | CrowdStrike + Darktrace + Snyk | CrowdStrike Falcon |
| AEMPS/GlobalGAP Contingency | High | Modo degradado + notificación auditores (SGS) | SGS API |
| IP Protection | Legal | OEPM + contratos confidencialidad + código cifrado (GitHub Enterprise) | OEPM API |
| **Cursor Integration** | **Automation** | Workflows para certificación automática (AEMPS/GlobalGAP) | Cursor CI/CD |

---

## Cursor Integration (nueva en v7.1)

- **Certificación AEMPS**: Workflow que valida THC con LIMS/API, registra en GaiaChain y emite certificado. Ver `.github/workflows/aemps.yml`.
- **Certificación batch**: Workflow completo validate LIMS → register GaiaChain → issue certificate. Ver `.github/workflows/certify.yml`.
- **Emergencia**: Script `scripts/emergency_alert.py` para temp>30°C (SMS, pausar farm, log GaiaChain); puede invocarse desde Cursor o cron.

---

## Referencias

- [Sabionda-Barriers-v6.1.md](Sabionda-Barriers-v6.1.md) — Detalle de rangos IoT, regex, PII, emergency stop, human review, audit trail, model guardrails.
- [SABIONDA_MASTER-v7.1.md](../ai/SABIONDA_MASTER-v7.1.md) — Propósito supremo, 12 módulos, roadmap 2026–2031.
