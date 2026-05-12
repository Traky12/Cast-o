# Protocolo despliegue Sabionda IA v3.1 - Ejecutar 1 vez
# Ajusta $origen a la ruta de tu PNG oficial (ej. desde Cursor workspace)

$ErrorActionPreference = "Stop"
$raiz = (Get-Item $PSScriptRoot).Parent.Parent.Parent.Parent.FullName
Set-Location $raiz

New-Item -ItemType Directory -Force -Path "frontend\public\assets\sabionda" | Out-Null

$origen = "C:\ruta\a\tu\sabionda-profile.png"   # <-- CAMBIAR por tu PNG
$destino = "frontend\public\assets\sabionda\sabionda-oficial.png"

if (Test-Path $origen) {
    Copy-Item $origen $destino -Force
    Write-Host "OK: sabionda-oficial.png desplegado en frontend/public/assets/sabionda/"
} else {
    Write-Host "AVISO: No existe $origen . Edita este script y define `$origen con la ruta de tu PNG."
}
