<#
.SYNOPSIS
    Transferencia completa al pendrive (alias operativo de Prepare-CastuoPendrive.ps1).

.DESCRIPTION
    Delega en Prepare-CastuoPendrive.ps1: tokens UTF-8 sin BOM, scripts LUKS, verify_castuo_tokens.py,
    PENDRIVE-CONTENIDO.md, INSTRUCCIONES.md + INSTRUCCIONES-PENDRIVE.md, config.env, etc.

    NOTAS IMPORTANTES:
    - No uses [System.Text.Encoding]::UTF8 con WriteAllText para secretos: suele escribir BOM y rompe Bearer/API keys.
    - Prepare-CastuoPendrive.ps1 espera DriveLetter como una sola letra (D), no "D:".

.PARAMETER DriveLetter
    Letra de unidad (D o D:).

.PARAMETER IncludeOptionalTokens
    Incluye tokens opcionales (vault, n8n, iot).

.PARAMETER FormatNtfs
    Formatea el pendrive como NTFS (destructivo).

.PARAMETER RepoRoot
    Ruta al repositorio Castuo-System (opcional).

.PARAMETER SkipTokens
    Omite la creación de tokens.

.EXAMPLE
    .\prepare_pendrive_final.ps1 -DriveLetter D

.EXAMPLE
    .\prepare_pendrive_final.ps1 -DriveLetter D -IncludeOptionalTokens -FormatNtfs -RepoRoot "C:\Users\traky\OneDrive - FCI\Castuo-System"
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $false)]
    [string]$DriveLetter = 'D',

    [switch]$IncludeOptionalTokens,
    [switch]$FormatNtfs,

    [Parameter(Mandatory = $false)]
    [string]$RepoRoot,

    [switch]$SkipTokens
)

$ErrorActionPreference = 'Stop'

# Una sola letra A-Z para el script interno (acepta D o D: o d:)
$letter = ($DriveLetter.Trim().TrimEnd(':').Substring(0, 1)).ToUpperInvariant()
if ($letter -notmatch '^[A-Za-z]$') {
    Write-Error "DriveLetter no válido: $DriveLetter"
    exit 1
}

# Raíz del repo = dos niveles por encima de scripts\windows (no usar Parent de scripts + ..\..)
if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
}
else {
    $RepoRoot = $RepoRoot.TrimEnd('\', '/')
    if (-not (Test-Path -LiteralPath $RepoRoot)) {
        Write-Error "No se encontró el repositorio en $RepoRoot"
        exit 1
    }
    $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
}

if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
    Write-Error "No se encontró el repositorio en $RepoRoot"
    exit 1
}

$internalScript = Join-Path $RepoRoot 'scripts\windows\Prepare-CastuoPendrive.ps1'
if (-not (Test-Path -LiteralPath $internalScript)) {
    Write-Error "No se encuentra Prepare-CastuoPendrive.ps1 en $internalScript"
    exit 1
}

$params = @{
    DriveLetter             = $letter
    RepoRoot                = $RepoRoot
    IncludeOptionalTokens   = $IncludeOptionalTokens
    FormatNtfs              = $FormatNtfs
    SkipTokens              = $SkipTokens
}
if ($PSBoundParameters.ContainsKey('WhatIf')) {
    $params['WhatIf'] = $true
}
if ($PSBoundParameters.ContainsKey('Confirm')) {
    $params['Confirm'] = $PSBoundParameters['Confirm']
}

try {
    & $internalScript @params
    Write-Host 'Transferencia completada.' -ForegroundColor Green
    Write-Host "Verificar contenido con: Get-ChildItem -LiteralPath '${letter}:\' -Recurse" -ForegroundColor Green
}
catch {
    Write-Error "Error durante la transferencia: $_"
    exit 1
}
