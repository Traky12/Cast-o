# Barreras de Protección Sabionda v6.1 — NUNCA VIOLAR

Reforzadas para autonomía global, protección contra ciberataques avanzados y cumplimiento AEMPS/GlobalGAP.

---

## 1. Rate limiting enterprise + geobloqueo

- **Límites**: 200 req/min por farm (antes 100), 500 req/hora por usuario, burst 20 req/seg (ventana 60 s).
- **IP whitelist**: OVH ENS Madrid, n8n cloud, Hetzner CAX21, AWS Frankfurt, Google Cloud (USA), Azure West Europe.
- **Geobloqueo**: Bloquear IPs de Rusia, China, Corea del Norte, Irán. Excepciones: CTAEX, GlobalGAP, AEMPS.
- **Circuit breaker**: CPU >90 % → PAUSE 2 min; memoria >85 % → PAUSE 1 min; latencia >500 ms → alerta DevOps + registro GaiaChain.
- **Herramientas**: Cloudflare WAF, Prometheus + Alertmanager.
- **Métricas**: Tasa de bloqueo IPs maliciosas >99 %; tiempo de respuesta ante picos <1 s.

---

## 2. Input validation (JSON Schema + regex + IA)

### IoT schema reforzado

| Parámetro | Rango válido | Normativa | Acción si incumplimiento |
|-----------|--------------|-----------|---------------------------|
| farm_id | 1–9100 | ISO 17025 | Rechazar + registrar en GaiaChain |
| temp | -10 °C a 50 °C | Reglamento UE 2018/848 | Alertar CTAEX + bloquear sensor |
| hum | 0–100 % | UNE 100021 | Recalibrar con calibration.py |
| soil_moisture | 0–100 % | PAC 2027 | Validar con LIMS CTAEX |
| light | 0–100 000 lux | ISO 17025 | Ajustar con yield_optimizer |
| co2 | 0–2000 ppm | ODS 13 | Alertar si >500 ppm |
| energy_consumption | 0–10 kWh/m² | ODS 7 | Optimizar con agrovoltaica |

### Regex BLOCK (SQLi/XSS/comandos)

- Comandos: `drop.*table|shutdown|halt|rm.*-rf|wget.*sh|python.*-c|exec.*sp_|xp_cmdshell|alter.*table|truncate|--|;.*sh|&&.*rm|>.*/dev/`
- SQLi/XSS: `DROP.*TABLE|DELETE.*FROM|UNION.*SELECT|--|<script.*>|javascript:|onload=|document\.cookie|eval\(|child_process`

### Validación con IA

- Modelo de anomalías (ej. Isolation Forest) sobre datos históricos de requests válidos; si `predict == -1` → bloquear y registrar.
- **Métricas**: False positives <1 %; tasa de bloqueo inputs maliciosos >99,9 %.

---

## 3. Output sanitization (hardened + zero trust)

- **Patrones bloqueados**: Comandos peligrosos, SQLi, XSS, PII (NIF/DNI/NIE, passport, tarjeta, geolocation precisa).
- **Zero trust**: Enmascaramiento dinámico (NIF, email, passport, credit_card, geolocation 3 decimales, DNI/NIE, IP últimos 3 dígitos). Respuestas JSON firmadas (SHA-256 + clave CASTÚO).
- **Métricas**: Datos personales enmascarados 100 %; respuestas firmadas 100 %.

---

## 4. GDPR Art.25 + AI Act

- **Nuevos campos enmascarados**: passport_number → [PASSPORT_MASCARA]; credit_card → [TARJETA_MASCARA]; geolocation → 3 decimales; dni/nie → [DNI_MASCARA]/[NIE_MASCARA]; ip_address → últimos 3 dígitos (192.168.1.X).
- **AI Act high-risk**: Revisión humana para acciones >€500. Registro en EU AI Database (propósito, datos entrenamiento, métricas de sesgo). Explicabilidad con SHAP.
- **Métricas**: Modelos registrados 100 %; sesgo <5 % (fairlearn).

---

## 5. Emergency stop (triggers + contingencia)

| Trigger | Umbral | Acción | Responsable |
|---------|--------|--------|-------------|
| Yield drop | >3 % | Pausar farms afectadas + alertar CTAEX | DevOps |
| Temperatura | >30 °C | Ventilación 100 % + riego + alerta AEMPS | IoT |
| Humedad | <30 % | Riego emergencia + revisión <1 h | Agrónomos |
| CO2 | >500 ppm | Extractores + notificar sostenibilidad | Sostenibilidad |
| Sensores offline | >10 min | Modo manual + alerta DevOps | DevOps |
| Energía | >5 kWh/m² | Optimizar consumo | Energía |
| CPU | >90 % | Pausar 2 min + alerta DevOps | DevOps |
| RAM | >85 % | Pausar 1 min + registrar GaiaChain | DevOps |

**Contingencia GaiaChain**: Modo degradado (Redis `pending_blockchain_tx`), notificar CTAEX, sincronizar al restaurar. **DDoS**: Cloudflare "Under Attack", fail2ban, registro en GaiaChain.

