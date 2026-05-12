# Guía Ejecutiva de Resiliencia (Windows) - CASTÚO-SYSTEM

## 1. Arquitectura de resiliencia actual

| Componente | Fallback offline | Sincronización post-fallo | Evidencia legal |
|---|---|---|---|
| GaiaChain | SQLite local (`resilience.db`) | `scripts/sync_with_gaiachain.ps1` (programada cada hora) | Transacciones locales marcadas como `local-fallback-...` |
| eIDAS 2 | Sello local con hash SHA-256 | Se reconcilia cuando vuelve GaiaChain | PDFs/TXT con cláusula `Art. 25.2 (continuidad operativa)` |
| Facturación | Facturas locales en `invoices/` | Reenvío a GaiaChain al sincronizar | Hash local + registro en SQLite |
| Certificados soberanos | Certificados locales en `docs/certificates/` | Reconciliación cuando vuelve GaiaChain | XML + PDF/TXT con metadatos de fallback |
| Suscripciones | Base de datos local | Sincronización automática | Registros con marcas de tiempo locales |

## 2. Rutas exactas recomendadas (Windows)

- Proyecto: `C:\Users\traky\OneDrive - FCI\Castuo-System`
- Logs: `C:\logs\castuo`
- Base de datos: `C:\Users\traky\OneDrive - FCI\Castuo-System\resilience.db`
- Certificados: `C:\Users\traky\OneDrive - FCI\Castuo-System\docs\certificates`
- Facturas: `C:\Users\traky\OneDrive - FCI\Castuo-System\invoices`

Recomendación: crea/asegura carpetas antes de programar el Task Scheduler:

```powershell
New-Item -ItemType Directory -Force -Path "C:\logs\castuo"
New-Item -ItemType Directory -Force -Path "C:\Users\traky\OneDrive - FCI\Castuo-System\docs\certificates"
New-Item -ItemType Directory -Force -Path "C:\Users\traky\OneDrive - FCI\Castuo-System\invoices"
```

## 3. Scripts de resiliencia (Windows)

| Script | Ubicación | Frecuencia | Propósito |
|---|---|---|---|
| `sync_with_gaiachain.ps1` | `scripts\sync_with_gaiachain.ps1` | Cada hora | Sincroniza operaciones pendientes con GaiaChain |
| `monitor_critical.ps1` | `scripts\monitor_critical.ps1` | Cada 5 minutos | Monitorea estado crítico y envía alertas (si SMTP existe) |
| `emergency_protocol.ps1` | `scripts\emergency_protocol.ps1` | Cada 6 horas | Activa protocolo de emergencia si GaiaChain lleva offline >24h y la cola supera umbral |

## 4. Tareas programadas (Task Scheduler)

### 4.1 Sincronización (cada hora)
Acción: iniciar programa

- Programa: `powershell.exe`
- Argumentos:
```text
-ExecutionPolicy Bypass -File "C:\Users\traky\OneDrive - FCI\Castuo-System\scripts\sync_with_gaiachain.ps1"
```

### 4.2 Monitoreo crítico (cada 5 minutos)
- Programa: `powershell.exe`
- Argumentos:
```text
-ExecutionPolicy Bypass -File "C:\Users\traky\OneDrive - FCI\Castuo-System\scripts\monitor_critical.ps1"
```

### 4.3 Emergencia (cada 6 horas)
- Programa: `powershell.exe`
- Argumentos:
```text
-ExecutionPolicy Bypass -File "C:\Users\traky\OneDrive - FCI\Castuo-System\scripts\emergency_protocol.ps1"
```

## 5. Verificación manual (fire-drill)

Ejecuta en PowerShell:

```powershell
cd "C:\Users\traky\OneDrive - FCI\Castuo-System"

Invoke-WebRequest -Uri "http://localhost:8001/agents/system/status" -Method Get

$response = Invoke-RestMethod -Uri "http://localhost:8001/agents/certificates/generate" `
    -Method Post `
    -Body '{"lote_id": "CAN-2026-001", "cultivo": "cannabis_medicinal"}' `
    -ContentType "application/json"

Invoke-RestMethod -Uri "http://localhost:8001/agents/system/status" | ConvertTo-Json -Depth 10

.\scripts\sync_with_gaiachain.ps1

Invoke-RestMethod -Uri "http://localhost:8001/agents/system/status" | ConvertTo-Json -Depth 10

.\scripts\monitor_critical.ps1

Get-Content -Path "C:\logs\castuo\gaiachain_sync.log" -Tail 10
Get-Content -Path "C:\logs\castuo\monitor_critical.log" -Tail 10
```

## 6. Rutas críticas (para operar offline)

| Operación | Endpoint |
|---|---|
| Estado general (incluye cola local) | `GET /agents/system/status` o `GET /agents/system/health` |
| Generar certificado soberano | `POST /agents/certificates/generate` |
| Verificar certificado (GaiaChain o fallback local) | `GET /agents/certificates/verify?tx_hash=...` |
| Sincronizar pendientes | `POST /agents/system/sync-gaiachain` |
| Listar evidencia local | `GET /agents/system/local-certificates`, `GET /agents/system/local-invoices` |

## 7. Nota de cumplimiento en modo offline

Los documentos generados localmente incorporan:
- Cláusula de continuidad operativa conforme a `eIDAS 2 (Art. 25.2)`.
- Hash SHA-256 para verificación posterior.
- Evidencia en `resilience.db` para trazabilidad.

