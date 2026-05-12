# Generate-ECSEReport.ps1
#
# Genera informes ECSE (JSON/CSV/posible PDF) a partir de endpoints implementados en este repo.
# - Datos base: GET /agents/system/health y GET /agents/system/status
# - Métricas adicionales (si existieran): opcional, se intentan y si no están se ignoran
#
# Registro inmutable opcional (GaiaChain Witness):
# - POST <GAIA_CHAIN_API_URL>/api/v1/witness (payload hash + coop_id)
#
param(
    [string[]]$OutputFormat = @("JSON", "CSV"),
    [switch]$RegisterInGaiaChain,
    [int]$CoopId = 1,
    [string]$OutputRoot = "reports/ecse",
    [switch]$UseSabiondaIA,
    [string]$MistralModel = "mistral-small-latest",
    [string]$BackendUrl = "http://localhost:8001",
    [switch]$LogEventInBackend = $true
)

$ErrorActionPreference = "Stop"

# Compatibilidad interna: el resto del script usa $BaseUrl.
$BaseUrl = $BackendUrl

function _Write-Info([string]$msg) { Write-Host $msg -ForegroundColor Green }
function _Write-Warn([string]$msg) { Write-Host $msg -ForegroundColor Yellow }
function _Write-Err([string]$msg) { Write-Host $msg -ForegroundColor Red }

function Invoke-GetJsonOrNull {
    param([string]$Uri)
    try {
        return Invoke-RestMethod -Uri $Uri -UseBasicParsing -Method Get
    } catch {
        return $null
    }
}

function Invoke-PostJsonOrNull {
    param(
        [string]$Uri,
        [Parameter(Mandatory=$true)]$BodyObj
    )
    try {
        $body = $BodyObj | ConvertTo-Json -Depth 30 -Compress
        return Invoke-RestMethod -Uri $Uri -UseBasicParsing -Method Post -ContentType "application/json" -Body $body
    } catch {
        return $null
    }
}

function Parse-PercentValue {
    param([Parameter(Mandatory=$false)]$Value)
    try {
        # Espera "42%" o numero; devuelve float.
        if ($null -eq $Value) { return 0.0 }
        if ($Value -is [string]) {
            $v = $Value -replace "%", ""
            if ([string]::IsNullOrWhiteSpace($v)) { return 0.0 }
            return [double]$v
        }
        return [double]$Value
    } catch {
        return 0.0
    }
}

# 1) Leer estado del sistema (endpoint implementado)
$health = Invoke-GetJsonOrNull -Uri "$BaseUrl/agents/system/health"
$status = Invoke-GetJsonOrNull -Uri "$BaseUrl/agents/system/status"
#
# Nota: este repo puede o no exponer /agents/system/metrics según el despliegue.
$metrics = Invoke-GetJsonOrNull -Uri "$BaseUrl/agents/system/metrics"
if ($null -eq $health -and $null -eq $status) {
    throw "No se pudo leer /agents/system/health ni /agents/system/status en $BaseUrl."
}
$h = if ($null -ne $health) { $health } else { $status }
$s = if ($null -ne $status) { $status } else { $health }

# 2) Derivar KPIs (disco/memoria/cola/eventos)
$gaiaStatus = $null
$pendingOps = 0
$lastSync = $null
$diskUsageStr = $null
$memoryUsageStr = $null
$criticalEvents = @()

try {
    $gaiaStatus = $s.components.gaiachain.status
    $pendingOps = [int]$s.components.gaiachain.pending_operations
    $lastSync = $s.components.gaiachain.last_sync_attempt
} catch { }

try {
    $diskUsageStr = $s.components.storage.disk_usage
    $memoryUsageStr = $s.components.storage.memory_usage
} catch { }

try {
    $criticalEvents = @($s.critical_events)
} catch { $criticalEvents = @() }

$diskUsagePct = Parse-PercentValue -Value $diskUsageStr
$memoryUsagePct = Parse-PercentValue -Value $memoryUsageStr
$criticalEventsCount = @($criticalEvents).Count

# KPIs opcionales (si el endpoint de métricas existe)
$metricsAvailable = ($null -ne $metrics)
$uptimePct = $null
$cpuUsage = $null
$networkLatency = $null

