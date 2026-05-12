<#
.SYNOPSIS
    Crea en un volumen Windows (ej. D:) la estructura CASTÚO: tokens/, config, scripts y documentación.

.DESCRIPTION
    NTFS en Windows NO equivale a LUKS. Use este script para empaquetar ficheros; el cifrado de volumen
    completo debe hacerse en Linux (prepare_pendrive_luks.example.sh) o WSL2 con cryptsetup.

.PARAMETER DriveLetter
    Letra de unidad sin dos puntos (ej. D).

.PARAMETER RepoRoot
    Raíz del repositorio Castuo-System. Por defecto: dos niveles por encima de este .ps1.

.PARAMETER FormatNtfs
    Si se indica, formatea el volumen (DESTRUCTIVO). Requiere -Confirm:$false o confirmación explícita.

.PARAMETER SkipTokens
    No genera ni sobrescribe ficheros en tokens\.

.PARAMETER IncludeOptionalTokens
    Crea vault.token, n8n.key e iot.key con marcador REPLACE_* (sustituir en Linux antes de producción).

.EXAMPLE
    .\Prepare-CastuoPendrive.ps1 -DriveLetter D
.EXAMPLE
    .\Prepare-CastuoPendrive.ps1 -DriveLetter D -IncludeOptionalTokens
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $false)]
    [ValidatePattern('^[A-Za-z]$')]
    [string]$DriveLetter = 'D',

    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = '',

    [switch]$FormatNtfs,
    [switch]$SkipTokens,
    [switch]$IncludeOptionalTokens
)

$ErrorActionPreference = 'Stop'

function Write-TokenFile {
    param([string]$Path, [string]$Value)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Value, $utf8NoBom)
}

function Test-Utf8Bom {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }
    $b = [System.IO.File]::ReadAllBytes($Path)
    if ($b.Length -lt 3) {
        return $false
    }
    return ($b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
}

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
}

$usbPath = "${DriveLetter}:\"
if (-not (Test-Path -LiteralPath $usbPath)) {
    throw "No existe la ruta $usbPath — conecta el pendrive y revisa la letra."
}

$deploy = Join-Path $RepoRoot 'deploy'
$scripts = Join-Path $RepoRoot 'scripts'
$items = @(
    @{ Src = Join-Path $deploy 'mount_secure.example.sh'; Dst = 'mount_secure.example.sh' },
    @{ Src = Join-Path $deploy 'umount_secure.example.sh'; Dst = 'umount_secure.example.sh' },
    @{ Src = Join-Path $deploy 'prepare_pendrive_luks.example.sh'; Dst = 'prepare_pendrive_luks.example.sh' },
    @{ Src = Join-Path $deploy 'PENDRIVE-CONTENIDO.md'; Dst = 'PENDRIVE-CONTENIDO.md' },
    @{ Src = Join-Path $deploy 'INSTRUCCIONES-PENDRIVE.md'; Dst = 'INSTRUCCIONES-PENDRIVE.md' },
    @{ Src = Join-Path $scripts 'verify_castuo_tokens.py'; Dst = 'verify_castuo_tokens.py' }
)

if ($FormatNtfs) {
    if (-not $PSCmdlet.ShouldProcess("${DriveLetter}:", 'Formatear volumen NTFS (destruye datos)')) {
        throw 'Cancelado.'
    }
    Get-Volume -DriveLetter $DriveLetter -ErrorAction Stop | Out-Null
    Format-Volume -DriveLetter $DriveLetter -FileSystem NTFS -NewFileSystemLabel 'CASTUO_PACK' -Confirm:$false
}

$tokensDir = Join-Path $usbPath 'tokens'
New-Item -ItemType Directory -Path $tokensDir -Force | Out-Null

if (-not $SkipTokens) {
    Write-TokenFile (Join-Path $tokensDir 'admin_general.token') ("admin_general_{0}" -f [guid]::NewGuid().ToString('N'))
    Write-TokenFile (Join-Path $tokensDir 'farmer.key') ("farmer_{0}" -f [guid]::NewGuid().ToString('N'))
    Write-TokenFile (Join-Path $tokensDir 'technician.key') ("technician_{0}" -f [guid]::NewGuid().ToString('N'))
    Write-Host 'Tokens de ejemplo generados (sustituir por secretos reales antes de producción).' -ForegroundColor Yellow
}

if ($IncludeOptionalTokens) {
    Write-TokenFile (Join-Path $tokensDir 'vault.token') 'REPLACE_VAULT_TOKEN_ROOT_OR_HVAC'
    Write-TokenFile (Join-Path $tokensDir 'n8n.key') 'REPLACE_N8N_WEBHOOK_OR_SECRET_SI_APLICA'
    Write-TokenFile (Join-Path $tokensDir 'iot.key') 'REPLACE_IOT_OR_MQTT_SECRET_SI_APLICA'
    Write-Host 'Tokens opcionales creados (vault.token, n8n.key, iot.key) — sustituir contenido y mapear *_FILE en .env.' -ForegroundColor Yellow
}

