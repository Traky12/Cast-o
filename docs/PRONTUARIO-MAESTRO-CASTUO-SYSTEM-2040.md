# Prontuario maestro CASTÚO-SYSTEM 2040

**Usabilidad · Trazabilidad · Crecimiento · Legalidad**  
*Vista ejecutiva (1 página) — alinear operación diaria con evidencia y territorio.*

---

## Estructura ejecutiva

```
USABILIDAD  ←  TRAZABILIDAD  ←  CRECIMIENTO  ←  LEGALIDAD
     ↓              ↓                ↓               ↓
Dashboard    GaiaChain         ICEX / CTAEX      DPIA / ISO 27001
SSE Live     SHA256            HLTH 2026         DPO + anexos
Kids UX      Air-gapped        Terracota         Qubes / Whonix / Parrot
```

**Relación con marco ECSE:** [PRONTUARIO_MAESTRO_EVOLUTIVO_ECSE.md](./PRONTUARIO_MAESTRO_EVOLUTIVO_ECSE.md)  
**Plan 90 días (EU / aceleradoras / técnico):** [ops/PLAN-90-DIAS-ENTERPRISE-EU-2026.md](./ops/PLAN-90-DIAS-ENTERPRISE-EU-2026.md)  
**Prontuario legal (LCSP / RGPD / marco certificación):** [legal/PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md](./legal/PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md)

---

## 1. Usabilidad (dashboard + UX)

| Módulo   | Endpoint / ruta              | UX                    | Métricas / notas        |
|----------|------------------------------|------------------------|-------------------------|
| Dashboard| `/` → `/dashboard`, SSE `/agents/dashboard/stream` | Tiempo real (~3 s)     | CPU / Mem / Health      |
| API Docs | `/docs`, `/redoc`            | OpenAPI                | Accesible sin auth demo |
| Kids     | `/kids/` (marco en `docs/ops/kids/`) | Edad / nivel educativo | Protocolos en expediente |
| Gemelo   | `POST /agents/gemelo/ingest` | Test 1-click en panel  | Validar despliegue si 404 |
| Cámara   | MotionEye + `GET /agents/camera/stream`, snapshot `/agents/camera/frame/latest` | SSE + JPEG proxy | [MOTIONEYE-CASTUO-INTEGRATION.md](./ops/MOTIONEYE-CASTUO-INTEGRATION.md) |

**Estándar front:** vanilla JS + SSE, sin dependencias npm en el panel base.

**Base URL:** según despliegue (`http://127.0.0.1:8000` o `:8001`; unificar en runbook).

---

## 2. Trazabilidad (GaiaChain + SHA256)

```
SHA256 → GaiaChain Witness → security-events/yyyyMMdd/txid.json
              ↓
   /agents/system/log-event → backend + evidencias operativas
```

| Acción | Script / referencia |
|--------|---------------------|
| Registrar evento de seguridad | `.\scripts\Register-SecurityEvent.ps1 -EventType "metric_update"` |
| KPIs + registro GaiaChain (cuando aplique) | `.\scripts\Generate-ECSEReport.ps1 -RegisterInGaiaChain` |

**Enlace legal-técnico:** [ARQUITECTURA-LEGAL-Y-TECNICA-VERIFICADA.md](./ARQUITECTURA-LEGAL-Y-TECNICA-VERIFICADA.md), [ENLACES-DE-TRAZABILIDAD.md](./ENLACES-DE-TRAZABILIDAD.md)

---

## 3. Crecimiento (ICEX + CTAEX)

| Oportunidad        | Plazo  | Pitch                         | Estado (revisar)   |
|--------------------|--------|-------------------------------|--------------------|
| HLTH Europe        | 31/03  | Hidropónicos / salud          | Inscripción        |
| Brasil virtual     | Marzo  | Microgreens nutracéuticos     | Misión virtual     |
| Singapur biotech   | Q2     | Digital twin / 5G             | Jornadas           |
| CTAEX TRL10.1      | Hoy    | Backend LIVE + air-gapped     | Demo operativa     |

**Demo técnica:** [ops/icex-hlth-europe/DEMO-TRL10.1.md](./ops/icex-hlth-europe/DEMO-TRL10.1.md)

---

## 4. Legalidad (DPIA + anexos)

| Tema            | Evidencia / acción |
|-----------------|--------------------|
| GDPR Art. 30    | [legal/DPIA-CASTUO-SYSTEM.md](./legal/DPIA-CASTUO-SYSTEM.md) |
| DPO             | Contrato vigente (María Gómez López — verificar expediente) |
| Anexos I–VII    | HolographicEncryption / anexos del expediente |
| Kids            | [ops/kids/validacion-por-edad-y-nivel-educativo-2026.md](./ops/kids/validacion-por-edad-y-nivel-educativo-2026.md) |
| ISO 27001 / hardening | [ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md](./ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md) |

---

## Flujo operativo diario

```powershell
# Mañana — demo CTAEX / operación
# Dashboard SSE (ajustar puerto)
Start-Process "http://localhost:8000/dashboard"
# o: http://localhost:8001/dashboard

.\scripts\Generate-ECSEReport.ps1   # KPIs + cadena cuando proceda

# Mediodía — ICEX / gemelo
curl -X POST "http://127.0.0.1:8000/agents/gemelo/ingest" -H "Content-Type: application/json" -d "{\"agent_type\":\"demo\",\"sensor_data\":{}}"

# Tarde — backup / air-gapped
python .\scripts\pen_drive\validate_transfer.py
```

---

## KPIs maestro (revisión semanal)

| Métrica           | Objetivo | Actual (ejemplo) | Estatus |
|-------------------|----------|------------------|---------|
| Backend uptime    | 99,9 %   | Ventana LIVE     | 🟢 / revisar |
| SSE intervalo     | 3 s      | Alineado código  | 🟢 |
| GaiaChain TX      | 10/día   | Según entorno    | 🟡 |
| Docs cifrados / evidencias | N definido | Inventariar | 🟢 / 🟡 |
| HLTH inscripción  | 31/03    | Pendiente / hecha| 🔴 / 🟢 |

---

*Última actualización: documento vivo; fechas y estados comerciales deben revisarse en cada sprint.*
