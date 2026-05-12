#Requires -Version 5.1
<#
.SYNOPSIS
    Valida honestidad de stub YOLO en backend/routers/cameras.py (sin cv2.detect_objects ficticio).

.DESCRIPTION
    Coherente con docs/legal/PLAN-INTEGRACION-TECNICAS-AVANZADAS-V2.5.md.
    Raiz repo: env CASTUO_REPO_ROOT o padre de scripts/.

.NOTES
    Sin modelo entrenado: estado esperado parcial (plan).
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Get-CastuoRepoRoot {
    if ($env:CASTUO_REPO_ROOT -and (Test-Path (Join-Path $env:CASTUO_REPO_ROOT "backend\routers\cameras.py"))) {
        return (Resolve-Path $env:CASTUO_REPO_ROOT).Path
    }
    $here = $PSScriptRoot
    if (-not $here) { $here = Split-Path -Parent $MyInvocation.MyCommand.Path }
    $candidate = Resolve-Path (Join-Path $here "..") | Select-Object -ExpandProperty Path
    if (Test-Path (Join-Path $candidate "backend\routers\cameras.py")) {
        return $candidate
    }
    throw "Raiz del repo no encontrada. Defina CASTUO_REPO_ROOT."
}

$RepoPath = Get-CastuoRepoRoot
$camerasPath = Join-Path $RepoPath "backend\routers\cameras.py"

if (-not (Test-Path $camerasPath)) {
    Write-Error "cameras.py no encontrado: $camerasPath"
    exit 1
}

$text = Get-Content -LiteralPath $camerasPath -Raw

Write-Host "Validando stubs en cameras.py ($camerasPath)..." -ForegroundColor Cyan

$failed = $false

if ($text -match "cv2\.detect_objects") {
    Write-Host "CRITICO: aparece cv2.detect_objects (API inexistente)." -ForegroundColor Red
    $failed = $true
} else {
    Write-Host "OK: no hay cv2.detect_objects" -ForegroundColor Green
}

foreach ($needle in @("detect_plagas", "YOLOv8", "Modelo no cargado")) {
    if ($text -notmatch [regex]::Escape($needle)) {
        Write-Host "AVISO: texto esperado ausente: $needle" -ForegroundColor Yellow
        $failed = $true
    } else {
        Write-Host "OK: presente '$needle'" -ForegroundColor Green
    }
}

if ($text -match "Modelo no cargado") {
    Write-Host ""
    Write-Host "Estado YOLOv8: PARCIAL (placeholder)." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Estado YOLOv8: revisar mensaje de placeholder." -ForegroundColor Yellow
    $failed = $true
}

if ($text -match "ADR-\d+") {
    Write-Host "ADR referenciada." -ForegroundColor Cyan
} else {
    Write-Warning "Sin referencia ADR en cameras.py."
}

if ($failed) {
    Write-Host ""
    Write-Host "Validacion terminada con avisos o errores." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Validacion OK: cameras.py alineado con stub parcial." -ForegroundColor Green
exit 0
