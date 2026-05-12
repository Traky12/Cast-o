<# 
.SYNOPSIS
    Protocolo de Continuidad Crítica (Windows) para fallos prolongados (>24h offline).
#>

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = "C:\Users\traky\OneDrive - FCI\Castuo-System"
$LOG_DIR = "C:\logs\castuo"

$ADMIN_EMAIL = "emergency@castuo-system.com"
$SMTP_SERVER = "smtp.tudominio.com"
$SMTP_TIMEOUT_MS = 5000

$CRITICAL_THRESHOLD = 50
$OFFLINE_HOURS_THRESHOLD = 24

$SERVER_URL = "http://localhost:8001/agents/system/health"
$REPORT_DIR = $LOG_DIR
$LOG_FILE = "$LOG_DIR\emergency.log"

function Ensure-LogDir {
  if (!(Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
  }
}

function Log-Emergency {
  param([string]$Message)
  Ensure-LogDir
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $entry = "[$timestamp] [EMERGENCY] $Message"
  Write-Output $entry
  Add-Content -Path $LOG_FILE -Value $entry
}

function Send-Notification {
  param([string]$Subject, [string]$Message)
  try {
    if ($SMTP_SERVER -and ($SMTP_SERVER -ne "smtp.tudominio.com")) {
      $from = "noreply@castuo-system.com"
      $host = $SMTP_SERVER
      $port = 25
      if ($SMTP_SERVER -match '^(.*):(\d+)$') {
        $host = $Matches[1]
        $port = [int]$Matches[2]
      }
      $client = New-Object System.Net.Mail.SmtpClient($host, $port)
      $client.Timeout = $SMTP_TIMEOUT_MS
      $mail = New-Object System.Net.Mail.MailMessage($from, $ADMIN_EMAIL, $Subject, $Message)
      $client.Send($mail)
    }
  } catch {
    # No bloqueamos.
  }
}

function Try-Activate {
  $healthRaw = & curl.exe -s --max-time 10 $SERVER_URL
  if ([string]::IsNullOrWhiteSpace($healthRaw)) {
    throw "Respuesta vacia $SERVER_URL"
  }
  $health = $healthRaw | ConvertFrom-Json
  $gaiaStatus = $health.components.gaiachain.status
  $pendingOps = [int]$health.components.gaiachain.pending_operations
  $lastSync = $health.components.gaiachain.last_sync_attempt

  $lastSyncTs = 0
  if ($lastSync) {
    try { $lastSyncTs = (Get-Date $lastSync).ToUniversalTime().Subtract([datetime]::UtcNow).TotalSeconds * -1 } catch { $lastSyncTs = 0 }
  }

  $now = [datetime]::UtcNow
  $hoursOffline = $OFFLINE_HOURS_THRESHOLD
  if ($lastSync) {
    try {
      $hoursOffline = [int]((([datetime]::Parse($lastSync)).ToUniversalTime() - $now).TotalHours * -1)
    } catch {
      $hoursOffline = $OFFLINE_HOURS_THRESHOLD
    }
  }

  if (($gaiaStatus -eq "offline") -and ($pendingOps -gt $CRITICAL_THRESHOLD) -and ($hoursOffline -gt $OFFLINE_HOURS_THRESHOLD)) {
    return $true
  }
  return $false
}

try {
  Log-Emergency "Chequeo de criticidad iniciado."

  $shouldActivate = $false
  try {
    $shouldActivate = Try-Activate
  } catch {
    # Si falla la lectura, mantenemos modo seguro (no activamos).
    $shouldActivate = $false
  }

  if ($shouldActivate) {
    Log-Emergency "🚨 ACTIVANDO PROTOCOLO DE CONTINUIDAD CRÍTICA"

    $healthRaw = & curl.exe -s --max-time 10 $SERVER_URL
    if ([string]::IsNullOrWhiteSpace($healthRaw)) {
      throw "Respuesta vacia $SERVER_URL"
    }
    $healthJson = $healthRaw | ConvertFrom-Json
    $reportFile = "$REPORT_DIR\emergency_report_{0}.json" -f (Get-Date -Format "yyyyMMddHHmmss")
    $healthJson | ConvertTo-Json -Depth 20 | Out-File -FilePath $reportFile -Encoding utf8

    try {
      $payload = (
        @{
          event_type = "emergency_protocol_activated"
          details = "report=$reportFile"
          severity = "critical"
        } | ConvertTo-Json -Compress
      )
      & curl.exe -s --max-time 10 -X POST -H "Content-Type: application/json" -d $payload "http://localhost:8001/agents/system/log-event" | Out-Null
    } catch {
      # No bloqueamos.
    }

    Send-Notification -Subject "🚨 PROTOCOLO DE EMERGENCIA ACTIVADO" -Message ("Se activó con reporte: {0}" -f $reportFile)
    Log-Emergency "Protocolo de emergencia completado."
    exit 0
  }

  Log-Emergency "Sistema operativo (no se activa protocolo)."
  exit 0
} catch {
  # En modo resiliente, no rompemos el scheduler.
  Log-Emergency ("Error ejecutando emergency_protocol.ps1: {0}" -f $_.Exception.Message)
  exit 1
}

