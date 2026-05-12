# scripts/thc.ps1
<#
.SYNOPSIS
    Script para ejecutar comandos THC en PowerShell.
.DESCRIPTION
    Ejecuta tests, valida el flujo THC y realiza backups.
.EXAMPLE
    .\scripts\thc.ps1 test-thc
    .\scripts\thc.ps1 validate-thc
    .\scripts\thc.ps1 backup-thc
#>

param (
    [string]$Action = "help"
)

function Run-TestTHC {
    Write-Host "Running THC tests..."
    pytest -q tests/test_thc_estimator.py tests/test_thc_integration.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Run-ValidateTHC {
    Write-Host "Validating THC flow..."
    $env:BASE_URL = "http://localhost:8000"
    bash scripts/validate_thc_flow.sh
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Run-BackupTHC {
    Write-Host "Running THC backup..."
    bash scripts/backup_castuo.sh
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Show-Help {
    Write-Host "Uso: .\scripts\thc.ps1 [action]"
    Write-Host ""
    Write-Host "Acciones disponibles:"
    Write-Host "  test-thc      - Ejecuta tests de THC"
    Write-Host "  validate-thc  - Valida el flujo THC"
    Write-Host "  backup-thc    - Ejecuta backup"
    Write-Host "  help          - Muestra esta ayuda"
}

switch ($Action) {
    "test-thc"      { Run-TestTHC; break }
    "validate-thc"  { Run-ValidateTHC; break }
    "backup-thc"    { Run-BackupTHC; break }
    default         { Show-Help; break }
}
