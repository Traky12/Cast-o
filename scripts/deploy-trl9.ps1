Param(
  [switch]$Strict = $true
)

$ErrorActionPreference = "Stop"

Write-Host "CASTÚO-SYSTEM TRL9 UE - Compliance Gate" -ForegroundColor Cyan

$strictArg = @()
if ($Strict) { $strictArg = @("--strict") }

python "scripts/seguridad/validar_coherencia_ue.py" @strictArg
if ($LASTEXITCODE -ne 0) {
  Write-Host "DESPLIEGUE BLOQUEADO: Cumplir mínimos UE (GDPR/DSA/eIDAS)." -ForegroundColor Red
  exit 1
}

Write-Host "DESPLIEGUE AUTORIZADO (gate OK)." -ForegroundColor Green
Write-Host "Siguiente paso: ejecutar tu pipeline real de despliegue (Ansible/Docker/CI)." -ForegroundColor Yellow
exit 0

