<# 
.SYNOPSIS
    Sincroniza operaciones pendientes con GaiaChain cuando la red está disponible.
    Rutas configuradas para: C:\Users\traky\OneDrive - FCI\Castuo-System
#>

$ErrorActionPreference = "Stop"

# =========================
# Configuración (Windows)
# =========================
$PROJECT_ROOT = "C:\Users\traky\OneDrive - FCI\Castuo-System"
$LOG_DIR = "C:\logs\castuo"
$LOG_FILE = "$LOG_DIR\gaiachain_sync.log"

$DB_PATH = "$PROJECT_ROOT\resilience.db"
$CERTIFICATES_DIR = "$PROJECT_ROOT\docs\certificates"
$INVOICES_DIR = "$PROJECT_ROOT\invoices"

$MAX_RETRIES = 5
$INITIAL_INTERVAL = 10
$BACKOFF_FACTOR = 2

$ADMIN_EMAIL = "tu@email.com"  # Cambia por tu email real
$SMTP_SERVER = "smtp.tudominio.com"
$EMAIL_FROM = "noreply@castuo-system.com"
$SMTP_TIMEOUT_MS = 5000

function Ensure-LogDir {
  if (!(Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
  }
}

function Log-Message {
  param(
    [string]$Level,
    [string]$Message
  )

  Ensure-LogDir
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $logEntry = "[$timestamp] [$Level] $Message"
  Write-Output $logEntry
  Add-Content -Path $LOG_FILE -Value $logEntry

  # Notificación opcional (si SMTP no está, no rompemos continuidad).
  if (($Level -eq "ERROR") -or ($Level -eq "CRITICAL")) {
    try {
      if ($SMTP_SERVER -and ($SMTP_SERVER -ne "smtp.tudominio.com")) {
        $emailSubject = "[$Level] Sincronización GaiaChain: $Message"
        $emailBody = @"
$logEntry

---
Este mensaje fue generado automáticamente por el sistema CASTÚO-SYSTEM.
No responder a este correo.
"@
        $host = $SMTP_SERVER
        $port = 25
        if ($SMTP_SERVER -match '^(.*):(\d+)$') {
          $host = $Matches[1]
          $port = [int]$Matches[2]
        }
        $client = New-Object System.Net.Mail.SmtpClient($host, $port)
        $client.Timeout = $SMTP_TIMEOUT_MS
        $mail = New-Object System.Net.Mail.MailMessage($EMAIL_FROM, $ADMIN_EMAIL, $emailSubject, $emailBody)
        $client.Send($mail)
      }
    } catch {
      # Ignorar fallos de notificación: el objetivo es no bloquear la sincronización.
    }
  }
}

function Test-GaiaChain {
  try {
    gaiachain version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
      Log-Message -Level "INFO" -Message "GaiaChain disponible"
      return $true
    }
  } catch {
    # Ignoramos errores: seguimos con el flujo tolerante a fallos.
  }
  Log-Message -Level "ERROR" -Message "GaiaChain NO disponible"
  return $false
}

function Invoke-Sync {
  # Llamada determinista: una ejecución con timeout y evidencia completa.
  try {
    Log-Message -Level "INFO" -Message "Ejecutando POST /agents/system/sync-gaiachain (timeout: 10s)"

    $responseRaw = & curl.exe -s --max-time 10 -X POST "http://localhost:8001/agents/system/sync-gaiachain"
    if ([string]::IsNullOrWhiteSpace($responseRaw)) {
      throw "Respuesta vacia sync-gaiachain"
    }

    Log-Message -Level "INFO" -Message ("sync-gaiachain response: " + $responseRaw)

    # Respuesta esperada (JSON): status/synced/failed/total.
    # No dependemos de ConvertFrom-Json: extraemos campos por regex para evitar fallos de parseo.
    $synced = 0
    $failed = 0
    $total = 0
    $mSynced = [regex]::Match($responseRaw, '"synced"\s*:\s*(\d+)')
    $mFailed = [regex]::Match($responseRaw, '"failed"\s*:\s*(\d+)')
    $mTotal = [regex]::Match($responseRaw, '"total"\s*:\s*(\d+)')
    if ($mSynced.Success) { $synced = [int]$mSynced.Groups[1].Value }
    if ($mFailed.Success) { $failed = [int]$mFailed.Groups[1].Value }
    if ($mTotal.Success) { $total = [int]$mTotal.Groups[1].Value }

    if ($synced -gt 0) {
      Log-Message -Level "INFO" -Message "Sincronización exitosa: $synced/$total operaciones sincronizadas"
    } elseif ($failed -eq 0 -and $total -eq 0) {
      Log-Message -Level "INFO" -Message "No hay operaciones pendientes (o GaiaChain sigue offline)."
    } else {
      Log-Message -Level "WARN" -Message "Resultado sync no optimizado: synced=$synced failed=$failed total=$total"
    }

    return $true
  } catch {
    $errMsg = $_.Exception.Message
    Log-Message -Level "ERROR" -Message ("Error en sync-gaiachain: " + $errMsg)
    return $false
  }
}

Log-Message -Level "INFO" -Message "=== INICIO DE SINCRONIZACIÓN CON GAIACHAIN ==="

$success = Invoke-Sync

Log-Message -Level "INFO" -Message "=== FIN DE SINCRONIZACIÓN ==="
if ($success -eq $true) {
  exit 0
}
exit 1

