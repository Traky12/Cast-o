<#
.SYNOPSIS
    Configura estructura base del repositorio CASTUO-SYSTEM.
.DESCRIPTION
    Crea directorios operativos y legales sin sobrescribir entregables existentes.
.NOTES
    Version: 1.0
    Autor: Gregorio Jimenez Bodes
    Fecha: 20/03/2026
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LegalDir = Join-Path -Path $RepoRoot -ChildPath "docs\legal"
$TRL10Dir = Join-Path -Path $LegalDir -ChildPath "TRL10"
$ScriptsDir = Join-Path -Path $RepoRoot -ChildPath "scripts"
$DocsDir = Join-Path -Path $RepoRoot -ChildPath "docs"

function Write-Ok([string]$Message) { Write-Host $Message -ForegroundColor Green }
function Write-Info([string]$Message) { Write-Host $Message -ForegroundColor Cyan }
function Write-WarnMsg([string]$Message) { Write-Host $Message -ForegroundColor Yellow }

function Ensure-Dir([string]$PathValue) {
    if (-not (Test-Path $PathValue)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
        Write-Info "Creado: $PathValue"
    } else {
        Write-WarnMsg "Ya existe: $PathValue"
    }
}

function Ensure-FileIfMissing([string]$FilePath, [string]$Content) {
    if (Test-Path $FilePath) {
        Write-WarnMsg "Se mantiene archivo existente: $FilePath"
        return
    }
    $Content | Out-File -FilePath $FilePath -Encoding utf8
    Write-Info "Creado: $FilePath"
}

function Create-DirectoryStructure {
    Write-Ok "Creando estructura de directorios..."

    $directories = @(
        $LegalDir,
        $TRL10Dir,
        (Join-Path -Path $LegalDir -ChildPath "TRL11"),
        (Join-Path -Path $LegalDir -ChildPath "TRL12"),
        (Join-Path -Path $LegalDir -ChildPath "TRL13"),
        (Join-Path -Path $LegalDir -ChildPath "plantillas"),
        (Join-Path -Path $LegalDir -ChildPath "cumplimiento"),
        (Join-Path -Path $TRL10Dir -ChildPath "pdfs"),
        (Join-Path -Path $ScriptsDir -ChildPath "deploy"),
        (Join-Path -Path $ScriptsDir -ChildPath "backup"),
        (Join-Path -Path $ScriptsDir -ChildPath "legal"),
        (Join-Path -Path $DocsDir -ChildPath "technical"),
        (Join-Path -Path $DocsDir -ChildPath "operations")
    )

    foreach ($dir in $directories) {
        Ensure-Dir -PathValue $dir
    }
}

function Create-OptionalPlaceholders {
    Write-Ok ""
    Write-Ok "Verificando placeholders minimos (sin sobreescritura)..."

    Ensure-FileIfMissing `
        -FilePath (Join-Path $TRL10Dir "contrato_ctaex_20260320.md") `
        -Content "# CONTRATO CTAEX`nDocumento base."

    Ensure-FileIfMissing `
        -FilePath (Join-Path $TRL10Dir "sla_20260320.md") `
        -Content "# SLA CASTUO-SYSTEM`nDocumento base."

    Ensure-FileIfMissing `
        -FilePath (Join-Path $TRL10Dir "politica_privacidad_gdpr_2026.md") `
        -Content "# Politica de Privacidad`nDocumento base."

    Ensure-FileIfMissing `
        -FilePath (Join-Path $TRL10Dir "terminos_servicio_suscripciones.md") `
        -Content "# Terminos de Servicio`nDocumento base."

    Ensure-FileIfMissing `
        -FilePath (Join-Path $TRL10Dir "checklist_iso_9001_2025.md") `
        -Content "# Checklist ISO 9001`nDocumento base."
}

function Ensure-ProdCompose {
    $prodCompose = Join-Path $RepoRoot "docker-compose.prod.yml"
    if (Test-Path $prodCompose) {
        Write-WarnMsg "Se mantiene docker-compose existente: $prodCompose"
        return
    }

    $composeContent = @"
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    restart: unless-stopped
"@

    $composeContent | Out-File -FilePath $prodCompose -Encoding utf8
    Write-Info "Creado: $prodCompose"
}

function Main {
    Write-Ok "=== INICIO: Setup-RepoStructure ==="
    Create-DirectoryStructure
    Create-OptionalPlaceholders
    Ensure-ProdCompose
    Write-Ok ""
    Write-Ok "Repositorio configurado correctamente."
    Write-Ok "Siguientes pasos:"
    Write-Info "1) .\scripts\Generate-LegalPdfs.ps1"
    Write-Info "2) .\scripts\deploy_hetzner.ps1"
}

Main

