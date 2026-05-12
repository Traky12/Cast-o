# -*- coding: utf-8 -*-
<#
.SYNOPSIS
  Auditoria end-to-end para cannabis medicinal/AEMPS, usando SOLO endpoints reales del repo:
    - POST /cannabis/certify_aemps
    - POST /agents/certificates/generate
    - GET  /agents/certificates/verify/{tx_hash}
    - (opcional) Register-SecurityEvent.ps1 para witness GaiaChain + evidencia local

.DESCRIPTION
  - La parte "AEMPS" en este repo devuelve status "pending" (integracion externa por validar).
  - La evidencia soberana y su verificacion se realiza con el certificador del repo y el alias publico de verificacion.
#>

[CmdletBinding()]
param(
    [string]$TrialId = "CT-2026-001",
    [string]$StrainId = "Cannabis sativa",
    [double]$ThcPercentage = 0.15,
    [double]$CbdPercentage = 0.05,
    [string]$Protocol = "AEMPS-2025/42",
    [int]$Patients = 45,
    [string]$BackendUrl = "http://localhost:8001",
    [int]$CoopId = 1,
    [switch]$LogEventInBackend = $true
)

$ErrorActionPreference = "Stop"

Write-Host "Iniciando auditoria para ensayo/lote: $TrialId" -ForegroundColor Cyan

# 1) Solicitud de certificacion AEMPS (pending en este repo)
$aempsBody = @{
    batch_id = $TrialId
    strain_id = $StrainId
    thc_percentage = [double]$ThcPercentage
    cbd_percentage = [double]$CbdPercentage
    lab_results = @{
        protocol = $Protocol
        patients = $Patients
        thc = [double]$ThcPercentage
        cbd = [double]$CbdPercentage
    }
}

$aempsUrl = ($BackendUrl.TrimEnd("/")) + "/cannabis/certify_aemps"
$aempsResp = Invoke-RestMethod -Uri $aempsUrl -Method Post -Headers @{"Content-Type"="application/json"} -Body ($aempsBody | ConvertTo-Json -Depth 20 -Compress)

Write-Host "AEMPS certification_id: $($aempsResp.certification_id) (status=$($aempsResp.status))" -ForegroundColor Green

# 2) Generacion de certificado soberano
$certGenBody = @{
    lote_id = $TrialId
    cultivo = "cannabis_medicinal"
}
$certGenUrl = ($BackendUrl.TrimEnd("/")) + "/agents/certificates/generate"
$certGenResp = Invoke-RestMethod -Uri $certGenUrl -Method Post -Headers @{"Content-Type"="application/json"} -Body ($certGenBody | ConvertTo-Json -Depth 20 -Compress)

$txHash = $certGenResp.gaiachain_tx
Write-Host "Certificado soberano TX: $txHash" -ForegroundColor Green

# 3) Verificacion del certificado
$verifyUrl = ($BackendUrl.TrimEnd("/")) + "/agents/certificates/verify/$txHash"
$verifyResp = Invoke-RestMethod -Uri $verifyUrl -Method Get

$normativas = @()
try {
    if ($verifyResp.data -and $verifyResp.data.certificate_data -and $verifyResp.data.certificate_data.metadata -and $verifyResp.data.certificate_data.metadata.normativas) {
        $normativas = @($verifyResp.data.certificate_data.metadata.normativas)
    }
} catch {
    $normativas = @()
}

$hasRd903 = ($normativas | Where-Object { $_ -like "*RD 903/2025*" -or $_ -like "*RD_903/2025*" }).Count -gt 0
$hasGdpr = ($normativas | Where-Object { $_ -like "*GDPR*" }).Count -gt 0
$hasIso17025 = ($normativas | Where-Object { $_ -like "*ISO 17025*" -or $_ -like "*ISO_17025*" }).Count -gt 0

$compliance = @{
    AEMPS = $hasRd903
    GDPR = $hasGdpr
    ISO_17025 = $hasIso17025
}

$trueCount = (@($compliance.Values) | Where-Object { $_ -eq $true }).Count
$complianceScore = 0.0
if ($compliance.Count -gt 0) {
    $complianceScore = [double]($trueCount) / [double]($compliance.Count)
}

$status = if ($complianceScore -ge 0.66) { "compliant" } else { "non_compliant" }

$findings = @()
if (-not $hasRd903) {
    $findings += @{
        standard = "AEMPS"
        issue = "Falta referencia RD 903/2025 en normativas del certificado."
        severity = "critical"
        recommendation = "Revisar el flujo de certificacion soberana y sus normativas."
    }
}
if (-not $hasGdpr) {
    $findings += @{
        standard = "GDPR"
        issue = "Falta referencia GDPR en normativas del certificado."
        severity = "high"
        recommendation = "Aplicar pseudonimizacion/cifrado y documentar Art. 25."
    }
}
if (-not $hasIso17025) {
    $findings += @{
        standard = "ISO_17025"
        issue = "ISO 17025 no aparece en normativas del certificado (por validar segun alcance actual)."
        severity = "medium"
        recommendation = "Si se requiere ISO 17025, extender el generador del certificado para incluirla."
    }
}

# 4) Auditoria report
$auditReport = @{
    trial_id = $TrialId
    timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    protocol = $Protocol
    patients = $Patients
    aemps = @{
        status = $aempsResp.status
        certification_id = $aempsResp.certification_id
        estimated_completion = $aempsResp.estimated_completion
    }
    certificate = @{
        gaiachain_tx = $txHash
        certificate_hash = $certGenResp.certificate_hash
        verification_url = $verifyResp.verification_url
    }
    compliance = $compliance
    compliance_score = $complianceScore
    status = $status
    findings = $findings
    evidence = @{
        certificate_metadata = $verifyResp.data.certificate_data.metadata
        legal_seals = $verifyResp.data.legal_seals
    }
}

# 5) Witness + evidencia inmutable (GaiaChain) con el script del repo
$registerScript = Join-Path $PSScriptRoot "Register-SecurityEvent.ps1"
$witnessEventType = "cannabis_trial_audited"
$eventData = @{
    trial_id = $TrialId
    protocol = $Protocol
    aemps_certification_id = $aempsResp.certification_id
    gaiachain_tx = $txHash
    compliance_score = $complianceScore
    status = $status
    findings = $findings
}

if (Test-Path $registerScript) {
    & $registerScript `
        -EventType $witnessEventType `
        -EventData $eventData `
        -CoopId $CoopId `
        -BackendUrl $BackendUrl `
        -Severity "info" `
        -LogEventInBackend:$LogEventInBackend
}

# 6) Guardar resultados
$outputDir = Join-Path "audits\cannabis" $TrialId
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$auditPath = Join-Path $outputDir "audit_report.json"
$auditReport | ConvertTo-Json -Depth 25 | Out-File -FilePath $auditPath -Encoding utf8

Write-Host "Auditoria completada. compliance_score=$complianceScore status=$status" -ForegroundColor Green
Write-Host "Reporte: $auditPath" -ForegroundColor Cyan