if ($metricsAvailable) {
    try {
        if ($null -ne $metrics.uptime -and $null -ne $metrics.total_time -and ([double]$metrics.total_time) -ne 0) {
            $uptimePct = [math]::Round(([double]$metrics.uptime / [double]$metrics.total_time) * 100, 2)
        }
    } catch { }
    try {
        if ($null -ne $metrics.cpu_usage) {
            $cpuUsage = [double]$metrics.cpu_usage
        }
    } catch { }
    try {
        if ($null -ne $metrics.network_latency) {
            $networkLatency = [double]$metrics.network_latency
        }
    } catch { }
}

# 2.1) KPIs y cumplimiento (umbrales configurables como valores "de trabajo" por defecto)
$ThresholdDisk = 80.0
$ThresholdDiskCritical = 90.0
$ThresholdMemory = 80.0
$ThresholdMemoryCritical = 90.0
$ThresholdCpu = 90.0
$ThresholdNetworkLatency = 50.0

$autonomyOk = ($diskUsagePct -lt $ThresholdDisk) -and ($memoryUsagePct -lt $ThresholdMemory)
$resilienceOk = ($gaiaStatus -eq "online")
$securityOk = ($criticalEventsCount -eq 0)
$cpuOk = if ($null -ne $cpuUsage) { ($cpuUsage -lt $ThresholdCpu) } else { $true }
$autonomyOk = $autonomyOk -and $cpuOk

$continuousImprovementOk = (($pendingOps -le 0) -or $null -eq $pendingOps) -and ($securityOk)
if ($null -ne $networkLatency) {
    $continuousImprovementOk = $continuousImprovementOk -and ($networkLatency -lt $ThresholdNetworkLatency)
}

$ecseCompliance = @{
    Autonomy = if ($autonomyOk) { "✅" } else { "⚠️" }
    Resilience = if ($resilienceOk) { "✅" } else { "⚠️" }
    Security = if ($securityOk) { "✅" } else { "⚠️" }
    ContinuousImprovement = if ($continuousImprovementOk) { "✅" } else { "⚠️" }
}

# 3) Análisis (sin dependencia dura de CrewAI: reglas deterministas del estado)
$recommendations = @()

if ($gaiaStatus -eq "offline") {
    $recommendations += "GaiaChain offline: ejecutar `POST /agents/system/sync-gaiachain` o `.\scripts\sync_with_gaiachain.ps1` segun runbook."
}
if ($pendingOps -gt 0) {
    $recommendations += "Cola local con operaciones pendientes: pending_operations=$pendingOps (priorizar sincronización)."
}
if ($diskUsagePct -ge $ThresholdDiskCritical) {
    $recommendations += "Disco con uso critico (>= $ThresholdDiskCritical%): revisar volúmenes/backups y limpieza con criterio."
} elseif ($diskUsagePct -ge $ThresholdDisk) {
    $recommendations += "Disco con uso alto (>= $ThresholdDisk%): planificar limpieza y verificar espacio."
}
if ($memoryUsagePct -ge $ThresholdMemoryCritical) {
    $recommendations += "Memoria con uso critico (>= $ThresholdMemoryCritical%): revisar carga y reinicios/limites de contenedores."
} elseif ($memoryUsagePct -ge $ThresholdMemory) {
    $recommendations += "Memoria con uso alto (>= $ThresholdMemory%): monitorear y reducir carga."
}
if ($criticalEventsCount -gt 0) {
    $top = @($criticalEvents) | Select-Object -First 3
    $recommendations += "Eventos con severidad detectada: count=$criticalEventsCount. Primeros: $($top | ConvertTo-Json -Compress)."
}

$metricsRec = 0
if (-not $metricsAvailable) {
    $recommendations += "Endpoint /agents/system/metrics no disponible en este despliegue; KPIs de uptime/CPU/latencia se derivan solo de health/status (parcial)."
    $metricsRec = 1
} else {
    if ($null -ne $uptimePct -and $uptimePct -lt 99.99) {
        $recommendations += "Uptime (aprox.) bajo: $uptimePct% (objetivo: 99.99%)."
    }
    if ($null -ne $cpuUsage -and $cpuUsage -gt $ThresholdCpu) {
        $recommendations += "CPU (aprox.) alto: $cpuUsage% (objetivo: < $ThresholdCpu%)."
    }
    if ($null -ne $networkLatency -and $networkLatency -gt $ThresholdNetworkLatency) {
        $recommendations += "Latencia de red (aprox.) alta: $networkLatency ms (objetivo: < $ThresholdNetworkLatency ms)."
    }
}

