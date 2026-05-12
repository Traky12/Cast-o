# scripts/Audit-CannabisTrial-Detailed.ps1
#
# Auditoria detallada (repo-verificable) basada en evidencia disponible:
#   - Verificacion soberana del certificado via GET /agents/certificates/verify/{tx_hash}
#   - Cumplimiento (AEMPS/GDPR/ISO 17025/UNE 66181) derivado de normativas del certificado.
#   - Protocolo/ICF/Data/Statistics: por defecto "por validar" (se requiere evidencia externa).
#
# Soberania: la evidencia inmutable se notaria con scripts/Register-SecurityEvent.ps1.

[CmdletBinding()]
param(
    [string]$TrialId = "CT-2026-001",
    [string]$BackendUrl = "http://localhost:8001",
    [string]$TxHash = "",
    [string]$ProtocolEvidence = "",
    [string]$ICFEvidence = "",
    [string]$DataEvidence = "",
    [string]$StatisticsEvidence = "",
    [int]$CoopId = 1,
    [switch]$LogEventInBackend = $true
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

Write-Host "Auditoria detallada para: $TrialId" -ForegroundColor Cyan

# 1) Obtener tx_hash soberano
if ([string]::IsNullOrWhiteSpace($TxHash)) {
    $listUrl = ($BackendUrl.TrimEnd("/")) + "/agents/system/local-certificates?limit=500"
    $listResp = Invoke-RestMethod -Uri $listUrl -Method Get
    $cert = $null
    if ($listResp -and $listResp.certificates) {
        $cert = ($listResp.certificates | Where-Object { $_.lote_id -eq $TrialId } | Select-Object -First 1)
    }
    if ($null -eq $cert -or [string]::IsNullOrWhiteSpace($cert.gaiachain_tx)) {
        throw "No se encontro un certificado local para lote_id=$TrialId. Genera primero el certificado soberano."
    }
    $TxHash = [string]$cert.gaiachain_tx
}

Write-Host "Usando tx_hash: $TxHash" -ForegroundColor Green

# 2) Verificar certificado
$verifyUrl = ($BackendUrl.TrimEnd("/")) + "/agents/certificates/verify/" + $TxHash
$verifyResp = Invoke-RestMethod -Uri $verifyUrl -Method Get

$metadata = $null
$normativas = @()
try {
    $metadata = $verifyResp.data.certificate_data.metadata
    if ($metadata -and $metadata.normativas) {
        $normativas = @($metadata.normativas)
    }
} catch {
    $normativas = @()
}

Write-Host "Normativas en certificado: $($normativas.Count)" -ForegroundColor Cyan

$normStr = ($normativas | ForEach-Object { [string]$_ }) -join ";"
$aempsOk = ($normStr -match "RD 903/2025") -or ($normStr -match "RD_903/2025")
$gdprOk = ($normStr -match "GDPR")
$isoOk = ($normStr -match "ISO 17025") -or ($normStr -match "ISO_17025")
$uneOk = ($normStr -match "UNE 66181") -or ($normStr -match "UNE_66181")

# 3) Checklist y scoring
$auditChecklist = @{
    protocol = @{
        weight = 0.30
        requirements = @(
            "Objetivos claramente definidos",
            "Criterios de inclusion/exclusion especificos",
            "Dosis y administracion detalladas",
            "Plan de seguridad definido",
            "Cumplimiento con RD 903/2025 (derivado/consistencia)"
        )
    }
    icf = @{
        weight = 0.25
        requirements = @(
            "Lenguaje claro y comprensible",
            "Riesgos y beneficios explicados",
            "Derechos del paciente detallados",
            "Firma del paciente y fecha (por validar)",
            "Cumplimiento con GDPR Art. 25"
        )
    }
    data = @{
        weight = 0.20
        requirements = @(
            "Datos anonimizados segun GDPR (evidencia requerida)",
            "Trazabilidad completa de muestras (por validar)",
            "Almacenamiento seguro (por validar)",
            "Backup regular (por validar)",
            "Acceso restringido (por validar)"
        )
    }
    statistics = @{
        weight = 0.15
        requirements = @(
            "Metodos estadisticos apropiados",
            "Tamanho de muestra justificado (por validar)",
            "Analisis de subgrupos (por validar)",
            "Manejo de datos faltantes (por validar)",
            "Cumplimiento con ISO 17025"
        )
    }
    compliance = @{
        weight = 0.10
        requirements = @(
            "Cumplimiento con AEMPS RD 903/2025",
            "Cumplimiento con GDPR",
            "Cumplimiento con ISO 17025",
            "Cumplimiento con UNE 66181",
            "Registros de auditoria completos"
        )
    }
}

function Test-ComplianceByEvidence {
    param(
        [string]$Section,
        [string]$Requirement,
        [bool]$AEMPSOk,
        [bool]$GDPROk,
        [bool]$ISOOk,
        [bool]$UNEOk,
        [string]$ProtocolEvidence,
        [string]$ICFEvidence,
        [string]$DataEvidence,
        [string]$StatisticsEvidence
    )

    $ev = ""
    $hasAny = $false

    switch ($Section) {
        "protocol" {
            $hasAny = -not [string]::IsNullOrWhiteSpace($ProtocolEvidence)
            if ($Requirement -match "RD 903/2025") {
                $hasAny = $AEMPSOk
                $ev = "Derivado de normativas del certificado"
            } else {
                $ev = "Evidencia externa: ProtocolEvidence"
            }
        }
        "icf" {
            if ($Requirement -match "GDPR") {
                $hasAny = $GDPROk
                $ev = "Derivado de normativas del certificado"
            } else {
                $hasAny = -not [string]::IsNullOrWhiteSpace($ICFEvidence)
                $ev = "Evidencia externa: ICFEvidence"
            }
        }
        "data" {
            if ($Requirement -match "anonimizados") {
                $hasAny = -not [string]::IsNullOrWhiteSpace($DataEvidence)
                $ev = "Evidencia externa: DataEvidence"
            } else {
                $hasAny = -not [string]::IsNullOrWhiteSpace($DataEvidence)
                $ev = "Evidencia externa: DataEvidence (o por validar)"
            }
        }
        "statistics" {
            if ($Requirement -match "ISO 17025") {
                $hasAny = $ISOOk
                $ev = "Derivado de normativas del certificado"
            } else {
                $hasAny = -not [string]::IsNullOrWhiteSpace($StatisticsEvidence)
                $ev = "Evidencia externa: StatisticsEvidence"
            }
        }
        "compliance" {
            if ($Requirement -match "AEMPS") { $hasAny = $AEMPSOk }
            elseif ($Requirement -match "GDPR") { $hasAny = $GDPROk }
            elseif ($Requirement -match "ISO 17025") { $hasAny = $ISOOk }
            elseif ($Requirement -match "UNE 66181") { $hasAny = $UNEOk }
            else { $hasAny = $true; $ev = "Por definicion (auditoria registrada)" }
            if (-not $ev) { $ev = "Derivado de normativas del certificado o registro de auditoria" }
        }
    }

    return @{
        compliant = [bool]$hasAny
        evidence = $ev
    }
}

$auditResults = @{}
$totalScore = 0.0
$auditChecklistKeys = @($auditChecklist.Keys)

foreach ($section in $auditChecklistKeys) {
    $sectionWeight = [double]$auditChecklist[$section].weight
    $requirements = @($auditChecklist[$section].requirements)

    $sectionCompliantCount = 0
    $sectionResults = @()

    foreach ($req in $requirements) {
        $check = Test-ComplianceByEvidence -Section $section -Requirement $req -AEMPSOk $aempsOk -GDPROk $gdprOk -ISOOk $isoOk -UNEOk $uneOk `
            -ProtocolEvidence $ProtocolEvidence -ICFEvidence $ICFEvidence -DataEvidence $DataEvidence -StatisticsEvidence $StatisticsEvidence

        if ($check.compliant) { $sectionCompliantCount += 1 }

        $sectionResults += @{
            requirement = $req
            compliant = $check.compliant
            evidence = $check.evidence
        }
    }

    $sectionScorePct = 0.0
    if ($requirements.Count -gt 0) {
        $sectionScorePct = ([double]$sectionCompliantCount / [double]$requirements.Count) * 100.0
    }

    $totalScore += $sectionScorePct * $sectionWeight

    $auditResults[$section] = @{
        score = [math]::Round($sectionScorePct, 2)
        details = $sectionResults
    }
}

$totalScorePct = [math]::Round($totalScore * 100.0, 2) / 100.0
$status = if ($totalScorePct -ge 90) { "compliant" } else { "non_compliant" }

Write-Host "Score total: $totalScorePct% status=$status" -ForegroundColor Green

# 4) Report object
$auditReport = @{
    trial_id = $TrialId
    timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    overall_score = $totalScorePct
    status = $status
    sections = $auditResults
    compliance = @{
        AEMPS = $aempsOk
        GDPR = $gdprOk
        ISO_17025 = $isoOk
        UNE_66181 = $uneOk
    }
    tx_hash = $TxHash
}

# 5) Hash + witness (repo contract)
$auditCanonical = ($auditReport | ConvertTo-Json -Depth 30 -Compress)
$auditHash = Get-Sha256HexFromString -Text $auditCanonical

$witnessEventType = "detailed_cannabis_trial_audited"
$eventData = @{
    trial_id = $TrialId
    tx_hash = $TxHash
    overall_score = $auditReport.overall_score
    status = $status
    audit_hash = $auditHash
    compliance = $auditReport.compliance
}

$witnessTxid = "witness-not-sent"
$registerScript = Join-Path $PSScriptRoot "Register-SecurityEvent.ps1"
if (Test-Path $registerScript) {
    $witnessTxid = & $registerScript `
        -EventType $witnessEventType `
        -EventData $eventData `
        -CoopId $CoopId `
        -BackendUrl $BackendUrl `
        -Severity "info" `
        -LogEventInBackend:$LogEventInBackend
}

# 6) Guardar resultados
$outputDir = Join-Path ("audits\detailed\$TrialId")
Ensure-Dir -Path $outputDir

$auditReportPath = Join-Path $outputDir "audit_report.json"
$auditMdPath = Join-Path $outputDir ("AUDITORIA-DETALLADA-" + $TrialId + ".md")

$auditReport | ConvertTo-Json -Depth 30 | Out-File -FilePath $auditReportPath -Encoding utf8

$auditMd = @"
# AUDITORIA DETALLADA (AEMPS Trial) - $TrialId

## Verificacion soberana
- tx_hash: $TxHash
- verificacion_url: $($verifyResp.verification_url)

## Compliance derivado de normativas del certificado soberano
- AEMPS: $aempsOk
- GDPR: $gdprOk
- ISO_17025: $isoOk
- UNE_66181: $uneOk

## Resultado
- overall_score: $($auditReport.overall_score)%
- status: $status

## Witness (repo contrato)
- event_type: $witnessEventType
- witness_tx_id: $witnessTxid
- audit_hash: $auditHash

## Nota
Las evidencias de protocolo/ICF/data/statistics se marcan como "por validar"
si no se proporcionan via parametros *Evidence.
"@
$auditMd | Out-File -FilePath $auditMdPath -Encoding utf8

Write-Host "Audit completa." -ForegroundColor Green
Write-Host " - JSON: $auditReportPath" -ForegroundColor Cyan
Write-Host " - MD: $auditMdPath" -ForegroundColor Cyan

