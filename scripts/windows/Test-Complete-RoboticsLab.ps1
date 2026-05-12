# Test-Complete-RoboticsLab.ps1 — Orquesta PEI snapshot + neuromórfico + Scan3D (mismo lab stub)
# Requisitos: uvicorn lab_stub_app en CASTUO_ROBOTICS_LAB_URL (default 8011), Bearer configurado.

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$here\Test-PEI001-RoboticsLab-Stub.ps1"
& "$here\Test-Scan3D-Print.ps1"
Write-Host "E2E robotics lab scripts ejecutados. OctoPrint: revisar compose y API key en .env (no hardcode en repo)." -ForegroundColor Magenta
