# scripts/Generate-AEMPS-TrialCertificate.ps1
#
# Genera un "certificado de prueba" verificable con trazabilidad del repo:
#   - Solicitud AEMPS (pendiente en este repo): POST /cannabis/certify_aemps
#   - Certificado soberano: POST /agents/certificates/generate
#   - Verificacion soberana: GET  /agents/certificates/verify/{tx_hash} (alias publico /api/...)
#   - Testigo GaiaChain + evidencia local (contrato del repo): scripts/Register-SecurityEvent.ps1
#
# Nota de soberania: la verificacion publica del certificado soberano depende del tx_hash.

[CmdletBinding()]
param(
    [string]$TrialId = "CT-2026-001",
    [string]$Strain = "Cannabis sativa",
    [string]$Protocol = "AEMPS-2025/42",
    [int]$Patients = 45,
    [string]$Institution = "CTAEX",
    [string]$BackendUrl = "http://localhost:8001",
    [double]$ThcPercentage = 0.15,
    [double]$CbdPercentage = 0.05,
    [int]$CoopId = 1,
    [switch]$LogEventInBackend = $true,
    [string]$OutputRoot = "certificates"
)

$ErrorActionPreference = "Stop"

function Get-Sha256HexFromString {
    param([Parameter(Mandatory=$true)][string]$Text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hashBytes = $sha.ComputeHash($bytes)
    return -join ($hashBytes | ForEach-Object { $_.ToString("x2") })
}

function Ensure-Dir {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

Write-Host "Generando certificado de prueba AEMPS para $TrialId" -ForegroundColor Cyan

# 1) Datos del ensayo (sin datos personales) para minimizar riesgo GDPR.
$trialData = @{
    trial_id = $TrialId
    strain = $Strain
    protocol = $Protocol
    institution = $Institution
    patients = $Patients
    study_phase = "Phase II"
    study_type = "Randomized, Double-Blind, Placebo-Controlled"
    compliance = @{
        AEMPS = @{
            regulation = "RD 903/2025"
            status = "pending"
            evidence = "Certificate sovereign + trazabilidad"
        }
        GDPR = @{
            article = "Art. 25"
            status = "pending"
            evidence = "Datos anonimizados/anon data en este repo (por validar)"
        }
        ISO_17025 = @{
            clause = "5.10"
            status = "pending"
            evidence = "Por validar segun alcance"
        }
        UNE_66181 = @{
            standard = "UNE 66181:2022"
            status = "pending"
            evidence = "Por validar segun alcance"
        }
    }
    metrics = @{
        adverse_events = 0
        completion_rate = 98.5
        statistical_significance = 0.001
        patient_compliance = 95.2
    }
    documents = @{
        protocol = "PROTOCOL-PENDING"
        icf = "ICF-PENDING"
        sap = "SAP-PENDING"
    }
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

$trialCanonicalJson = ($trialData | ConvertTo-Json -Depth 30 -Compress)
$trialHash = Get-Sha256HexFromString -Text $trialCanonicalJson

# 2) Solicitud AEMPS (endpoint real del repo)
$aempsUrl = ($BackendUrl.TrimEnd("/")) + "/cannabis/certify_aemps"
$aempsBody = @{
    batch_id = $TrialId
    strain_id = $Strain
    thc_percentage = [double]$ThcPercentage
    cbd_percentage = [double]$CbdPercentage
    lab_results = @{
        protocol = $Protocol
        patients = $Patients
        thc = [double]$ThcPercentage
        cbd = [double]$CbdPercentage
        institution = $Institution
    }
}

Write-Host "Llamando AEMPS (pending en este repo): POST /cannabis/certify_aemps" -ForegroundColor Yellow
$aempsResp = Invoke-RestMethod -Uri $aempsUrl -Method Post -Headers @{"Content-Type"="application/json"} -Body ($aempsBody | ConvertTo-Json -Depth 25 -Compress)

Write-Host "AEMPS certification_id=$($aempsResp.certification_id) status=$($aempsResp.status)" -ForegroundColor Green

# 3) Certificado soberano (GaiaChain final_certificate)
$certGenUrl = ($BackendUrl.TrimEnd("/")) + "/agents/certificates/generate"
$certGenBody = @{
    lote_id = $TrialId
    cultivo = "cannabis_medicinal"
}

Write-Host "Generando certificado soberano: POST /agents/certificates/generate" -ForegroundColor Yellow
$certGenResp = Invoke-RestMethod -Uri $certGenUrl -Method Post -Headers @{"Content-Type"="application/json"} -Body ($certGenBody | ConvertTo-Json -Depth 10 -Compress)

$gaiachainTx = $certGenResp.gaiachain_tx
Write-Host "Sovereign gaiachain_tx=$gaiachainTx" -ForegroundColor Green

# 4) Verificacion soberana
$verifyUrl = ($BackendUrl.TrimEnd("/")) + "/agents/certificates/verify/$gaiachainTx"
$verifyResp = Invoke-RestMethod -Uri $verifyUrl -Method Get

$verificationUrl = $verifyResp.verification_url
Write-Host "verification_url=$verificationUrl" -ForegroundColor Magenta

# 5) Witness + evidencia local (contrato del repo)
$registerScript = Join-Path $PSScriptRoot "Register-SecurityEvent.ps1"
$witnessEventType = "aemps_trial_proof"

$eventData = @{
    trial_id = $TrialId
    protocol = $Protocol
    institution = $Institution
    patients = $Patients
    trial_hash = $trialHash
    aemps_certification_id = $aempsResp.certification_id
    gaiachain_tx = $gaiachainTx
    verification_url = $verificationUrl
}

$witnessTxid = "witness-not-sent"
if (Test-Path $registerScript) {
    Write-Host "Registrando witness + evidencia local con Register-SecurityEvent.ps1" -ForegroundColor Yellow
    $witnessTxid = & $registerScript `
        -EventType $witnessEventType `
        -EventData $eventData `
        -CoopId $CoopId `
        -BackendUrl $BackendUrl `
        -Severity "info" `
        -LogEventInBackend:$LogEventInBackend
}

# 6) Artefactos
$outDir = Join-Path $OutputRoot ("aemps\" + $TrialId)
Ensure-Dir -Path $outDir

$certificate = @{
    type = "aemps_trial_proof"
    trial_id = $TrialId
    trial_hash = $trialHash
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    aemps = @{
        status = $aempsResp.status
        certification_id = $aempsResp.certification_id
        estimated_completion = $aempsResp.estimated_completion
    }
    sovereign_certificate = @{
        lote_id = $TrialId
        gaiachain_tx = $gaiachainTx
        verification_url = $verificationUrl
        certificate_hash = $certGenResp.certificate_hash
    }
    witness = @{
        event_type = $witnessEventType
        tx_id = $witnessTxid
        witness_url = ("https://gaiachain.castuo-system.com/tx/" + $witnessTxid)
    }
    inputs = @{
        strain = $Strain
        protocol = $Protocol
        institution = $Institution
        patients = $Patients
        thc_percentage = [double]$ThcPercentage
        cbd_percentage = [double]$CbdPercentage
    }
}

$certificateJsonPath = Join-Path $outDir "certificate.json"
$certificate | ConvertTo-Json -Depth 30 | Out-File -FilePath $certificateJsonPath -Encoding utf8

$certificateMdPath = Join-Path $outDir ("CERTIFICADO-" + $TrialId + ".md")
$certificateMd = @"
# CERTIFICADO DE PRUEBA (AEMPS) - $TrialId

## Resumen verificable
- AEMPS certification_id: $($certificate.aemps.certification_id)
- AEMPS status: $($certificate.aemps.status)
- Certificado soberano gaiachain_tx: $gaiachainTx
- Verificacion soberana: $verificationUrl
- Witness evidencia local (GaiaChain witness tx_id): $witnessTxid

## Ensayo
- Strain: $Strain
- Protocol: $Protocol
- Institution: $Institution
- Patients: $Patients
- THC%: $ThcPercentage
- CBD%: $CbdPercentage

## Hash de integridad (trial_data canonico)
- trial_hash (SHA256 de JSON canonico): $trialHash

## Nota legal
Este certificado es una prueba generada por el repo. La validez final depende de la integridad del certificado soberano y la verificacion por tx_hash.
"@
$certificateMd | Out-File -FilePath $certificateMdPath -Encoding utf8

# 6b) Estructura de documentos (placeholders, para que el flujo quede completo en el repo)
$docsDir = Join-Path $outDir "documents"
Ensure-Dir -Path $docsDir

@(
    @{ name = "protocol.pdf"; content = "PLACEHOLDER: protocol pdf generado en despliegue (por validar)." },
    @{ name = "icf.pdf"; content = "PLACEHOLDER: informed consent pdf generado en despliegue (por validar)." },
    @{ name = "sap.pdf"; content = "PLACEHOLDER: sap pdf generado en despliegue (por validar)." }
) | ForEach-Object {
    $p = Join-Path $docsDir $_.name
    $_.content | Out-File -FilePath $p -Encoding utf8
}

Write-Host "Certificado generado: $certificateJsonPath" -ForegroundColor Green
Write-Host "Documento: $certificateMdPath" -ForegroundColor Green

Write-Host "Fin." -ForegroundColor Cyan