---

## 6. Human review (4 niveles)

| Rango coste | Aprobación | Canal | Plazo |
|-------------|------------|--------|--------|
| <€50 | Auto (AGENT 8) | — | Inmediato |
| €50–€500 | SMS CEO/CTO | Twilio | <1 h |
| €500–€1K | Video call (técnico + legal) | Zoom | <4 h |
| >€1K | Triple (Legal + Técnico + CEO) | Video + acta | <24 h |
| Cambios críticos (ej. THC >0,25 %) | Manual | Slack + email | Inmediato |

RPA (UiPath): validar certificaciones AEMPS si coste <€500; informes sostenibilidad mensuales.

---

## 7. Audit trail blockchain (GS1 EPCIS v2.0 + IPFS)

- **Campos en GaiaChain**: farm_id, action, timestamp, user (enmascarado), compliance (GDPR, AI_Act, PAC_2027, GlobalGAP), sustainability (co2_saved, water_saved, energy_saved), ipfs_hash, signature.
- **Almacenamiento**: OVH ENS Madrid, Backblaze B2 (backups 5 min), IPFS (inmutable), GaiaChain.
- **Zero trust**: MFA + firma digital + registro en 3 sistemas.

---

## 8. Model guardrails (4 capas)

- **Físico**: No riego si humedad >90 %; no superar 30 °C cannabis (RD 903/2025); no exceder 5 kWh/m² (ODS 7).
- **Datos**: Validación cruzada IoT–LIMS–Blockchain; datos fuera de rango → alertar CTAEX <1 min; registrar en GaiaChain (EPCIS v2.0).
- **Ético (AI Act)**: No optimizar si huella carbono +5 %; priorizar menor consumo agua (ODS 12); transparencia (SHAP); explicar decisiones (Art. 13).
- **Legal**: SII Facturae, PAC 2027, GDPR ENS Alto, registro blockchain para auditorías.

---

## 9. Barreras adicionales v6.1

- **Día cero**: CrowdStrike Falcon, Darktrace, Snyk; aislar en <1 min; notificar CTAEX/AEMPS <10 min; registrar en GaiaChain.
- **Validación datos con blockchain**: Firma por sensor (clave pública en GaiaChain); hash del dato anterior (cadena de custodia); validación por 3 nodos.
- **Contingencia AEMPS/GlobalGAP**: Modo degradado con últimos datos válidos LIMS CTAEX; notificar auditores (SGS); registrar en GaiaChain (hora fallo, datos backup, firma responsable).
- **Propiedad intelectual**: OEPM, NDA con CTAEX/empleados, código en repositorios privados (GitHub Enterprise).

---

## Checklist de verificación v6.1

| Barrera | Nivel | Detalles | Estado | Responsable |
|---------|--------|----------|--------|-------------|
| Rate limiting | Enterprise | 200 req/min + geobloqueo + Cloudflare WAF | ✅ Activo | DevOps |
| Input validation | Hardened | JSON Schema + Regex + IA (Isolation Forest) | ✅ Activo | Seguridad |
| Output sanitization | Military | 20+ patrones + firmado digital | ✅ Activo | Backend |
| GDPR/PII masking | Legal | 7 tipos enmascarados + precisión reducida | ✅ Activo | Legal |
| Emergency stop | Critical | 7 triggers + protocolos contingencia | ✅ Activo | DevOps |
| Human review | Governance | 4 niveles + RPA (UiPath) | ✅ Activo | Compliance |
| Blockchain audit trail | Immutable | EPCIS v2.0 + IPFS + Zero Trust | ✅ Activo | Blockchain |
| Model guardrails | Ethical | 4 capas + AI Act | ✅ Activo | IA Team |
| Día cero | Critical | CrowdStrike + Darktrace + Snyk | ✅ Activo | Seguridad |
| Contingencia AEMPS/GlobalGAP | High | Modo degradado + notificación auditores | ✅ Activo | Legal |
| IP protection | Legal | OEPM + NDA + código cifrado | ✅ Activo | Legal |

---

## Próximos pasos implementación

| Acción | Plazo | Responsable | Documentación |
|--------|--------|-------------|---------------|
| Implementar geobloqueo | 1 semana | DevOps | [GeoBlock-Implementation.md](GeoBlock-Implementation.md) |
| Validación con IA (anomalías) | 2 semanas | IA Team | [Anomaly-Detection-Guide.md](../ai/Anomaly-Detection-Guide.md) |
| Configurar CrowdStrike | 1 mes | Seguridad | [CrowdStrike-Setup.md](CrowdStrike-Setup.md) |
| Firmar datos IoT con blockchain | 3 semanas | Blockchain Team | [IoT-Blockchain-Signature.md](../traceability/IoT-Blockchain-Signature.md) |
| Actualizar contingencia AEMPS | 2 semanas | Legal | [AEMPS-Contingency-Plan.md](../compliance/AEMPS-Contingency-Plan.md) |
| Registrar modelos en EU AI Database | 1 mes | IA Team | [EU-AI-Database-Registration.md](../compliance/EU-AI-Database-Registration.md) |
