<#
.SYNOPSIS
    Proceso completo de conexion y despliegue de CASTUO-SYSTEM en Hetzner Cloud.

.DESCRIPTION
    Cubre:
      1. Verificar requisitos locales (SSH, Docker)
      2. Conectar al servidor Hetzner via SSH
      3. Clonar el repo y preparar el entorno
      4. Levantar el stack con Docker Compose
      5. Verificar health checks de todos los servicios
      6. Configurar DNS (opcional)

    Servidores disponibles en el proyecto (Helsinki, hel1):
      - ubuntu-4gb-hel1-1 : 4GB RAM  (entornos de staging / prueba)
      - ubuntu-8gb-hel1-1 : 8GB RAM  (produccion / demo Alex)

.PARAMETER ServerIP
    IP publica del servidor Hetzner.
    Obtenerla en: https://console.hetzner.cloud -> Servers -> nombre -> Public IP.

.PARAMETER SshKeyPath
    Ruta a la clave privada SSH (por defecto ~/.ssh/id_rsa).

.PARAMETER SshUser
    Usuario SSH del servidor (por defecto root para Ubuntu en Hetzner).

.PARAMETER EnvFile
    Ruta local al fichero .env con los secretos. Se copiara al servidor si no existe.

.PARAMETER SkipDeploy
    Solo conecta y verifica; no ejecuta docker compose.

.EXAMPLE
    # Despliegue completo en ubuntu-8gb-hel1-1 (#118296333 · cax21 ARM64):
    .\Connect-Hetzner-Deploy.ps1 -ServerIP "89.167.5.233"

    # Con .env ya preparado:
    .\Connect-Hetzner-Deploy.ps1 -ServerIP "89.167.5.233" -EnvFile "C:\Users\traky\.castuo.env"

    # Solo verificar sin redesplegar:
    .\Connect-Hetzner-Deploy.ps1 -ServerIP "89.167.5.233" -SkipDeploy

    # Servidor de staging ubuntu-4gb-hel1-1:
    .\Connect-Hetzner-Deploy.ps1 -ServerIP "TU_IP_STAGING" -SshKeyPath "C:\Users\traky\.ssh\hetzner_ed25519"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $ServerIP,

    [string] $SshKeyPath   = "$env:USERPROFILE\.ssh\id_rsa",
    [string] $SshUser      = "root",
    [string] $EnvFile      = "",
    [switch] $SkipDeploy
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# ─── Colores de salida ────────────────────────────────────────────────────────
function Write-Step  { param($msg) Write-Host "`n[>>] $msg" -ForegroundColor Cyan }
function Write-Ok    { param($msg) Write-Host "[OK] $msg"   -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "[!!] $msg"   -ForegroundColor Yellow }
function Write-Fail  { param($msg) Write-Host "[XX] $msg"   -ForegroundColor Red; exit 1 }

$SshOpts = @(
    "-o", "StrictHostKeyChecking=no"
    "-o", "ConnectTimeout=15"
    "-o", "ServerAliveInterval=30"
    "-i", $SshKeyPath
)

function Invoke-Ssh {
    param([string]$Cmd)
    & ssh @SshOpts "$SshUser@$ServerIP" $Cmd
    if ($LASTEXITCODE -ne 0) { Write-Fail "Fallo SSH: $Cmd" }
}

function Invoke-SshCapture {
    param([string]$Cmd)
    $out = & ssh @SshOpts "$SshUser@$ServerIP" $Cmd 2>&1
    return $out
}

# ─── 1. Requisitos locales ────────────────────────────────────────────────────
Write-Step "1/6  Verificando requisitos locales"

if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Fail "ssh no está en PATH. En Windows 10/11 ve a: Configuracion > Aplicaciones > Características opcionales > OpenSSH Client."
}
if (-not (Test-Path $SshKeyPath)) {
    Write-Fail "Clave SSH no encontrada: $SshKeyPath`n  → Genera una con: ssh-keygen -t ed25519 -C 'castuo-hetzner'"
}
Write-Ok "ssh disponible y clave SSH localizada."

# ─── 2. Conectividad SSH ─────────────────────────────────────────────────────
Write-Step "2/6  Probando conexion SSH a $ServerIP"

$uname = Invoke-SshCapture "uname -a"
if ($uname -match "Linux") {
    Write-Ok "Conectado: $uname"
} else {
    Write-Fail "Respuesta inesperada: $uname"
}

# ─── 3. Preparar servidor ─────────────────────────────────────────────────────
Write-Step "3/6  Preparando entorno en el servidor"

$remoteHasDocker = Invoke-SshCapture "command -v docker && echo YES || echo NO"
if ($remoteHasDocker -notmatch "YES") {
    Write-Warn "Docker no instalado. Instalando..."
    Invoke-Ssh "apt-get update -qq && apt-get install -y docker.io docker-compose-plugin && systemctl enable --now docker"
    Write-Ok "Docker instalado."
} else {
    Write-Ok "Docker disponible."
}

$remoteHasGit = Invoke-SshCapture "command -v git && echo YES || echo NO"
if ($remoteHasGit -notmatch "YES") {
    Invoke-Ssh "apt-get install -y git"
}

