<#
.SYNOPSIS
    Despliegue base en Hetzner Cloud desde PowerShell.
.DESCRIPTION
    Crea servidor y firewall, y ejecuta bootstrap remoto via SSH.
    Parametrizado por variables de entorno para evitar secretos en codigo.
.NOTES
    Version: 1.2
    Autor: Gregorio Jimenez Bodes
    Fecha: 20/03/2026
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Level, [string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    switch ($Level) {
        "INFO" { Write-Host "[$ts] [INFO] $Message" -ForegroundColor Green }
        "WARN" { Write-Host "[$ts] [WARN] $Message" -ForegroundColor Yellow }
        "ERROR" { Write-Host "[$ts] [ERROR] $Message" -ForegroundColor Red }
        default { Write-Host "[$ts] [LOG] $Message" }
    }
}

$HetznerApiToken = $env:HETZNER_API_TOKEN
$PlinkPath = if ($env:PLINK_PATH) { $env:PLINK_PATH } else { "${env:ProgramFiles}\PuTTY\plink.exe" }
$SshPublicKeyPath = if ($env:SSH_KEY_PATH) { $env:SSH_KEY_PATH } else { "$HOME\.ssh\id_rsa.pub" }
$SshPrivateKeyPath = if ($env:SSH_PRIVATE_KEY_PATH) { $env:SSH_PRIVATE_KEY_PATH } else { "$HOME\.ssh\id_rsa" }
$ServerName = if ($env:HETZNER_SERVER_NAME) { $env:HETZNER_SERVER_NAME } else { "castuo-prod-1" }
$ServerType = if ($env:HETZNER_SERVER_TYPE) { $env:HETZNER_SERVER_TYPE } else { "cx21" }
$ServerLocation = if ($env:HETZNER_SERVER_LOCATION) { $env:HETZNER_SERVER_LOCATION } else { "fsn1" }
$FirewallName = if ($env:HETZNER_FIREWALL_NAME) { $env:HETZNER_FIREWALL_NAME } else { "castuo-fw" }
$DomainName = if ($env:DOMAIN_NAME) { $env:DOMAIN_NAME } else { "tu-dominio.com" }
$ContactEmail = if ($env:CONTACT_EMAIL) { $env:CONTACT_EMAIL } else { "admin@castuo-system.com" }
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$IpFile = Join-Path $ProjectRoot ".hetzner_ip"

if (-not $HetznerApiToken) {
    Write-Log "ERROR" "Falta HETZNER_API_TOKEN en variables de entorno."
    exit 1
}

if (-not (Test-Path $SshPublicKeyPath)) {
    Write-Log "ERROR" "No existe clave publica SSH: $SshPublicKeyPath"
    exit 1
}

if (-not (Test-Path $SshPrivateKeyPath)) {
    Write-Log "ERROR" "No existe clave privada SSH: $SshPrivateKeyPath"
    exit 1
}

if (-not (Test-Path $PlinkPath)) {
    Write-Log "ERROR" "No se encontro plink.exe (PuTTY) en: $PlinkPath"
    Write-Log "INFO" "Instala PuTTY o define PLINK_PATH con la ruta completa a plink.exe."
    exit 1
}

function Test-PreRequirements {
    Write-Log "INFO" "Validando prerequisitos..."
    if ([string]::IsNullOrWhiteSpace($HetznerApiToken)) {
        Write-Log "ERROR" "Configura HETZNER_API_TOKEN en el entorno antes de ejecutar."
        Write-Log "INFO" "Ejemplo: `$env:HETZNER_API_TOKEN = '<token>' (no commitear ni pegar en logs)."
        exit 1
    }
    try {
        Invoke-RestMethod -Uri "https://api.hetzner.cloud/v1/servers" -Method Get -Headers @{
            Authorization = "Bearer $HetznerApiToken"
        } | Out-Null
        Write-Log "INFO" "API de Hetzner accesible."
    } catch {
        Write-Log "ERROR" "No se pudo acceder a la API de Hetzner. Verifica token, permisos y red (no se muestra el token en log)."
        exit 1
    }
}

function Invoke-HetznerApi {
    param(
        [string]$Method,
        [string]$Path,
        [object]$Body = $null
    )

    $headers = @{
        Authorization = "Bearer $HetznerApiToken"
        "Content-Type" = "application/json"
    }
    $uri = "https://api.hetzner.cloud/v1/$Path"
    if ($null -eq $Body) {
        return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers
    }
    $json = $Body | ConvertTo-Json -Depth 10
    return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers -Body $json
}

function Ensure-Firewall {
    Write-Log "INFO" "Asegurando firewall..."
    $all = Invoke-HetznerApi -Method "GET" -Path "firewalls"
    $existing = $all.firewalls | Where-Object { $_.name -eq $FirewallName } | Select-Object -First 1

    $rules = @(
        @{ direction = "in"; protocol = "tcp"; port = "22"; source_ips = @("0.0.0.0/0", "::/0") },
        @{ direction = "in"; protocol = "tcp"; port = "80"; source_ips = @("0.0.0.0/0", "::/0") },
        @{ direction = "in"; protocol = "tcp"; port = "443"; source_ips = @("0.0.0.0/0", "::/0") },
        @{ direction = "in"; protocol = "icmp"; source_ips = @("0.0.0.0/0", "::/0") }
    )

    if ($existing) {
        $fwId = $existing.id
        Invoke-HetznerApi -Method "POST" -Path "firewalls/$fwId/actions/set_rules" -Body @{ rules = $rules } | Out-Null
        Write-Log "INFO" "Firewall actualizado (id: $fwId)."
        return $fwId
    }

    $created = Invoke-HetznerApi -Method "POST" -Path "firewalls" -Body @{
        name = $FirewallName
        rules = $rules
    }
    $fwId = $created.firewall.id
    Write-Log "INFO" "Firewall creado (id: $fwId)."
    return $fwId
}

