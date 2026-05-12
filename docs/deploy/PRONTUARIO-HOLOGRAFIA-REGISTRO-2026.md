# PRONTUARIO HOLOGRAFÍA Y REGISTRO DE INFORMACIÓN

*Cableado **edge Windows** para captura holográfica y registro ambiental. Los servicios `Castuo*` y `C:\CastuoSystem` deben existir en el host tras el instalador/stack propio; si no, sustituir nombres y rutas sin romper la traza de datos.*

---

## 📋 CONFIGURACIÓN INICIAL

### 1.1. Verificación del Sistema

```powershell
# Verificar estado de los servicios
Get-Service -Name "CastuoHolography" | Select-Object Status, DisplayName
Get-Service -Name "CastuoDataLogger" | Select-Object Status, DisplayName

# Verificar directorios de datos
Test-Path "C:\CastuoSystem\HolographyData"
Test-Path "C:\CastuoSystem\DataLog"
```

---

## 🔧 CONFIGURACIÓN DEL SISTEMA

### 2.1. Configuración de Holografía

```powershell
# Asegurar árbol base (evita fallos silenciosos en New-Item de JSON)
$base = "C:\CastuoSystem"
New-Item -Path "$base\Config", "$base\HolographyData" -ItemType Directory -Force | Out-Null

$holographyConfig = @{
    Resolution = "4K"
    FPS        = 30
    Depth      = 16
    OutputPath = "$base\HolographyData"
}

Set-Content -Path "$base\Config\HolographyConfig.json" -Value ($holographyConfig | ConvertTo-Json) -Encoding UTF8

# Iniciar servicio de holografía
Start-Service -Name "CastuoHolography"
```

### 2.2. Configuración de Registro de Datos

```powershell
$base = "C:\CastuoSystem"
New-Item -Path "$base\Config", "$base\DataLog" -ItemType Directory -Force | Out-Null

$dataLoggerConfig = @{
    LogInterval = 60
    DataSources = @("Temperature", "Humidity", "Pressure", "LightIntensity")
    OutputPath  = "$base\DataLog"
}

Set-Content -Path "$base\Config\DataLoggerConfig.json" -Value ($dataLoggerConfig | ConvertTo-Json) -Encoding UTF8

# Iniciar servicio de registro
Start-Service -Name "CastuoDataLogger"
```

---

## 🔗 VISUALIZACIÓN DE DATOS

### 3.1. Mostrar Datos de Holografía

```powershell
# Mostrar hologramas almacenados
Get-ChildItem -Path "C:\CastuoSystem\HolographyData" -Filter "*.holo" |
    Select-Object Name, LastWriteTime, Length |
    Format-Table -AutoSize

# Mostrar último holograma generado
$lastHologram = Get-ChildItem -Path "C:\CastuoSystem\HolographyData" -Filter "*.holo" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($lastHologram) {
    Write-Host "Último holograma generado:"
    Write-Host "Nombre: $($lastHologram.Name)"
    Write-Host "Fecha: $($lastHologram.LastWriteTime)"
    Write-Host "Tamaño: $($lastHologram.Length / 1MB) MB"
}
```

### 3.2. Mostrar Registros de Datos

```powershell
# Mostrar archivos de registro
Get-ChildItem -Path "C:\CastuoSystem\DataLog" -Filter "*.log" |
    Select-Object Name, LastWriteTime, Length |
    Format-Table -AutoSize

# Mostrar contenido del último registro
$lastLog = Get-ChildItem -Path "C:\CastuoSystem\DataLog" -Filter "*.log" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($lastLog) {
    Write-Host "Último registro generado:"
    Write-Host "Nombre: $($lastLog.Name)"
    Write-Host "Fecha: $($lastLog.LastWriteTime)"
    Write-Host "Tamaño: $($lastLog.Length / 1KB) KB"
    Write-Host "Contenido:"
    Get-Content -Path $lastLog.FullName -Tail 10
}
```

---

## ⚙️ MONITOREO Y MANTENIMIENTO

### 4.1. Script de Monitoreo

```powershell
# Bucle de vigilancia: Ctrl+C para detener sin dejar servicios huérfanos de consola
function Monitor-System {
    while ($true) {
        $holographyStatus = (Get-Service -Name "CastuoHolography").Status
        $loggerStatus = (Get-Service -Name "CastuoDataLogger").Status

        Write-Host "`nEstado del sistema - $(Get-Date)"
        Write-Host "Holografía: $holographyStatus"
        Write-Host "Registro de datos: $loggerStatus"

        $holoSpace = Get-ChildItem -Path "C:\CastuoSystem\HolographyData" -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
        $logSpace = Get-ChildItem -Path "C:\CastuoSystem\DataLog" -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum

        Write-Host "Espacio usado:"
        Write-Host "Hologramas: $($holoSpace.Sum / 1GB) GB"
        Write-Host "Registros: $($logSpace.Sum / 1MB) MB"

        Start-Sleep -Seconds 60
    }
}

Monitor-System
```

---

## 🎯 GOBERNANZA Y REGISTRO

### 5.1. Registro en system_admin_playbook.py

```python
# En system_admin_playbook.py → GOVERNANCE_DOCUMENTATION
{
    "titulo": "Holografía y registro de información 2026",
    "ruta": "docs/deploy/PRONTUARIO-HOLOGRAFIA-REGISTRO-2026.md"
}
```

**Nota:** La entrada vive en `GOVERNANCE_DOCUMENTATION` del repo; `pytest tests/models/test_system_admin_playbook.py -q` valida el playbook general.

---

## 🚀 ACTIVACIÓN COMPLETA DEL SISTEMA

### 1. Iniciar Todos los Servicios

```powershell
# Iniciar todos los servicios necesarios
Start-Service -Name "CastuoHolography"
Start-Service -Name "CastuoDataLogger"
Start-Service -Name "CastuoDataProcessor"

# Verificar estado
Get-Service -Name "Castuo*" | Select-Object Name, Status | Format-Table -AutoSize
```

### 2. Configuración de Visualización en Tiempo Real

```powershell
# Configurar visualización en tiempo real (rutas del instalador edge)
$holographyViewer = Start-Process "C:\CastuoSystem\HolographyViewer.exe" -ArgumentList "--fullscreen" -PassThru
$dataDashboard = Start-Process "C:\CastuoSystem\DataDashboard.exe" -ArgumentList "--live" -PassThru

Write-Host "Visualización en tiempo real iniciada:"
Write-Host "Holografía: PID $($holographyViewer.Id)"
Write-Host "Dashboard: PID $($dataDashboard.Id)"
```

---

🚜 **Sistema completamente operativo** 🌱💪

Ahora tienes un sistema de holografía y registro de información completamente funcional que:

- Captura hologramas en tiempo real
- Registra datos ambientales y de sistema
- Monitorea el estado de los servicios
- Proporciona visualización en tiempo real
