<#
.SYNOPSIS
    Lanza el sistema Castúo localmente con un solo comando (Windows).
#>

$projectRoot = "c:\Users\traky\OneDrive - FCI\Castuo-System"
Set-Location $projectRoot

Write-Host "🔧 Activando entorno virtual..."
if (-not (Test-Path ".\venv")) {
    Write-Host "Creando entorno virtual en .\venv ..."
    python -m venv venv
}
& ".\venv\Scripts\Activate.ps1"

Write-Host "🚀 Iniciando API en http://localhost:8000..."
Start-Process "python" -ArgumentList "backend/main.py"
Start-Sleep -Seconds 2

Write-Host "📖 Abriendo documentación..."
Start-Process "http://localhost:8000/docs"

Write-Host "`n✅ SISTEMA OPERATIVO:`n"
Write-Host "1. Probar cifrado holográfico:"
Write-Host "   curl -X POST http://localhost:8000/encrypt -H \"Content-Type: application/json\" -d '{\"data\":\"Hola Mundo\",\"use_holography\":true}'`n"
Write-Host "2. Probar análisis de finca:"
Write-Host "   curl -X POST http://localhost:8000/api/analyze -F \"file=@test.csv\"`n"
Write-Host "3. Ver métricas (si Prometheus está desplegado en Kubernetes): http://localhost:9090"