function Ensure-SshKey {
    Write-Log "INFO" "Asegurando clave SSH en Hetzner..."
    $name = "castuo-bootstrap-key"
    $keys = Invoke-HetznerApi -Method "GET" -Path "ssh_keys"
    $existing = $keys.ssh_keys | Where-Object { $_.name -eq $name } | Select-Object -First 1
    if ($existing) { return $existing.id }

    $pub = (Get-Content $SshPublicKeyPath -Raw).Trim()
    $created = Invoke-HetznerApi -Method "POST" -Path "ssh_keys" -Body @{
        name = $name
        public_key = $pub
    }
    return $created.ssh_key.id
}

function Create-Server {
    param(
        [int]$FirewallId,
        [int]$SshKeyId
    )
    Write-Log "INFO" "Creando servidor en Hetzner..."
    try {
        $body = @{
            name = $ServerName
            server_type = $ServerType
            image = "ubuntu-22.04"
            location = $ServerLocation
            ssh_keys = @($SshKeyId)
            firewalls = @(@{ firewall = $FirewallId })
            labels = @{ project = "castuo-system" }
        }
        $response = Invoke-HetznerApi -Method "POST" -Path "servers" -Body $body
        $serverId = $response.server.id
        $serverIp = $response.server.public_net.ipv4.ip
        Set-Content -Path $IpFile -Value $serverIp -Encoding utf8
        Write-Log "INFO" "Servidor creado. ID: $serverId, IP: $serverIp"
        return $serverIp
    } catch {
        Write-Log "ERROR" "Fallo al crear servidor: $($_.Exception.Message)"
        exit 1
    }
}

function Wait-Ssh {
    param([string]$ServerIp)
    Write-Log "INFO" "Esperando SSH en $ServerIp..."
    for ($i = 0; $i -lt 30; $i++) {
        try {
            & "$PlinkPath" -i "$SshPrivateKeyPath" -batch "root@$ServerIp" "echo ok" 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Log "INFO" "SSH disponible."
                return
            }
        } catch {}
        Start-Sleep -Seconds 10
    }
    Write-Log "ERROR" "No fue posible conectar por SSH al servidor."
    exit 1
}

function Setup-RemoteServer {
    param([string]$ServerIp)

    Write-Log "INFO" "Configurando servidor remoto..."
    $remoteScript = @"
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq curl git docker.io docker-compose-plugin ufw fail2ban nginx certbot python3-certbot-nginx
systemctl enable docker --now
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable
systemctl enable fail2ban --now
if [ ! -d /opt/castuo-system ]; then
  git clone https://github.com/tu-usuario/castuo-system.git /opt/castuo-system
fi
cd /opt/castuo-system
if [ -f .env.production ]; then cp .env.production .env; fi
if [ -f docker-compose.prod.yml ]; then
  docker compose -f docker-compose.prod.yml pull || true
  docker compose -f docker-compose.prod.yml up -d
fi
cat >/etc/nginx/sites-available/castuo-system <<'NGINX'
server {
  listen 80;
  server_name $DomainName;
  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
  location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
}
NGINX
ln -sf /etc/nginx/sites-available/castuo-system /etc/nginx/sites-enabled/castuo-system
nginx -t
systemctl restart nginx
certbot --nginx -d $DomainName --non-interactive --agree-tos -m $ContactEmail || true
"@

    $tmpFile = Join-Path $env:TEMP "castuo_remote_setup.sh"
    Set-Content -Path $tmpFile -Value $remoteScript -Encoding utf8

    & "$PlinkPath" -i "$SshPrivateKeyPath" -batch "root@$ServerIp" "bash -s" < $tmpFile
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Fallo en bootstrap remoto."
        exit 1
    }

    Remove-Item $tmpFile -ErrorAction SilentlyContinue
    Write-Log "INFO" "Bootstrap remoto completado."
}

function Main {
    Write-Log "INFO" "=== INICIO DEPLOY HETZNER ==="
    Test-PreRequirements
    $fwId = Ensure-Firewall
    $keyId = Ensure-SshKey
    $ip = Create-Server -FirewallId $fwId -SshKeyId $keyId
    Wait-Ssh -ServerIp $ip
    Setup-RemoteServer -ServerIp $ip
    try {
        Invoke-WebRequest -Uri "http://$ip:3000" -UseBasicParsing -TimeoutSec 10 | Out-Null
        Invoke-WebRequest -Uri "http://$ip:8000/health" -UseBasicParsing -TimeoutSec 10 | Out-Null
        Write-Log "INFO" "Verificacion de servicios completada."
    } catch {
        Write-Log "WARN" "No se pudo verificar algun servicio inmediatamente tras el bootstrap."
    }
    Write-Log "INFO" "Despliegue completado."
    Write-Log "INFO" "Frontend: http://$ip:3000"
    Write-Log "INFO" "Backend:  http://$ip:8000"
}

Main

