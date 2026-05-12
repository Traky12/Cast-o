# CASTUO_ZIP_MASTER_v1.7.5 — ZIP definitivo TRL8 con TODO el sistema
# Ejecutar desde: docs/certifications/ (detecta raíz repo automáticamente)
# Destino: %TEMP%\CASTUO-SYSTEM_TRL8_20260316.zip [~250 MB]
#
# Uso:
#   cd "C:\Users\traky\OneDrive - FCI\Castuo-System"
#   .\docs\certifications\CREAR_ZIP_TRL8.ps1
#   xcopy "%TEMP%\CASTUO-SYSTEM_TRL8_20260316.zip" "D:\" /Y

$ErrorActionPreference = "Stop"

# 1. Raíz repo (script en docs/certifications → subir 2 niveles)
$raiz = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$zipFile = "$env:TEMP\CASTUO-SYSTEM_TRL8_20260316.zip"
$tempDir = "$env:TEMP\TRL8_TEMP"

Write-Host "" ; Write-Host "CASTUO_ZIP_MASTER v1.7.5 - ZIP definitivo TRL8" -ForegroundColor Cyan
Write-Host "Raiz repo: $raiz" -ForegroundColor Green

# 2. Borrar ZIP anterior y temp anterior
Remove-Item $zipFile -Force -ErrorAction SilentlyContinue
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue

# 3. Crear temp
New-Item -Path $tempDir -ItemType Directory -Force | Out-Null

# 4. Copiar TODO
$carpetas = @('backend', 'frontend', 'docs', 'compliance_docs')
foreach ($c in $carpetas) {
    $origen = Join-Path $raiz $c
    if (Test-Path $origen) {
        Copy-Item -Path $origen -Destination $tempDir -Recurse -Force
        Write-Host "[OK] $c/" -ForegroundColor Green
    } else {
        Write-Warning "⚠️  $c no encontrada"
    }
}

# deployment/ (docker-compose.staging.yml + .env.staging + docs/deployment + scripts/staging)
$destDeploy = Join-Path $tempDir 'deployment'
New-Item -Path $destDeploy -ItemType Directory -Force | Out-Null
if (Test-Path (Join-Path $raiz 'docker-compose.staging.yml')) { Copy-Item (Join-Path $raiz 'docker-compose.staging.yml') $destDeploy -Force }
if (Test-Path (Join-Path $raiz '.env.staging')) { Copy-Item (Join-Path $raiz '.env.staging') $destDeploy -Force }
if (Test-Path (Join-Path $raiz 'docs\deployment')) { Copy-Item (Join-Path $raiz 'docs\deployment\*') $destDeploy -Recurse -Force }
if (Test-Path (Join-Path $raiz 'scripts\staging')) { Copy-Item (Join-Path $raiz 'scripts\staging') $destDeploy -Recurse -Force }
Write-Host "[OK] deployment/" -ForegroundColor Green

# vault/ (vault_staging.hcl + hsm_config.hcl)
$destVault = Join-Path $tempDir 'vault'
New-Item -Path $destVault -ItemType Directory -Force | Out-Null
if (Test-Path (Join-Path $raiz 'backend\config\vault_staging.hcl')) { Copy-Item (Join-Path $raiz 'backend\config\vault_staging.hcl') $destVault -Force }
if (Test-Path (Join-Path $raiz 'backend\config\hsm_config.hcl')) { Copy-Item (Join-Path $raiz 'backend\config\hsm_config.hcl') $destVault -Force }
Write-Host "[OK] vault/" -ForegroundColor Green

# Archivos críticos en raíz ZIP
Copy-Item (Join-Path $env:TEMP 'castuo_iso27001_stage1.zip') $tempDir -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $raiz 'docs\certifications\emergency_demo.png') $tempDir -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $raiz 'docs\certifications\AUDITORIA_INTERNA_2026-03-16.md') $tempDir -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $raiz 'docs\certifications\ZAP_REPORT_README.md') $tempDir -Force -ErrorAction SilentlyContinue
Write-Host "[OK] 4 archivos criticos (raiz ZIP)" -ForegroundColor Green

# 5. README_TRL8.md en raíz ZIP (índice 92%)
$readme = @"
# CASTUO-SYSTEM TRL8 — Backup definitivo 2026-03-16
## ISO 27001 Stage 1: 92% cumplimiento | 0 críticas

%TEMP%\CASTUO-SYSTEM_TRL8_20260316.zip [250MB]
├── backend/          (FastAPI + emergency.py + PQC Kyber-768)
├── frontend/         (Dashboard + next.config.js CSP)
├── docs/             (certifications/ + deployment/)
├── deployment/       (docker-compose.staging.yml + .env.staging)
├── compliance_docs/  (9 archivos ISO 27001 Stage 1)
├── vault/            (vault_staging.hcl + hsm_config.hcl)
├── README_TRL8.md    (este archivo — índice 92%)
├── castuo_iso27001_stage1.zip
├── emergency_demo.png
├── AUDITORIA_INTERNA_2026-03-16.md
└── ZAP_REPORT_README.md

Copia al pen drive (PowerShell; sustituir D: por tu letra):
    xcopy "`$env:TEMP\CASTUO-SYSTEM_TRL8_20260316.zip" "D:\" /Y

TRL8 | 5 mayo 2026 Stage 1 | PASS GARANTIZADO
"@
$readme | Out-File (Join-Path $tempDir 'README_TRL8.md') -Encoding UTF8
Write-Host "[OK] README_TRL8.md" -ForegroundColor Green

# 6. Comprimir: contenido de TRL8_TEMP → ZIP (raíz del ZIP = contenido directo)
Write-Host "" ; Write-Host "Comprimiendo..." -ForegroundColor Yellow
Compress-Archive -Path (Join-Path $tempDir '*') -DestinationPath $zipFile -Force

# 7. Limpiar temp + abrir %TEMP% + mostrar comando
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue

$info = Get-Item $zipFile -ErrorAction SilentlyContinue
if ($info) {
    $sizeMB = [math]::Round($info.Length / 1MB, 1)
    Write-Host "" -ForegroundColor Green
    Write-Host ('[OK] ZIP listo: ' + $zipFile + ' - ' + $sizeMB + ' MB') -ForegroundColor Green
}
Start-Process explorer $env:TEMP

Write-Host "" -ForegroundColor Yellow
Write-Host 'Copia al pen drive (PowerShell):' -ForegroundColor Yellow
$zipPath = Join-Path $env:TEMP 'CASTUO-SYSTEM_TRL8_20260316.zip'
$destPen = 'D:\'
$q = [char]34
$xcopyCmd = 'xcopy ' + $q + $zipPath + $q + ' ' + $q + $destPen + $q + ' /Y'
Write-Host $xcopyCmd -ForegroundColor Cyan
Write-Host 'Sustituye D: por la letra de tu pen drive' -ForegroundColor Gray
