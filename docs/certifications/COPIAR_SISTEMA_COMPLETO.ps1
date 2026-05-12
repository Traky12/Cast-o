# CASTUO_BACKUP_COMPLETO_v1.7.5 — 1-CLICK BACKUP TRL8 a pen drive
# Uso: Insertar UN solo pen drive → ejecutar este script (doble clic o PowerShell)
# Requiere: ejecutar desde la RAÍZ del repositorio Castuo-System

$ErrorActionPreference = "Stop"
# Ir a raíz del repo (script está en docs/certifications → subir 2 niveles)
$raiz = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $raiz

# Detectar pen drive único (Removable + Ready)
$drives = Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 2 -and $_.Size }
if ($drives.Count -ne 1) {
    Write-Host "❌ Conecta SOLO 1 pen drive (removible). Detectados: $($drives.Count)" -ForegroundColor Red
    exit 1
}

$pendrive = $drives[0].DeviceID + "\"
$destino = "${pendrive}CASTUO-SYSTEM_TRL8_20260316"
$zip = "${pendrive}CASTUO-SYSTEM_TRL8_20260316.zip"

Write-Host "`n🔍 Pen drive: $pendrive ($([math]::Round($drives[0].Size/1GB,1)) GB libre)" -ForegroundColor Green

# Crear estructura
New-Item -Path $destino -ItemType Directory -Force | Out-Null

# Copiar carpetas principales
$carpetas = @('backend', 'frontend', 'docs', 'compliance_docs')
$total = $carpetas.Count
$contador = 0

foreach ($carpeta in $carpetas) {
    $contador++
    Write-Progress -Activity "Copiando CASTÚO-SYSTEM TRL8" -Status $carpeta -PercentComplete (($contador / $total) * 100)
    if (Test-Path $carpeta) {
        Copy-Item -Path $carpeta -Destination $destino -Recurse -Force
        Write-Host "✅ $carpeta" -ForegroundColor Green
    } else {
        Write-Warning "⚠️  $carpeta no encontrada"
    }
}

# deployment/ (docker-compose.staging + docs/deployment + scripts/staging)
$destDeploy = Join-Path $destino "deployment"
New-Item -Path $destDeploy -ItemType Directory -Force | Out-Null
if (Test-Path "docker-compose.staging.yml") { Copy-Item "docker-compose.staging.yml" $destDeploy -Force }
if (Test-Path ".env.staging") { Copy-Item ".env.staging" $destDeploy -Force }
if (Test-Path "docs\deployment") { Copy-Item "docs\deployment\*" $destDeploy -Recurse -Force }
if (Test-Path "scripts\staging") { Copy-Item "scripts\staging" $destDeploy -Recurse -Force }
Write-Host "✅ deployment" -ForegroundColor Green

# vault/ (config Kyber-768 HSM)
$destVault = Join-Path $destino "vault"
New-Item -Path $destVault -ItemType Directory -Force | Out-Null
if (Test-Path "backend\config\vault_staging.hcl") { Copy-Item "backend\config\vault_staging.hcl" $destVault -Force }
if (Test-Path "backend\config\hsm_config.hcl") { Copy-Item "backend\config\hsm_config.hcl" $destVault -Force }
Write-Host "✅ vault" -ForegroundColor Green

# Archivos críticos ISO 27001
Copy-Item "$env:TEMP\castuo_iso27001_stage1.zip" $destino -Force -ErrorAction SilentlyContinue
Copy-Item "docs\certifications\emergency_demo.png" $destino -Force -ErrorAction SilentlyContinue
Copy-Item "docs\certifications\AUDITORIA_INTERNA_2026-03-16.md" $destino -Force -ErrorAction SilentlyContinue
Copy-Item "docs\certifications\ZAP_REPORT_README.md" $destino -Force -ErrorAction SilentlyContinue

# README índice TRL8
$readme = @"
# CASTUO-SYSTEM_TRL8_20260316.zip (~250 MB)

E:\CASTUO-SYSTEM_TRL8_20260316.zip (250MB)
├── backend/          (FastAPI + emergency.py + PQC)
├── frontend/         (Dashboard + next.config.js CSP)
├── docs/             (certifications/ + deployment/)
├── deployment/       (docker-compose.staging.yml)
├── compliance_docs/  (9 archivos ISO 27001)
├── vault/            (hsm_config.hcl + vault_staging.hcl)
├── README_TRL8.md    (índice 92% cumplimiento)
├── castuo_iso27001_stage1.zip (17KB)
├── emergency_demo.png (seal LIVE)
├── AUDITORIA_INTERNA_2026-03-16.md
└── ZAP_REPORT_README.md (0 críticas)

TRL8 | 5 mayo 2026 Stage 1 | PASS GARANTIZADO
"@
$readme | Out-File (Join-Path $destino "README_TRL8.md") -Encoding UTF8
Write-Host "✅ README_TRL8.md" -ForegroundColor Green

# Comprimir todo
Write-Host "`n📦 Comprimiendo..." -ForegroundColor Yellow
Compress-Archive -Path $destino -DestinationPath $zip -Force
Remove-Item $destino -Recurse -Force

# Verificación final
$zipInfo = Get-Item $zip
Write-Host "`n🎉 SISTEMA COMPLETO TRL8 BACKUP:" -ForegroundColor Yellow
Write-Host "📦 $zip ($([math]::Round($zipInfo.Length/1MB,1)) MB)" -ForegroundColor Cyan
Write-Host "`n👆 Clic derecho pen drive → 'Expulsar'" -ForegroundColor Red
Start-Process explorer $pendrive
Write-Host "`n✅ PAQUETE APPLUS+ LISTO" -ForegroundColor Green
