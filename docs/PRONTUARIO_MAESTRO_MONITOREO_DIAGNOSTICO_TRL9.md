# Prontuario Maestro de Monitoreo y Diagnóstico
**Versión:** 1.0  
**Fecha:** 20/03/2026  
**Autor:** Gregorio Jiménez Bodes  
**Sistema:** CASTÚO-SYSTEM (TRL9)  
**Endpoint Base:** `http://localhost:8001`

---
## Relacion con ECSE (marco evolutivo)

Este prontuario aporta **evidencia operativa verificable** para el marco **Excelencia Computacional Sistemática Evolutiva (ECSE)**:
- **Documento de referencia**: [`PRONTUARIO_MAESTRO_EVOLUTIVO_ECSE.md`](PRONTUARIO_MAESTRO_EVOLUTIVO_ECSE.md)
- **Documento de integraciones y evolución**: [`PRONTUARIO_MAESTRO_INTEGRACIONES_EVOLUCION_ECSE.md`](PRONTUARIO_MAESTRO_INTEGRACIONES_EVOLUCION_ECSE.md)
- **Proposito**: Proporcionar métricas y registros operativos (ej: `system_status`, `critical_events`, evidencias generadas por scripts) que permitan validar/verificar la evolución en los pilares ECSE.
- **Nota legal**: Este documento **no sustituye** acuerdos de nivel de servicio (SLA), contratos con CTAEX, ni auditorías externas. Sirve como mapa evolutivo y evidencia operativa para procesos internos.

## 1. Endpoints disponibles

Antes de ejecutar los ejemplos PowerShell:
```powershell
$base = "http://localhost:8001"
```

| Endpoint | Método | Descripcion | Ejemplo de uso (PowerShell) |
|---|---|---|---|
| `/docs` | GET | Documentacion OpenAPI/Swagger (HTML) | `Invoke-WebRequest -Uri "$base/docs" | Select-Object -ExpandProperty StatusCode` |
| `/agents/system/health` | GET | Health check (alias) | `Invoke-RestMethod -Uri "$base/agents/system/health"` |
| `/agents/system/status` | GET | Estado detallado (componentes, cola local, eventos criticos y recomendaciones) | `Invoke-RestMethod -Uri "$base/agents/system/status"` |
| `/agents/system/sync-gaiachain` | POST | Sincroniza operaciones pendientes con GaiaChain | `Invoke-RestMethod -Uri "$base/agents/system/sync-gaiachain" -Method Post` |
| `/agents/system/log-event` | POST | Registra un evento critico en la base local (SQLite) | `$payload = @{ event_type="manual_check"; details="ejemplo"; severity="warning" } | ConvertTo-Json -Compress; Invoke-RestMethod -Uri "$base/agents/system/log-event" -Method Post -ContentType "application/json" -Body $payload` |
| `/agents/system/local-certificates` | GET | Lista de certificados generados localmente | `Invoke-RestMethod -Uri "$base/agents/system/local-certificates"` |
| `/agents/system/local-invoices` | GET | Lista de facturas generadas localmente | `Invoke-RestMethod -Uri "$base/agents/system/local-invoices"` |

> Nota: `GET /agents/system/health` y `GET /agents/system/status` devuelven el mismo payload en este repo (alias de compatibilidad).

---

## 2. Diagnostico rapido (15 minutos)

### 2.1 Variables de trabajo
```powershell
$base = "http://localhost:8001"
```

### 2.2 Verificar disponibilidad de la API
```powershell
$swagger = Invoke-WebRequest -Uri "$base/docs" -UseBasicParsing
$swagger.StatusCode  # deberia ser 200
```

### 2.3 Consultar health/status y leer campos clave
```powershell
$health = Invoke-RestMethod -Uri "$base/agents/system/health" -UseBasicParsing

$health.system_status
$health.components.gaiachain.status
$health.components.gaiachain.pending_operations
$health.components.gaiachain.last_sync_attempt

$health.components.storage.disk_usage    # p.ej. "42%"
$health.components.storage.memory_usage  # p.ej. "78%"

$health.components.network.status        # "online" o "degraded" (en este diseño depende de GaiaChain)
$health.critical_events | Select-Object -First 5
$health.recommendations
```

