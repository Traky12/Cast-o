<#
.SYNOPSIS
    Verifica publicamente certificados soberanos (GaiaChain TXID) usando el endpoint del backend.

.DESCRIPTION
    Llama a:
      - GET {BackendUrl}/api/certificates/verify/{TxHash}

    En el repo, ese endpoint actua como alias:
    - Si {TxHash} parece un TXID GaiaChain, se proxy-a la verificacion soberana existente.
    - Si no lo parece, se mantiene la verificacion de certificados CTAEX (compliance).

    Si existe `pdf_url` o `pdf_certificate_url` (dependiente del despliegue), intenta descargarlo.

.NOTES
    - Para evitar dependencia externa, este script solo usa el backend. La verificcion "doble" con GaiaChain
      se deja como futura extension (por validar en tu entorno).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$TxHash,

    [string]$BackendUrl = "http://localhost:8001",

    [string]$OutputDir = "certificates",

    [switch]$DownloadPdfIfAvailable
)

$ErrorActionPreference = "Stop"

function Try-DownloadFile {
    param(
        [Parameter(Mandatory=$true)][string]$Url,
        [Parameter(Mandatory=$true)][string]$Path
    )
    try {
        Invoke-WebRequest -Uri $Url -OutFile $Path -UseBasicParsing
        return $true
    } catch {
        Write-Warning ("No se pudo descargar PDF desde: " + $Url + " | " + $_.Exception.Message)
        return $false
    }
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$uri = ($BackendUrl.TrimEnd("/")) + "/api/certificates/verify/" + $TxHash

$verification = Invoke-RestMethod -Uri $uri -Method Get -ErrorAction Stop

Write-Host "🔍 Resultado de verificacion:" -ForegroundColor Green
Write-Host "   - Status: $($verification.status)" -ForegroundColor Cyan

if ($null -ne $verification.certificate) {
    Write-Host "   - TXID: $($verification.certificate.tx_id)" -ForegroundColor Cyan
    Write-Host "   - Certificate Hash: $($verification.certificate.certificate_hash)" -ForegroundColor Cyan
    if ($null -ne $verification.certificate.timestamp) {
        Write-Host "   - Timestamp: $($verification.certificate.timestamp)" -ForegroundColor Cyan
    }
}

if ($null -ne $verification.verification_url) {
    Write-Host "   - Verificacion URL: $($verification.verification_url)" -ForegroundColor Magenta
}

$pdfUrl = $null
if ($verification.PSObject.Properties.Name -contains "pdf_certificate_url") {
    $pdfUrl = $verification.pdf_certificate_url
}
if (-not $pdfUrl -and $verification.PSObject.Properties.Name -contains "pdf_url") {
    $pdfUrl = $verification.pdf_url
}

if ($DownloadPdfIfAvailable -and $pdfUrl -and ($pdfUrl -match "^https?://")) {
    $outPath = Join-Path $OutputDir ($TxHash + ".pdf")
    $ok = Try-DownloadFile -Url $pdfUrl -Path $outPath
    if ($ok) {
        Write-Host "   - PDF descargado: $outPath" -ForegroundColor Green
    }
}

return $verification