foreach ($it in $items) {
    if (-not (Test-Path -LiteralPath $it.Src)) {
        throw "Falta en el repo: $($it.Src)"
    }
    Copy-Item -LiteralPath $it.Src -Destination (Join-Path $usbPath $it.Dst) -Force
}

# scripts\ai\<módulo>: copia recursiva si existe (generativo, sigpac, n8n, robotics, …)
$aiRoot = Join-Path $scripts 'ai'
if (Test-Path -LiteralPath $aiRoot) {
    New-Item -ItemType Directory -Path (Join-Path $usbPath 'scripts\ai') -Force | Out-Null
    foreach ($sub in @('generative', 'sigpac', 'n8n', 'robotics')) {
        $modSrc = Join-Path $aiRoot $sub
        if (-not (Test-Path -LiteralPath $modSrc)) {
            continue
        }
        $modDst = Join-Path $usbPath "scripts\ai\$sub"
        Copy-Item -LiteralPath $modSrc -Destination $modDst -Recurse -Force
        Write-Host "Copiado scripts\ai\$sub -> $modDst" -ForegroundColor DarkCyan
    }
}
else {
    Write-Warning "No existe $aiRoot — omite paquete scripts\ai en el USB."
}

$modelsRg = Join-Path $RepoRoot 'models\rg'
$modelsDst = Join-Path $usbPath 'models\rg'
if (Test-Path -LiteralPath $modelsRg) {
    $any = Get-ChildItem -LiteralPath $modelsRg -File -ErrorAction SilentlyContinue
    if ($any) {
        New-Item -ItemType Directory -Path $modelsDst -Force | Out-Null
        Copy-Item -Path (Join-Path $modelsRg '*') -Destination $modelsDst -Force
        Write-Host "Copiados artefactos bajo models\rg" -ForegroundColor DarkCyan
    }
}

$rgiCompose = Join-Path $RepoRoot 'docker-compose.rgi.example.yml'
if (Test-Path -LiteralPath $rgiCompose) {
    Copy-Item -LiteralPath $rgiCompose -Destination (Join-Path $usbPath 'docker-compose.rgi.example.yml') -Force
}

$deployDocs = Join-Path $RepoRoot 'docs\deploy'
Get-ChildItem -Path $deployDocs -Filter 'PRONT-*.md' -File -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $usbPath $_.Name) -Force
    Write-Host "Copiado PRONT al USB: $($_.Name)" -ForegroundColor DarkCyan
}

$trlMaster = Join-Path $deployDocs 'TRL-MASTER.md'
if (Test-Path -LiteralPath $trlMaster) {
    Copy-Item -LiteralPath $trlMaster -Destination (Join-Path $usbPath 'TRL-MASTER.md') -Force
    Write-Host 'Copiado TRL-MASTER.md al USB' -ForegroundColor DarkCyan
}

$instr = Join-Path $deploy 'INSTRUCCIONES-PENDRIVE.md'
if (Test-Path -LiteralPath $instr) {
    Copy-Item -LiteralPath $instr -Destination (Join-Path $usbPath 'INSTRUCCIONES.md') -Force
}

$configSrc = Join-Path $deploy 'config.env.pendrive.example'
$configDst = Join-Path $usbPath 'config.env'
if (Test-Path -LiteralPath $configSrc) {
    Copy-Item -LiteralPath $configSrc -Destination $configDst -Force
} else {
    $cfg = @'
CASTUO_LUKS_DEVICE=/dev/disk/by-id/usb-SUSTITUIR_POR_EL_REAL
CASTUO_LUKS_MAPPER=castuo_usb
CASTUO_CASTUO_SECURE_MOUNT=/mnt/castuo_secure
CASTUO_TOKENS_PATH=/mnt/castuo_secure/tokens
'@
    Write-TokenFile $configDst ($cfg.TrimEnd() + "`n")
}

if (Test-Path -LiteralPath $configSrc) {
    Copy-Item -LiteralPath $configSrc -Destination (Join-Path $usbPath 'config.env.pendrive.example') -Force
}

if (-not $SkipTokens) {
    foreach ($name in @('admin_general.token', 'farmer.key', 'technician.key')) {
        $p = Join-Path $tokensDir $name
        if (-not (Test-Path -LiteralPath $p)) {
            continue
        }
        if (Test-Utf8Bom $p) {
            Write-Warning "BOM UTF-8 en tokens\$name — revisar codificación."
        }
        else {
            Write-Host "Sin BOM (correcto): tokens\$name" -ForegroundColor DarkGreen
        }
    }
}

Write-Host "Listo: $usbPath" -ForegroundColor Green
Write-Host 'Siguiente: revisar tokens\, editar config.env (by-id Linux), LUKS en Linux con prepare_pendrive_luks.example.sh (copia en el USB).' -ForegroundColor Cyan
Get-ChildItem -LiteralPath $usbPath -Recurse -File | Select-Object FullName, Length
