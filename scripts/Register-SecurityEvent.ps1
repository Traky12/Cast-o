<#
.SYNOPSIS
    Registra eventos de seguridad con trazabilidad inmutable (GaiaChain witness) y evidencia local.

.DESCRIPTION
    - Calcula SHA256 sobre un payload canonico del metadata del evento.
    - Registra hash en GaiaChain via POST /api/v1/witness (contrato witness del repo: hash + coop_id + ipfs_cid).
    - Guarda evidencia local en `security-events/<yyyyMMdd>/<txid>.json`.
    - Opcionalmente registra el evento en el backend: POST /agents/system/log-event.

.NOTES
    - Evita claims absolutos: la eficacia depende de la configuracion y auditorias (Wazuh/OpenVAS/pentesting).
    - Para produccion, validar DPA/contratos y politica de retencion de evidencias.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$EventType,

    [Parameter(Mandatory=$true)]
    [object]$EventData,

    [int]$CoopId = 1,

    [string]$GaiaChainApiUrl = $env:GAIA_CHAIN_API_URL,
    [string]$GaiaChainApiKey = $env:GAIA_CHAIN_API_KEY,

    [string]$BackendUrl = "http://localhost:8001",

    [switch]$LogEventInBackend = $true,

    [ValidateSet("warning","error","critical","info")]
    [string]$Severity = "warning",

    [string]$OutputRoot = "security-events"
)

$ErrorActionPreference = "Stop"

function ConvertTo-Canonical {
    param([object]$obj)
    if ($null -eq $obj) { return $null }

    # Hashtable / IDictionary -> ordenar claves
    if ($obj -is [System.Collections.IDictionary]) {
        $ordered = [ordered]@{}
        foreach ($k in @($obj.Keys) | Sort-Object) {
            $ordered[$k] = ConvertTo-Canonical $obj[$k]
        }
        return $ordered
    }

    # PSCustomObject -> tratar como diccionario
    if ($obj -is [pscustomobject]) {
        $ordered = [ordered]@{}
        foreach ($p in $obj.PSObject.Properties) {
            $ordered[$p.Name] = ConvertTo-Canonical $p.Value
        }
        # ordenar de nuevo por consistencia
        $tmp = @($ordered.Keys) | Sort-Object
        $ordered2 = [ordered]@{}
        foreach ($k in $tmp) { $ordered2[$k] = $ordered[$k] }
        return $ordered2
    }

    # Arrays/Enumerables (excepto string)
    if (($obj -is [System.Collections.IEnumerable]) -and -not ($obj -is [string])) {
        $list = @()
        foreach ($i in $obj) { $list += (ConvertTo-Canonical $i) }
        return $list
    }

    return $obj
}

function Get-Sha256HexFromString {
    param([Parameter(Mandatory=$true)][string]$Text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hashBytes = $sha.ComputeHash($bytes)
    return -join ($hashBytes | ForEach-Object { $_.ToString("x2") })
}

function Invoke-Witness {
    param(
        [Parameter(Mandatory=$true)][string]$WitnessUrl,
        [Parameter(Mandatory=$true)][hashtable]$Payload,
        [string]$BearerToken
    )
    $headers = @{}
    if (-not [string]::IsNullOrWhiteSpace($BearerToken)) {
        $headers["Authorization"] = "Bearer $BearerToken"
    }
    $headers["Content-Type"] = "application/json"

    if ($headers.Count -gt 0) {
        return Invoke-RestMethod -Uri $WitnessUrl -Method Post -Headers $headers -UseBasicParsing -Body ($Payload | ConvertTo-Json -Depth 20 -Compress)
    }
    return Invoke-RestMethod -Uri $WitnessUrl -Method Post -UseBasicParsing -Body ($Payload | ConvertTo-Json -Depth 20 -Compress)
}

# 1) Construir metadata del evento (minimizar datos)
$timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$metadata = @{
    event_type = $EventType
    event_data = $EventData
    timestamp = $timestamp
    source = $env:COMPUTERNAME
}

# 2) SHA256 canonico
$canonical = ConvertTo-Canonical $metadata
$canonicalJson = ($canonical | ConvertTo-Json -Depth 50 -Compress)
$eventHash = Get-Sha256HexFromString -Text $canonicalJson

# 3) GaiaChain witness (contrato minimo del repo)
if ([string]::IsNullOrWhiteSpace($GaiaChainApiUrl)) {
    Write-Warning "GAIA_CHAIN_API_URL no definido; se omite witness remoto y se guarda evidencia local igualmente."
    $witnessResponse = @{ ok = $false; error = "missing_GAIA_CHAIN_API_URL"; tx_hash = $eventHash }
    $txid = "no-witness"
} else {
    $witnessUrl = ($GaiaChainApiUrl.TrimEnd("/")) + "/api/v1/witness"
    $payloadWitness = @{
        hash = $eventHash
        coop_id = $CoopId
        ipfs_cid = $null
    }

    try {
        $witnessResponse = Invoke-Witness -WitnessUrl $witnessUrl -Payload $payloadWitness -BearerToken $GaiaChainApiKey
        # Diferentes APIs devuelven diferentes claves; normalizamos lo que haya.
        $txid = $witnessResponse.tx_id
        if ([string]::IsNullOrWhiteSpace($txid)) { $txid = $witnessResponse.txid }
        if ([string]::IsNullOrWhiteSpace($txid)) { $txid = "tx-unknown" }
    } catch {
        Write-Warning "GaiaChain witness fallo; se guarda evidencia local igualmente. Error: $($_.Exception.Message)"
        $witnessResponse = @{ ok = $false; error = "witness_http_failed"; tx_hash = $eventHash }
        $txid = "witness-failed"
    }
}

# 4) Guardar evidencia local
$outDir = Join-Path $OutputRoot (Get-Date -Format "yyyyMMdd")
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$evidence = @{
    event_type = $EventType
    event_data = $EventData
    timestamp = $timestamp
    hash = $eventHash
    gaiachain = @{
        witness_url = $GaiaChainApiUrl
        tx_id = $txid
        response = $witnessResponse
    }
    metadata = $metadata
}

$evidencePath = Join-Path $outDir ("{0}.json" -f $txid)
$evidence | ConvertTo-Json -Depth 25 | Out-File -FilePath $evidencePath -Encoding utf8

# 5) (Opcional) Registrar en backend para evidencia en SQLite
if ($LogEventInBackend) {
    try {
        $null = Invoke-RestMethod -Uri "$BackendUrl/agents/system/log-event" -Method Post `
            -Headers @{"Content-Type"="application/json"} `
            -Body (@{
                event_type = $EventType
                details = $canonicalJson
                severity = $Severity
            } | ConvertTo-Json -Depth 20 -Compress) `
            -UseBasicParsing
    } catch {
        Write-Warning "No se pudo registrar el evento en backend /agents/system/log-event: $($_.Exception.Message)"
    }
}

Write-Host "🔒 Evento de seguridad: '$EventType' => hash SHA256=$eventHash" -ForegroundColor Cyan
Write-Host "   Evidencia local: $evidencePath" -ForegroundColor Green
if ($GaiaChainApiUrl) {
    Write-Host "   GaiaChain witness tx_id: $txid" -ForegroundColor Green
}

return $txid