$aiAnalysis = @{
    Recommendations = $recommendations
    Mode = "rules-based"
    Source = "local_rules_fallback"
}

# 3.1) Sabionda IA (Mistral vía backend) — opcional
if ($UseSabiondaIA) {
    try {
        $prompt = @"
Eres Sabionda IA (Soberana) para CASTÚO-SYSTEM bajo marco ECSE.
Debes proponer recomendaciones priorizadas (CRITICA/ALTA/MEDIA/BAJA) para alinear:
Autonomía, Resiliencia, Seguridad, Mejora Continua.

Datos operativos (fuente: endpoints del sistema):
- system_status: $($s.system_status)
- gaiachain.status: $gaiaStatus
- pending_operations: $pendingOps
- uptime (aprox, si metrics disponibles): $uptimePct%
- cpu_usage (aprox, si metrics disponibles): $cpuUsage%
- disk_usage: $diskUsageStr (parsed: $diskUsagePct%)
- memory_usage: $memoryUsageStr (parsed: $memoryUsagePct%)
- network_latency (aprox, si metrics disponibles): $networkLatency ms
- critical_events_count: $criticalEventsCount
- critical_events (top 3): $(@($criticalEvents) | Select-Object -First 3 | ConvertTo-Json -Compress)
- umbrales trabajo: disk>=${ThresholdDisk}% (alto), disk>=${ThresholdDiskCritical}% (critico); memory>=${ThresholdMemory}% (alto), memory>=${ThresholdMemoryCritical}% (critico); network_latency<$ThresholdNetworkLatency ms (si aplica)

Devuelve ÚNICAMENTE JSON con el siguiente esquema:
{
  "pillar_status": {
     "Autonomy": "ok|warning|critical",
     "Resilience": "ok|warning|critical",
     "Security": "ok|warning|critical",
     "ContinuousImprovement": "ok|warning|critical"
  },
  "recommendations": [
     {"priority":"CRITICA|ALTA|MEDIA|BAJA","action":"string","expected_impact":"string"}
  ],
  "risks": [
     {"risk":"string","mitigation":"string"}
  ],
  "summary": "string"
}
"@

        $mistralPayload = @{
            prompt = $prompt
            model = $MistralModel
        }

        $aiRaw = Invoke-PostJsonOrNull -Uri "$BaseUrl/mistral/ask" -BodyObj $mistralPayload
        if ($null -ne $aiRaw) {
            $content = $null
            try {
                $content = $aiRaw.choices[0].message.content
            } catch { }

            # Fase de normalización: intentar JSON estricto primero; si falla, usar texto.
            $parsed = $null
            if ($null -ne $content) {
                try {
                    $parsed = $content | ConvertFrom-Json
                } catch { $parsed = $null }
            }

            if ($null -ne $parsed -and $null -ne $parsed.recommendations) {
                $recommendations = @()
                foreach ($r in @($parsed.recommendations)) {
                    $recommendations += ("[{0}] {1} (Impacto: {2})" -f $r.priority, $r.action, $r.expected_impact)
                }
                $aiAnalysis = @{
                    Recommendations = $recommendations
                    Mode = "mistral_backend"
                    Source = "backend_/mistral/ask"
                    Model = $MistralModel
                    Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
                    AIJson = $parsed
                }
                $reportDataRecsUpdated = $true
            } elseif ($null -ne $content) {
                # Fallback: extraer lineas con marcadores si el modelo responde en formato libre.
                $recommendations = @($content -split "`r?`n" | Where-Object { $_ -match "⚠️|✅|CRITICA|ALTA|MEDIA|BAJA" })
                $aiAnalysis = @{
                    Recommendations = $recommendations
                    Mode = "mistral_backend_text"
                    Source = "backend_/mistral/ask"
                    Model = $MistralModel
                    Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
                    ResponseText = $content
                }
            } else {
                _Write-Warn "Sabionda IA activada pero respuesta Mistral sin content; se mantiene fallback local."
            }
        } else {
            _Write-Warn "Sabionda IA: backend /mistral/ask devolvio null; se mantiene fallback local."
        }
    } catch {
        _Write-Warn "Sabionda IA falló; se mantiene fallback determinista. Error: $($_.Exception.Message)"
    }
}

