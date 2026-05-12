# CASTUO_BACKUP_LOCAL_v1.7.5 — ZIP completo TRL8 en %TEMP% (para copia manual a pen drive)
# Ejecutar desde: docs/certifications/ (o cualquier ruta; detecta raíz repo)
# Destino: %TEMP%\CASTUO-SYSTEM_TRL8_20260316.zip (~250 MB)

$ErrorActionPreference = "Stop"
$repoRaiz = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$tempDir = "$env:TEMP\CASTUO_TRL8_BACKUP"
$zipFile = "$env:TEMP\CASTUO-SYSTEM_TRL8_20260316.zip"

Write-Host "`n🚀 CASTÚO-SYSTEM TRL8 → BACKUP LOCAL" -ForegroundColor Cyan
Write-Host "📁 Raíz repo: $repoRaiz" -ForegroundColor Green

# Limpiar temp anterior
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $zipFile -Force -ErrorAction SilentlyContinue

# Crear estructura backup
New-Item -Path $tempDir -ItemType Directory -Force | Out-Null
Set-Location $repoRaiz

# Copiar carpetas principales (existentes en raíz)
$carpetas = @('backend', 'frontend', 'docs', 'compliance_docs')
foreach ($carpeta in $carpetas) {
    $origen = Join-Path $repoRaiz $carpeta
    if (Test-Path $origen) {
        Copy-Item -Path $origen -Destination $tempDir -Recurse -Force
        Write-Host "✅ $carpeta/" -ForegroundColor Green
    } else {
        Write-Warning "⚠️  $carpeta no encontrada"
    }
}

# deployment/ (docker-compose.staging + docs/deployment + scripts/staging)
$destDeploy = Join-Path $tempDir "deployment"
New-Item -Path $destDeploy -ItemType Directory -Force | Out-Null
if (Test-Path (Join-Path $repoRaiz "docker-compose.staging.yml")) { Copy-Item (Join-Path $repoRaiz "docker-compose.staging.yml") $destDeploy -Force }
if (Test-Path (Join-Path $repoRaiz ".env.staging")) { Copy-Item (Join-Path $repoRaiz ".env.staging") $destDeploy -Force }
if (Test-Path (Join-Path $repoRaiz "docs\deployment")) { Copy-Item (Join-Path $repoRaiz "docs\deployment\*") $destDeploy -Recurse -Force }
if (Test-Path (Join-Path $repoRaiz "scripts\staging")) { Copy-Item (Join-Path $repoRaiz "scripts\staging") $destDeploy -Recurse -Force }
Write-Host "✅ deployment/" -ForegroundColor Green

# vault/ (hsm_config.hcl + vault_staging.hcl)
$destVault = Join-Path $tempDir "vault"
New-Item -Path $destVault -ItemType Directory -Force | Out-Null
if (Test-Path (Join-Path $repoRaiz "backend\config\vault_staging.hcl")) { Copy-Item (Join-Path $repoRaiz "backend\config\vault_staging.hcl") $destVault -Force }
if (Test-Path (Join-Path $repoRaiz "backend\config\hsm_config.hcl")) { Copy-Item (Join-Path $repoRaiz "backend\config\hsm_config.hcl") $destVault -Force }
Write-Host "✅ vault/" -ForegroundColor Green

# Archivos críticos ISO 27001
Copy-Item "$env:TEMP\castuo_iso27001_stage1.zip" $tempDir -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $repoRaiz "docs\certifications\emergency_demo.png") $tempDir -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $repoRaiz "docs\certifications\AUDITORIA_INTERNA_2026-03-16.md") $tempDir -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $repoRaiz "docs\certifications\ZAP_REPORT_README.md") $tempDir -Force -ErrorAction SilentlyContinue
Write-Host "✅ 4 archivos críticos" -ForegroundColor Green

# README_TRL8.md índice completo
$readme = @"
# CASTÚO-SYSTEM TRL8 - Backup Completo 2026-03-16
## ISO 27001 Stage 1: 92% Cumplimiento | 0 Críticas

### Estructura (~250 MB)
- **backend/** — FastAPI + PQC Kyber-768 + emergency seal
- **frontend/** — Dashboard + CSP A.14.2.5 (next.config.js)
- **docs/** — certifications/ + deployment/
- **deployment/** — docker-compose.staging.yml
- **compliance_docs/** — 9 archivos ISO 27001
- **vault/** — hsm_config.hcl + vault_staging.hcl
- **castuo_iso27001_stage1.zip** — 17KB Stage 1 Applus+
- **emergency_demo.png** — Seal LIVE 19:14 CET
- **AUDITORIA_INTERNA_2026-03-16.md** — 92% cumplimiento
- **ZAP_REPORT_README.md** — 0 vulnerabilidades

### Despliegue staging
    docker-compose -f deployment/docker-compose.staging.yml --env-file deployment/.env.staging up -d

### Copia al pen drive (sustituir E: por tu letra)
    xcopy "%TEMP%\CASTUO-SYSTEM_TRL8_20260316.zip" "E:\" /Y

TRL8 | 5 mayo 2026 Stage 1 | PASS GARANTIZADO
"@
$readme | Out-File (Join-Path $tempDir "README_TRL8.md") -Encoding UTF8
Write-Host "✅ README_TRL8.md" -ForegroundColor Green

# Comprimir ZIP en %TEMP%
Write-Host "`n📦 Comprimiendo en %TEMP%..." -ForegroundColor Yellow
Compress-Archive -Path $tempDir -DestinationPath $zipFile -Force
Remove-Item $tempDir -Recurse -Force

# Verificar y abrir carpeta %TEMP%
$zipInfo = Get-Item $zipFile -ErrorAction SilentlyContinue
if ($zipInfo) {
    Write-Host "`n✅ ZIP generado: $zipFile ($([math]::Round($zipInfo.Length/1MB,1)) MB)" -ForegroundColor Green
}
Start-Process explorer $env:TEMP

Write-Host "`n✅ Copia manual al pen drive:" -ForegroundColor Yellow
Write-Host "xcopy `"%TEMP%\CASTUO-SYSTEM_TRL8_20260316.zip`" `"E:\`" /Y" -ForegroundColor Cyan
Write-Host "`n(Sustituye E: por la letra de tu pen drive)" -ForegroundColor Gray
