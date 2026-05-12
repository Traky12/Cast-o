# CASTUO-SYSTEM™ — Arquitectura evolucionada v5.2

Autonomía, cifrado, IoT, blockchain y compliance (AI Act 2024/1689, GDPR, GS1 EPCIS).

---

## 1. Stack tecnológico (autónomo)

| Capa        | Tecnología                          | Propósito                                                                 |
|-------------|-------------------------------------|---------------------------------------------------------------------------|
| Frontend    | HTML/JS + Tailwind (Next.js opcional) | Dashboard agrovoltaico y visualización de datos IoT                      |
| Backend     | FastAPI + Uvicorn (ASGI)            | APIs IoT, drones, blockchain (módulo Sabionda)                           |
| Base de datos | PostgreSQL (Hetzner) + TimescaleDB  | Métricas y series temporales (sensores, clima)                            |
| IoT         | Raspberry Pi 5 + LoRaWAN            | Sensores por granja (temp, humedad, suelo, luz)                          |
| Blockchain  | GS1 EPCIS + Hyperledger             | Trazabilidad inmutable para cultivos y BioCoin                           |
| Monitoring  | Prometheus + Grafana + Alertmanager | Métricas en tiempo real, alertas y compliance                            |
| Automatización | n8n (workflows)                     | Integración drones, riego automático y alertas                            |
| Seguridad   | Firewall + Zero Trust               | Rate limiting, PII masking (GDPR Art.25), circuit breakers                |

---

## 2. Estructura de directorios (mapeo al repo)

En este repositorio la estructura equivale a:

```
CASTUO-SYSTEM/
├── backend/          # api/ → FastAPI (IoT, blockchain, IA, Sabionda)
├── frontend/         # Next.js opcional; actualmente public/ HTML + assets
├── monitor/          # Prometheus + Grafana (puertos 3001, 9090)
├── scripts/          # Automatización (deploy, backup, cifrado)
├── docs/             # Documentación (MONITORING.md, ARCHITECTURE.md)
├── n8n/              # Workflows
└── docker-compose.yml
```

---

## 3. Flujo de trabajo (de code a deploy)

**Deploy 1-click (producción):**

```bash
# 1. Build y levanta la API (métricas integradas)
docker-compose up -d --build api

# 2. Stack de monitoring (Grafana en 3001)
docker-compose -f docker-compose.monitor.yml up -d

# 3. Verificar Prometheus (targets UP)
curl http://localhost:9090/api/v1/targets | grep -i "castuo"

# 4. Accesos
# Landing: http://localhost:3000
# Grafana: http://localhost:3001 (admin/castuo123)
# Prometheus: http://localhost:9090
```

---

## 4. Seguridad y compliance (AI Act + GDPR)

| Barrera          | Configuración                                                                 |
|------------------|-------------------------------------------------------------------------------|
| Rate limiting    | 100 req/min por granja, burst 10 req/s (ventana 60 s).                        |
| Input validation | JSON Schema + regex (bloqueo rm, sudo, SQLi, XSS).                            |
| PII masking     | NIF/IBAN/email → [MASCARA] (GDPR Art.25).                                     |
| Emergency stop   | Temp > 35°C → PAUSE granjas + notificación.                                  |
| Blockchain audit | Transacciones en GS1 EPCIS (hash 32 caracteres).                              |
| Human review     | Acciones por encima de umbral → aprobación dual + registro.                   |

**Cumplimiento legal:**

- **AI Act (UE 2024/1689)**: Modelos y auditorías según normativa.
- **GS1 EPCIS**: Trazabilidad alimentaria (Reglamento 178/2002).
- **Facturación**: SII Facturae u homologado según país.

---

## 5. Módulo Sabionda 3.0 (IA autónoma)

| Agente           | Responsabilidad                                      | Tecnología                    |
|------------------|------------------------------------------------------|-------------------------------|
| Sabionda Core    | Decisiones (IoT → ROI → formación)                   | FastAPI + motor de reglas     |
| Predictive AI    | Optimización de yield (riego, humedad, etc.)         | Mistral + TimescaleDB         |
| Blockchain Agent | Registro inmutable (BioCoin, cultivos)               | Hyperledger + GS1 EPCIS       |
| Legal Compliance | Enmascarado PII, auditorías, alertas legales         | GDPR Art.25 + AI Act          |

**Ejemplo de decisión autónoma (regla tipo Sabionda):**

- Si `temp > 28°C` (ej. rúcula): incrementar ventilación, registrar acción y ROI en blockchain (tx_hash GS1 EPCIS).

---

## 6. Próximos pasos (evolución continua)

- **Escalar granjas**: Kubernetes (Hetzner), auto-scaling basado en Prometheus.
- **Blockchain**: Smart contracts BioCoin (Solidity), oráculos (ej. Chainlink) para datos climáticos.
- **IA**: Modelos predictivos por variedad; Mistral para recomendaciones en tiempo real.
- **Seguridad**: Zero Trust (ej. Tailscale), backups cifrados (ej. Age).

---

Para monitorización en detalle, ver **[MONITORING.md](../MONITORING.md)**.