---

## 3. Matriz de sintomas -> endpoint -> accion correctiva

| Sintoma | Endpoint a revisar | Accion correctiva (Windows) |
|---|---|---|
| GaiaChain offline (`components.gaiachain.status = "offline"`) | `GET /agents/system/health` | 1) Ejecutar `.\scripts\sync_with_gaiachain.ps1` 2) Si se requiere ciclo inmediato: `POST /agents/system/sync-gaiachain` |
| Cola local creciente (`pending_operations` alto) | `GET /agents/system/status` | Ejecutar `.\scripts\sync_with_gaiachain.ps1` y revisar `C:\logs\castuo\gaiachain_sync.log` |
| Disco alto (`components.storage.disk_usage` > 80%) | `GET /agents/system/health` | 1) Ver espacio Docker (ej: `docker system df -v`) 2) Aplicar limpieza con criterio (backup verificado) 3) Evitar pruning agresivo sin confirmacion |
| Memoria alta (`components.storage.memory_usage` > 80%) | `GET /agents/system/health` | 1) Ver consumo con `docker stats` 2) Reducir carga (servicios no criticos) 3) Re-evaluar limites/recursos |
| Eventos criticos recientes (`critical_events` no vacio) | `GET /agents/system/health` | Revisar `critical_events[*].details` y, si aplica, registrar/encadenar con `POST /agents/system/log-event` |
| API no responde (timeout o 5xx) | `GET /docs`, `GET /agents/system/health` | 1) Verificar que el servicio escucha en `:8001` 2) Revisar logs del backend segun tu despliegue (docker compose) 3) Reiniciar servicio del backend |

---

## 4. Exportar informe (JSON) para auditoria CTAEX/TRL9

Este snapshot se basa en `GET /agents/system/health` y `GET /agents/system/status`.
```powershell
$outDir = Join-Path (Get-Location) "reports"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$health = Invoke-RestMethod -Uri "$base/agents/system/health" -UseBasicParsing
$status = Invoke-RestMethod -Uri "$base/agents/system/status" -UseBasicParsing

$report = @{
  timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  base = $base
  health = $health
  status = $status
}

$file = Join-Path $outDir ("diagnostic_report_{0}.json" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$report | ConvertTo-Json -Depth 20 | Out-File -FilePath $file -Encoding utf8
Write-Output $file
```

---

## 5. Monitorizacion continua (recomendado)

El repo ya incluye:

- `scripts\monitor_critical.ps1`: consulta `GET /agents/system/health`, aplica umbrales y deja evidencia/log en `C:\logs\castuo\monitor_critical.log` (y otros ficheros).
- `scripts\Generate-ECSEReport.ps1`: exporta evidencia ECSE (JSON/CSV; PDF si PSWritePDF está disponible) y opcionalmente registra un witness SHA256 en GaiaChain.
- Si se desea análisis “Sabionda IA”, usar `-UseSabiondaIA` (llama a `POST /mistral/ask` del backend).
- `scripts\emergency_protocol.ps1`: activa protocolo si GaiaChain lleva offline por un umbral configurado y hay cola.
- `scripts\sync_with_gaiachain.ps1`: ejecuta `POST /agents/system/sync-gaiachain` y escribe evidencia en `C:\logs\castuo\gaiachain_sync.log`.

Referencia de rutas exactas y Task Scheduler: `docs/RESILIENCIA_WINDOWS.md`.

### Ejemplo (evidencia ECSE + Sabionda IA soberana)
```powershell
.\scripts\Generate-ECSEReport.ps1 -OutputFormat JSON,CSV,PDF -UseSabiondaIA -RegisterInGaiaChain -CoopId 1 -MistralModel "mistral-small-latest"
```

> Nota legal prudente: el análisis de Sabionda IA se integra a través del backend; el script exporta evidencia operativa y (si se activa) registra un witness en GaiaChain. Los requisitos de terceros (DPA/SLA/certificados) siguen siendo exigibles por contrato.

