# Test-PEI001-RoboticsLab-Stub.ps1
# Castúo-System — PEI-001 JSON sintético → digest local → POST /api/robotics/lab/snapshot
# Requiere: stub en marcha (ver README robotics) y mismo token en cliente y servidor.

$ErrorActionPreference = "Stop"

# Mismo valor que CASTUO_ROBOTICS_LAB_BEARER_TOKEN del proceso uvicorn (no uses Get-Random en prod).
if (-not $env:CASTUO_ROBOTICS_LAB_BEARER_TOKEN) {
    $env:CASTUO_ROBOTICS_LAB_BEARER_TOKEN = "dev-castuo-lab-bearer"
    Write-Warning "Usando token por defecto. Exporta CASTUO_ROBOTICS_LAB_BEARER_TOKEN en prod."
}
$BackendUrl = if ($env:CASTUO_ROBOTICS_LAB_URL) { $env:CASTUO_ROBOTICS_LAB_URL.TrimEnd('/') } else { "http://127.0.0.1:8011" }
$BearerToken = $env:CASTUO_ROBOTICS_LAB_BEARER_TOKEN

function New-PEI001Report {
    param([string]$ParcelaId = "EX-CTAEX-001")
    $obj = [ordered]@{
        parcela_id          = $ParcelaId
        fecha               = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        operador            = "CTO-GJJB"
        tipo_intervencion   = "riego_precision"
        volumen_ml          = 1250
        sensores            = @(
            @{ nombre = "humedad_suelo"; valor = 42.5; unidad = "%" },
            @{ nombre = "ph"; valor = 6.2; unidad = "" }
        )
        compliance_sigpac   = $true
        digest_artefacto    = "sha256:placeholder_local"
    }
    return ($obj | ConvertTo-Json -Depth 10 -Compress)
}

function Get-Sha256Hex {
    param([string]$Text)
    $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return (-join ($hash | ForEach-Object { $_.ToString("x2") }))
}

function New-RoboticsSnapshotPayload {
    param([string]$PEIReportJson)
    $report = $PEIReportJson | ConvertFrom-Json
    $digest = Get-Sha256Hex -Text $PEIReportJson
    $payload = [ordered]@{
        parcel_id           = [string]$report.parcela_id
        timestamp           = (Get-Date).ToUniversalTime().ToString("o")
        intervention_type   = [string]$report.tipo_intervencion
        metrics_summary     = @{
            volumen_ml = $report.volumen_ml
            sensores   = $report.sensores
        }
        sigpac_compliant    = [bool]$report.compliance_sigpac
        pei001_digest       = $digest
        audit_event         = "PEI001_REGISTERED"
    }
    return ($payload | ConvertTo-Json -Depth 10 -Compress)
}

function Invoke-RoboticsLabSnapshot {
    param([string]$PayloadJson)
    $headers = @{
        "Authorization" = "Bearer $BearerToken"
        "Content-Type"  = "application/json; charset=utf-8"
    }
    try {
        $response = Invoke-RestMethod -Uri "$BackendUrl/api/robotics/lab/snapshot" -Method Post -Headers $headers -Body $PayloadJson
        $tx = $response.tx_id
        if ($null -eq $tx -or $tx -eq "") { $tx = "stub-null" }
        Write-Host "OK snapshot: tx_id=$tx gaia_chain_digest=$($response.gaia_chain_digest)" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "Fallo HTTP: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) { Write-Host "Body: $($_.ErrorDetails.Message)" -ForegroundColor Red }
        throw
    }
}

Write-Host "Robotics Lab Stub: $BackendUrl" -ForegroundColor Cyan
$pei001 = New-PEI001Report -ParcelaId "EX-CTAEX-001"
Write-Host "PEI-001 (sintético, comprimido): $pei001" -ForegroundColor Yellow

$snapshot = New-RoboticsSnapshotPayload -PEIReportJson $pei001
Write-Host "POST body: $snapshot" -ForegroundColor Yellow

$null = Invoke-RoboticsLabSnapshot -PayloadJson $snapshot
Write-Host "Flujo: PEI-001 JSON -> digest local -> stub (digest canónico del POST en respuesta)." -ForegroundColor Green

# Neuromórfico lab (mismo Bearer)
$neuroBody = @{ humedad = 42.5; ph = 6.2; ec = 1.8; luz_umol = 0.0 } | ConvertTo-Json -Compress
try {
    $neuro = Invoke-RestMethod -Uri "$BackendUrl/api/robotics/lab/neuromorphic/hydroponics/infer" -Method Post -Headers @{
        "Authorization" = "Bearer $BearerToken"
        "Content-Type"  = "application/json; charset=utf-8"
    } -Body $neuroBody
    Write-Host "OK neuromorphic: riego_ml=$($neuro.riego_ml) power_uW=$($neuro.power_uW)" -ForegroundColor Green
}
catch {
    Write-Warning "Infer neuromórfica no disponible: $($_.Exception.Message)"
}

# Informe real (sin geo/PII):
#   $raw = Get-Content -Path "C:\ruta\informe_pei001.json" -Raw -Encoding UTF8
#   $snapshot = New-RoboticsSnapshotPayload -PEIReportJson $raw
#   Invoke-RoboticsLabSnapshot -PayloadJson $snapshot
