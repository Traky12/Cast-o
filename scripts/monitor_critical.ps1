<# 
.SYNOPSIS
    Monitorea el estado crítico del sistema y registra/alerta.

.DESCRIPTION
    Diseñado para Windows con rutas exactas:
      - C:\Users\traky\OneDrive - FCI\Castuo-System
      - C:\logs\castuo

    Si no hay SMTP, las alertas por email se omiten sin romper el monitoreo.
#>

$ErrorActionPreference = "Stop"

# =========================
# Configuración (Windows)
# =========================
$PROJECT_ROOT = "C:\Users\traky\OneDrive - FCI\Castuo-System"
$LOG_DIR = "C:\logs\castuo"
$ADMIN_EMAIL = "tu@email.com"
$SMTP_SERVER = "smtp.tudominio.com"
$SMTP_TIMEOUT_MS = 5000
$EMAIL_WAIT_SECONDS = 3

$CRITICAL_THRESHOLD = 5
$ERROR_THRESHOLD = 3

function Ensure-LogDir {
  if (!(Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
  }
}

function Send-Notification {
  param (
    [string]$Subject,
    [string]$Message,
    [string]$Method = "email"  # email, sms, or both (sms no implementado)
  )

  Ensure-LogDir
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $logEntry = "[$timestamp] [$Subject] $Message"
  Write-Output $logEntry
  Add-Content -Path "$LOG_DIR\monitor_critical.log" -Value $logEntry

  if (($Method -eq "email") -or ($Method -eq "both")) {
    try {
      if ($SMTP_SERVER -and ($SMTP_SERVER -ne "smtp.tudominio.com")) {
        # Envío SMTP en Job con timeout para no bloquear el monitoreo.
        $from = "noreply@castuo-system.com"
        $host = $SMTP_SERVER
        $port = 25
        if ($SMTP_SERVER -match '^(.*):(\d+)$') {
          $host = $Matches[1]
          $port = [int]$Matches[2]
        }

        $job = Start-Job -ScriptBlock {
          param($from, $to, $subj, $body, $host, $port, $timeoutMs)
          $client = New-Object System.Net.Mail.SmtpClient($host, $port)
          $client.Timeout = $timeoutMs
          $mail = New-Object System.Net.Mail.MailMessage($from, $to, $subj, $body)
          $client.Send($mail)
        } -ArgumentList $from, $ADMIN_EMAIL, $Subject, $Message, $host, $port, $SMTP_TIMEOUT_MS

        Wait-Job -Job $job -Timeout $EMAIL_WAIT_SECONDS | Out-Null
        if ($job.State -eq "Running") {
          Stop-Job -Job $job -Force | Out-Null
        }
        try { Receive-Job -Job $job -ErrorAction SilentlyContinue | Out-Null } catch { }
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue | Out-Null
      }
    } catch {
      # No bloqueamos monitoreo si falla el canal de notificación.
    }
  }
}

# 1-2. Obtiene estado del sistema (sin Invoke-WebRequest para evitar bloqueos)
try {
  $healthRaw = & curl.exe -s --max-time 5 "http://localhost:8001/agents/system/health"
  if ([string]::IsNullOrWhiteSpace($healthRaw)) {
    throw "Respuesta vacia"
  }
  $healthStatus = $healthRaw | ConvertFrom-Json
} catch {
  Send-Notification -Subject "❌ ALERTA CRÍTICA: Servidor CASTÚO-SYSTEM caído" `
    -Message "El endpoint /system/health no responde (timeout/empty). Verifica el servicio en el puerto 8001." `
    -Method "both"
  exit 1
}

$gaiachainStatus = $healthStatus.components.gaiachain.status
$pendingOps = [int]$healthStatus.components.gaiachain.pending_operations
$diskUsage = ($healthStatus.components.storage.disk_usage -replace "%", "")
$memoryUsage = ($healthStatus.components.storage.memory_usage -replace "%", "")
$criticalEventsCount = @($healthStatus.critical_events).Count
$lastSync = $healthStatus.components.gaiachain.last_sync_attempt

# 3. Verifica umbrales críticos
if ($gaiachainStatus -eq "offline" -and $pendingOps -gt $CRITICAL_THRESHOLD) {
  Send-Notification -Subject "❌ ALERTA CRÍTICA: GaiaChain offline con operaciones pendientes" `
    -Message "GaiaChain está offline con $pendingOps operaciones pendientes. Último intento de sincronización: $lastSync" `
    -Method "both"
} elseif ($gaiachainStatus -eq "offline") {
  Send-Notification -Subject "⚠️ ADVERTENCIA: GaiaChain offline" `
    -Message "GaiaChain no está disponible. El sistema sigue operativo en modo local. Operaciones pendientes: $pendingOps." `
    -Method "email"
}

if ([int]$diskUsage -gt 90) {
  Send-Notification -Subject "❌ ALERTA CRÍTICA: Disco lleno" `
    -Message "El disco está al $diskUsage%. Libera espacio inmediatamente." `
    -Method "both"
} elseif ([int]$diskUsage -gt 80) {
  Send-Notification -Subject "⚠️ ADVERTENCIA: Disco casi lleno" `
    -Message "El disco está al $diskUsage%. Monitorea el espacio." `
    -Method "email"
}

if ([int]$memoryUsage -gt 90) {
  Send-Notification -Subject "❌ ALERTA CRÍTICA: Memoria alta" `
    -Message "El uso de memoria es del $memoryUsage%. Reinicia servicios si es necesario." `
    -Method "both"
} elseif ([int]$memoryUsage -gt 80) {
  Send-Notification -Subject "⚠️ ADVERTENCIA: Memoria alta" `
    -Message "El uso de memoria es del $memoryUsage%. Monitorea el rendimiento." `
    -Method "email"
}

if ($criticalEventsCount -gt $ERROR_THRESHOLD) {
  $events = @($healthStatus.critical_events) | ForEach-Object { "$($_.timestamp) $($_.severity): $($_.details)" }
  Send-Notification -Subject "⚠️ ADVERTENCIA: Eventos críticos recientes" `
    -Message ("Se detectaron {0} eventos críticos:`n{1}" -f $criticalEventsCount, ($events -join "`n")) `
    -Method "email"
}

# 4. Verifica errores en logs recientes (optimizado para no bloquear)
try {
  $filesToCheck = @(
    "$LOG_DIR\monitor_critical.log",
    "$LOG_DIR\gaiachain_sync.log",
    "$LOG_DIR\emergency.log"
  )

  $recentErrorsLines = New-Object System.Collections.Generic.List[string]
  foreach ($f in $filesToCheck) {
    if (Test-Path $f) {
      # Leemos solo la cola para evitar recorridos costosos.
      $tailLines = Get-Content -Path $f -Tail 300 -ErrorAction SilentlyContinue
      if ($tailLines) {
        $errs = $tailLines | Select-String -Pattern "error|fail|exception|critical" -CaseSensitive
        foreach ($e in @($errs)) { $recentErrorsLines.Add($e.Line) | Out-Null }
      }
    }
  }

  if ($recentErrorsLines.Count -gt 0) {
    $errorMessage = ($recentErrorsLines | Select-Object -Last 10) -join "`n"
    Send-Notification -Subject "⚠️ ADVERTENCIA: Errores recientes en logs" `
      -Message ("Errores detectados en los logs:`n{0}" -f $errorMessage) `
      -Method "email"
  }
} catch {
  # Si fallan lecturas de logs, no bloqueamos el monitoreo.
}

# 5. Verifica cola grande
if ($pendingOps -gt 20) {
  Send-Notification -Subject "⚠️ ADVERTENCIA: Cola de operaciones pendientes grande" `
    -Message "Hay $pendingOps operaciones pendientes. Verifica la sincronización con GaiaChain." `
    -Method "email"
}

Write-Output "✅ Monitorización completada sin alertas críticas"