# Clonar o actualizar repo
$repoExists = Invoke-SshCapture "[ -d /opt/castuo-system/.git ] && echo YES || echo NO"
if ($repoExists -match "YES") {
    Write-Warn "Repo ya existe. Actualizando a HEAD de main..."
    Invoke-Ssh "cd /opt/castuo-system && git fetch origin && git checkout main && git pull --ff-only"
} else {
    Write-Step "  Clonando repositorio..."
    Invoke-Ssh "git clone https://github.com/Traky12/Castuo-system.git /opt/castuo-system"
}
Write-Ok "Repositorio en /opt/castuo-system"

# ─── 4. Copiar .env ───────────────────────────────────────────────────────────
Write-Step "4/6  Configurando variables de entorno"

$remoteEnv = Invoke-SshCapture "[ -f /opt/castuo-system/.env ] && echo YES || echo NO"

if ($remoteEnv -notmatch "YES") {
    if ($EnvFile -and (Test-Path $EnvFile)) {
        Write-Step "  Copiando $EnvFile al servidor..."
        & scp @SshOpts $EnvFile "${SshUser}@${ServerIP}:/opt/castuo-system/.env"
        if ($LASTEXITCODE -ne 0) { Write-Fail "Error copiando .env" }
        Write-Ok ".env copiado desde $EnvFile"
    } else {
        Write-Warn "No hay .env en el servidor ni se proporcionó -EnvFile local."
        Write-Warn "Creando .env desde .env.example. DEBES editar los secretos antes de usar en produccion."
        Invoke-Ssh "cp /opt/castuo-system/.env.example /opt/castuo-system/.env"
    }
} else {
    Write-Ok ".env ya existe en el servidor. Se mantiene sin cambios."
}

# ─── 5. Docker Compose up ────────────────────────────────────────────────────
if (-not $SkipDeploy) {
    Write-Step "5/6  Levantando stack (docker compose up --build)"
    Write-Warn "  Servidor: cax21 ARM64 (Ampere Altra). Las imagenes se compilan para linux/arm64."
    Write-Warn "  Primer despliegue puede tardar 5-10 minutos."

    Invoke-Ssh @"
        cd /opt/castuo-system &&
        docker compose pull --quiet 2>/dev/null || true &&
        DOCKER_BUILDKIT=1 docker compose up -d --build
"@
    Write-Ok "docker compose up completado."
} else {
    Write-Step "5/6  -SkipDeploy activo; omitiendo despliegue."
}

# ─── 6. Health checks ────────────────────────────────────────────────────────
Write-Step "6/6  Verificando salud de los servicios"

# Esperar a que la API arranque (max 90s)
$apiUrl = "http://${ServerIP}:8000/health"
$n8nUrl = "http://${ServerIP}:5678"
$grafanaUrl = "http://${ServerIP}:3000"

Write-Host "  Esperando API en $apiUrl ..."
$maxWait = 90
$waited  = 0
$apiOk   = $false
do {
    Start-Sleep -Seconds 5
    $waited += 5
    try {
        $r = Invoke-WebRequest -Uri $apiUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $apiOk = $true; break }
    } catch { }
} while ($waited -lt $maxWait)

if ($apiOk) {
    Write-Ok "API         $apiUrl  [200 OK]"
    Write-Host "     Respuesta: $($r.Content)"
} else {
    Write-Warn "API no respondio en ${maxWait}s. Comprueba logs: ssh $SshUser@$ServerIP 'docker compose -C /opt/castuo-system logs api'"
}

# n8n - solo comprobar puerto abierto
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect($ServerIP, 5678)
    $tcp.Close()
    Write-Ok "n8n         $n8nUrl  [puerto abierto]"
} catch {
    Write-Warn "n8n         puerto 5678 no accesible aun."
}

# Grafana
try {
    $rg = Invoke-WebRequest -Uri $grafanaUrl -UseBasicParsing -TimeoutSec 8 -ErrorAction Stop
    Write-Ok "Grafana     $grafanaUrl  [$($rg.StatusCode)]"
} catch {
    Write-Warn "Grafana     puerto 3000 no accesible aun."
}

# Estado de contenedores en el servidor
Write-Host ""
Write-Step "   Estado de contenedores en el servidor:"
Invoke-Ssh "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || docker compose -f /opt/castuo-system/docker-compose.yml ps 2>/dev/null"

# ─── Resumen ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  CASTUO-SYSTEM  —  Acceso a servicios" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  API  (SABIONDA)   http://${ServerIP}:8000/health"
Write-Host "  n8n  (workflows)  http://${ServerIP}:5678"
Write-Host "  Grafana           http://${ServerIP}:3000  (admin / ver .env GRAFANA_PASSWORD)"
Write-Host "  Prometheus        http://${ServerIP}:9090"
Write-Host "  GaiaChain RPC     http://${ServerIP}:8545"
Write-Host ""
Write-Host "  SSH directo:"
Write-Host "    ssh -i $SshKeyPath $SshUser@$ServerIP"
Write-Host ""
Write-Host "  Logs en tiempo real:"
Write-Host "    ssh $SshUser@$ServerIP 'cd /opt/castuo-system && docker compose logs -f'"
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
