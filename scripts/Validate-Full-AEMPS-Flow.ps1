# scripts/Validate-Full-AEMPS-Flow.ps1
#
# Orquesta el flujo:
# 1) Generar certificado de prueba AEMPS (repo-verificable)
# 2) Ejecutar auditoria detallada
# 3) (Opcional) Probar webhook en staging
#
[CmdletBinding()]
param(
    [string]$TrialId = "CT-2026-001",
    [string]$BackendUrl = "http://localhost:8001",
    [string]$Protocol = "AEMPS-2025/42",
    [string]$Institution = "CTAEX",
    [int]$Patients = 45,
    [string]$Strain = "Cannabis sativa",
    [double]$ThcPercentage = 0.15,
    [double]$CbdPercentage = 0.05,
    [switch]$RunStagingWebhookProbe
)

$ErrorActionPreference = "Stop"

$genScript = Join-Path $PSScriptRoot "Generate-AEMPS-TrialCertificate.ps1"
$auditScript = Join-Path $PSScriptRoot "Audit-CannabisTrial-Detailed.ps1"

if (-not (Test-Path $genScript)) { throw "Missing: $genScript" }
if (-not (Test-Path $auditScript)) { throw "Missing: $auditScript" }

Write-Host "Paso 1: Generar certificado de prueba..." -ForegroundColor Cyan
& $genScript `
    -TrialId $TrialId `
    -Strain $Strain `
    -Protocol $Protocol `
    -Patients $Patients `
    -Institution $Institution `
    -BackendUrl $BackendUrl `
    -ThcPercentage $ThcPercentage `
    -CbdPercentage $CbdPercentage

# 1b) Verificacion publica soberana (alias /api/...)
$certJsonPath = Join-Path "certificates" ("aemps\" + $TrialId + "\certificate.json")
if (Test-Path $certJsonPath) {
    try {
        $certObj = Get-Content -Path $certJsonPath -Raw | ConvertFrom-Json
        $txHash = $certObj.sovereign_certificate.gaiachain_tx
        if ($txHash) {
            $verifyScript = Join-Path $PSScriptRoot "Verify-PublicCertificate.ps1"
            if (Test-Path $verifyScript) {
                Write-Host "Paso 1b: Verificar tx soberano con Verify-PublicCertificate.ps1 ..." -ForegroundColor Cyan
                & $verifyScript -TxHash $txHash -BackendUrl $BackendUrl
            }
        }
    } catch {
        Write-Warning "No se pudo ejecutar verificacion publica: $($_.Exception.Message)"
    }
}

Write-Host "Paso 2: Ejecutar auditoria detallada..." -ForegroundColor Cyan
& $auditScript `
    -TrialId $TrialId `
    -BackendUrl $BackendUrl

if ($RunStagingWebhookProbe) {
    Write-Host "Paso 3: Probar webhook en staging..." -ForegroundColor Cyan
    $stagingScript = Join-Path $PSScriptRoot "Setup-AEMPS-Webhook-Staging.sh"
    if (Test-Path $stagingScript) {
        # Si estas en Windows, requiere bash instalado.
        bash $stagingScript
    } else {
        Write-Warning "No existe $stagingScript"
    }
}

Write-Host "Flujo completo finalizado." -ForegroundColor Green

