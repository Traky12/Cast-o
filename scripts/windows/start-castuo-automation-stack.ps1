# Orquesta n8n (Docker) + lab API (uvicorn) para el cableado del prontuario de automatización.
# Impacto: reduce fricción al levantar el territorio local sin repetir comandos a mano.

param(
    [int]$ApiPort = 8000,
    [switch]$SkipDocker,
    [switch]$SkipApi
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $root

$envFile = Join-Path $root ".env.n8n-castuo"
$envExample = Join-Path $root ".env.n8n-castuo.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "Creado .env.n8n-castuo desde example — revisa secretos antes de exponer el stack."
    }
    else {
        Write-Warning "No hay .env.n8n-castuo ni .env.n8n-castuo.example; docker compose puede fallar."
    }
}

if (-not $SkipDocker) {
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCmd) {
        Write-Warning "docker no está en PATH; instala Docker Desktop o usa -SkipDocker y levanta n8n por tu cuenta."
    }
    else {
        $composeArgs = @("compose", "-f", "docker-compose.n8n-castuo.yml")
        if (Test-Path $envFile) {
            $composeArgs += @("--env-file", ".env.n8n-castuo")
        }
        $composeArgs += @("up", "-d")
        & docker @composeArgs
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Write-Host "n8n: http://localhost:5678 (ajusta si N8N_PORT en .env difiere)."
    }
}

if (-not $SkipApi) {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        Write-Error "python no está en PATH."
    }
    $apiCmd = "`$env:PYTHONPATH='.'; python -m uvicorn backend.integrations.robotics.lab_stub_app:app --host 0.0.0.0 --port $ApiPort"
    Start-Process powershell -WorkingDirectory $root -ArgumentList @("-NoExit", "-Command", $apiCmd) | Out-Null
    Write-Host "Lab API en nueva ventana: http://localhost:${ApiPort}/docs"
}