# 4) Construir reportData
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$reportData = @{
    Timestamp = $timestamp
    BaseUrl = $BaseUrl
    SystemStatus = $s.system_status
    Components = $s.components
    CriticalEvents = $criticalEvents
    DiskUsagePct = $diskUsagePct
    MemoryUsagePct = $memoryUsagePct
    # Alias "humanos" para trazabilidad/reporting (si el despliegue no provee metrics, quedan en 0).
    Uptime = if ($null -ne $uptimePct) { $uptimePct } else { 0 }
    CPUUsage = if ($null -ne $cpuUsage) { $cpuUsage } else { 0 }
    MemoryUsage = if ($null -ne $memoryUsagePct) { $memoryUsagePct } else { 0 }
    DiskUsage = if ($null -ne $diskUsagePct) { $diskUsagePct } else { 0 }
    NetworkLatency = if ($null -ne $networkLatency) { $networkLatency } else { 0 }
    PendingOperations = $pendingOps
    GaiaChain = @{
        status = $gaiaStatus
        pending_operations = $pendingOps
        last_sync_attempt = $lastSync
    }
    UptimePct = $uptimePct
    ECSECompliance = $ecseCompliance
    AIAnalysis = $aiAnalysis
    Recommendations = $aiAnalysis.Recommendations
}

# 5) Exportar a múltiples formatos
$today = Get-Date -Format "yyyyMMdd"
$outputDir = Join-Path (Join-Path $PWD $OutputRoot) $today
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$reportJsonPath = Join-Path $outputDir "report.json"
$reportCsvPath = Join-Path $outputDir "report.csv"
$reportPdfPath = Join-Path $outputDir "report.pdf"
$witnessPath = Join-Path $outputDir "gaiachain_witness.json"

if ("JSON" -in $OutputFormat) {
    $reportData | ConvertTo-Json -Depth 30 | Out-File -FilePath $reportJsonPath -Encoding utf8
}

if ("CSV" -in $OutputFormat) {
    $csvRow = [PSCustomObject]@{
        Timestamp = $reportData.Timestamp
        SystemStatus = $reportData.SystemStatus
        GaiaChainStatus = $reportData.GaiaChain.status
        PendingOperations = $reportData.GaiaChain.pending_operations
        UptimePct = $reportData.UptimePct
        CPUUsage = $reportData.CPUUsage
        NetworkLatency = $reportData.NetworkLatency
        DiskUsagePct = $reportData.DiskUsagePct
        MemoryUsagePct = $reportData.MemoryUsagePct
        CriticalEventsCount = @($reportData.CriticalEvents).Count
        AutonomyOk = $autonomyOk
        ResilienceOk = $resilienceOk
        SecurityOk = $securityOk
        ContinuousImprovementOk = $continuousImprovementOk
    }
    $csvRow | Export-Csv -Path $reportCsvPath -NoTypeInformation -Encoding utf8
}

if ("PDF" -in $OutputFormat) {
    if (Get-Command -Name "New-PDF" -ErrorAction SilentlyContinue) {
        # Espera PSWritePDF; si no está, fallará y omitimos.
        try {
            $pdf = New-PDF -Path $reportPdfPath
            $pdf | Add-PDFPage | Out-Null
            $pdf = $pdf | Add-PDFText -Text ("Informe ECSE - " + (Get-Date -Format 'dd/MM/yyyy')) -FontSize 18
            $pdf = $pdf | Add-PDFText -Text ("Estado del sistema: " + $reportData.SystemStatus) -FontSize 12
            $pdf = $pdf | Add-PDFText -Text ("GaiaChain: " + $reportData.GaiaChain.status + " | pending=" + $reportData.GaiaChain.pending_operations) -FontSize 12
            $pdf = $pdf | Add-PDFText -Text ("Uptime: " + $reportData.UptimePct + "% | CPU: " + $reportData.CPUUsage + "% | Latencia: " + $reportData.NetworkLatency + " ms") -FontSize 12
            $pdf = $pdf | Add-PDFText -Text ("Disco: " + $reportData.DiskUsagePct + "% | Memoria: " + $reportData.MemoryUsagePct + "%") -FontSize 12
            $pdf = $pdf | Add-PDFText -Text ("Recomendaciones: " + (@($recommendations) -join " | ")) -FontSize 10
            $pdf | Close-PDF
        } catch {
            _Write-Warn "PDF solicitado pero falló PSWritePDF; se generaron JSON/CSV. Error: $($_.Exception.Message)"
        }
    } else {
        _Write-Warn "PDF solicitado pero no existe comando `New-PDF` (instala PSWritePDF). Se generaron JSON/CSV."
    }
}

