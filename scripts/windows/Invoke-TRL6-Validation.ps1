# Invoke-TRL6-Validation.ps1 — pytest -m trl6 + scripts E2E del lab (Windows)
# Requisitos: PYTHONPATH=raíz repo; stub lab en marcha si ejecutas E2E (Test-Complete-RoboticsLab.ps1).
# -Evidence: Export-TRL6-Evidence.ps1 (JUnit + manifest) antes del E2E; amplía manifest con e2e_*.

param(
    [string]$LabUrl = "http://127.0.0.1:8011",
    [switch]$SkipE2E,
    [switch]$Evidence
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $root
$env:PYTHONPATH = $root
$env:CASTUO_ROBOTICS_LAB_URL = $LabUrl

if ($Evidence) {
    Write-Host "[TRL6] Generando evidencia (JUnit + manifest)..." -ForegroundColor Cyan
    & "$PSScriptRoot\Export-TRL6-Evidence.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "[TRL6] pytest -m trl6 (raíz: $root)" -ForegroundColor Cyan
    python -m pytest -m trl6 -q
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$e2eOk = $true
$e2eRan = $false
if (-not $SkipE2E) {
    $e2eRan = $true
    Write-Host "[TRL6] Test-Complete-RoboticsLab.ps1 (CASTUO_ROBOTICS_LAB_URL=$LabUrl)" -ForegroundColor Cyan
    & "$PSScriptRoot\Test-Complete-RoboticsLab.ps1"
    if ($LASTEXITCODE -ne 0) { $e2eOk = $false }
}

if ($Evidence -and (Test-Path (Join-Path $root "reports\trl6\manifest.json"))) {
    $m = Get-Content (Join-Path $root "reports\trl6\manifest.json") -Raw | ConvertFrom-Json
    $m | Add-Member -NotePropertyName e2e_scripts_ran -NotePropertyValue $e2eRan -Force
    $m | Add-Member -NotePropertyName e2e_scripts_completed_ok -NotePropertyValue ($(if ($e2eRan) { $e2eOk } else { $null })) -Force
    $m | Add-Member -NotePropertyName e2e_lab_url -NotePropertyValue $LabUrl -Force
    ($m | ConvertTo-Json -Depth 8) | Set-Content (Join-Path $root "reports\trl6\manifest.json") -Encoding UTF8
}

Write-Host "[TRL6] Validación completada." -ForegroundColor Green
if ($e2eRan -and -not $e2eOk) { exit 1 }
