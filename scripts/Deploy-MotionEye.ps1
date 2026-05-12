<#
.SYNOPSIS
    Arranca MotionEye con docker compose (borde Hetzner/Arsys).

.NOTES
    Usar .env.camera en la raiz del repo (ver .env.camera.example).
    Tras el despliegue (requiere -EventData): .\scripts\Register-SecurityEvent.ps1 -EventType motioneye_deploy -EventData @{ integrated = $true }
#>
[CmdletBinding()]
param(
    [string]$ComposeFile = "docker-compose.camera.yml",
    [switch]$Detached = $true
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$args = @("compose", "-f", $ComposeFile, "up")
if ($Detached) { $args += "-d" }
& docker @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "MotionEye: http://127.0.0.1:8765 (ajustar host/puerto si aplica)"