# 6) Registro inmutable opcional (GaiaChain Witness)
$witnessResult = $null
if ($RegisterInGaiaChain) {
    # Consistente con el repositorio (GaiaChain Witness real).
    $gaiaChainBase = $env:GAIA_CHAIN_API_URL
    if ([string]::IsNullOrWhiteSpace($gaiaChainBase)) {
        $gaiaChainBase = "https://api.gaiachain.castuo-system.com"
    }
    $gaiaChainBase = $gaiaChainBase.TrimEnd("/")
    $witnessUrl = "$gaiaChainBase/api/v1/witness"

    # Hash del JSON del informe (evidencia exacta en fichero).
    if (-not (Test-Path $reportJsonPath)) {
        throw "RegisterInGaiaChain=true pero report.json no existe en $reportJsonPath"
    }
    $reportHash = (Get-FileHash -Path $reportJsonPath -Algorithm SHA256).Hash

    $payload = @{
        hash = $reportHash
        coop_id = $CoopId
        ipfs_cid = $null
    }

    $witnessResult = Invoke-PostJsonOrNull -Uri $witnessUrl -BodyObj $payload
    if ($null -eq $witnessResult) {
        _Write-Warn "GaiaChain witness no disponible o fallo HTTP; se guarda evidencia local igualmente."
        $witnessResult = @{
            ok = $false
            error = "witness_http_failed_or_unavailable"
            tx_hash = $reportHash
        }
    }

    $witnessOut = @{
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        WitnessUrl = $witnessUrl
        CoopId = $CoopId
        ReportHash = $reportHash
        WitnessResponse = $witnessResult
        Metadata = @{
            system_status = $reportData.SystemStatus
            uptime = $reportData.Uptime
            disk_usage_pct = $reportData.DiskUsagePct
            memory_usage_pct = $reportData.MemoryUsagePct
            cpu_usage = $reportData.CPUUsage
            network_latency = $reportData.NetworkLatency
            pending_operations = $reportData.PendingOperations
            critical_events_count = @($reportData.CriticalEvents).Count
            ai_used = [bool]$UseSabiondaIA
            ai_model = $MistralModel
            ecse_compliance = $ecseCompliance
        }
        ReportJsonPath = $reportJsonPath
    }
    $witnessOut | ConvertTo-Json -Depth 20 | Out-File -FilePath $witnessPath -Encoding utf8
}

# 7) Registrar evento en backend (opcional, para trazabilidad en SQLite)
if ($LogEventInBackend) {
    $payloadEvent = @{
        event_type = "ecse_report_generated"
        details = @{
            report_path = $reportJsonPath
            report_hash = (if (Test-Path $reportJsonPath) { (Get-FileHash -Path $reportJsonPath -Algorithm SHA256).Hash } else { $null })
            system_status = $reportData.SystemStatus
            gaiachain_status = $reportData.GaiaChain.status
            disk_usage_pct = $reportData.DiskUsagePct
            memory_usage_pct = $reportData.MemoryUsagePct
            critical_events_count = @($reportData.CriticalEvents).Count
            uptime = $reportData.Uptime
            cpu_usage = $reportData.CPUUsage
            network_latency = $reportData.NetworkLatency
            pending_operations = $reportData.PendingOperations
            ai_used = [bool]$UseSabiondaIA
            ai_model = $MistralModel
            recommendations_count = @($reportData.Recommendations).Count
        }
        severity = "info"
    }
    $null = Invoke-PostJsonOrNull -Uri "$BaseUrl/agents/system/log-event" -BodyObj $payloadEvent
}

_Write-Info "✅ Informe ECSE generado en $outputDir"
if ($RegisterInGaiaChain) {
    _Write-Info "   GaiaChain witness: $witnessPath"
}

