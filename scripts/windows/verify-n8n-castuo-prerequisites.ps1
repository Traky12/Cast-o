# Verificación corpus PRONTUARIO + workflow n8n + gobernanza (pytest)
# Uso: .\scripts\windows\verify-n8n-castuo-prerequisites.ps1

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")

$prontuarios = Get-ChildItem -Path (Join-Path $root "docs") -Filter *PRONTUARIO* -Recurse -File
Write-Host "Archivos PRONTUARIO encontrados: $($prontuarios.Count)"

$workflow = Test-Path (Join-Path $root "n8n\workflows\castuo_biohub_sentinel_v2_0.json")
Write-Host "Workflow JSON existe: $workflow"
if ($workflow) {
    Get-Item (Join-Path $root "n8n\workflows\castuo_biohub_sentinel_v2_0.json") | Format-List Name, Length, LastWriteTime
}

foreach ($f in @(
        "castuo_satellite_neuro_infer_manual.json",
        "castuo_satellite_neuro_infer_webhook.json"
    )) {
    $p = Join-Path $root "n8n\workflows\$f"
    if (-not (Test-Path $p)) { Write-Warning "Falta $p" }
}

Set-Location $root
$env:PYTHONPATH = "."
python -m pytest tests/models/test_system_admin_playbook.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$labBearer = $env:CASTUO_ROBOTICS_LAB_BEARER_TOKEN
if (-not $labBearer) {
    Write-Warning "CASTUO_ROBOTICS_LAB_BEARER_TOKEN no está definido; se omitirá la verificación autenticada del lab."
}

if ($labBearer) {
    $env:CASTUO_ROBOTICS_LAB_BEARER_TOKEN = $labBearer
    python -c "import os; from fastapi.testclient import TestClient; from backend.integrations.robotics.lab_stub_app import app; c=TestClient(app); t=os.environ['CASTUO_ROBOTICS_LAB_BEARER_TOKEN']; r=c.post('/api/robotics/lab/neuromorphic/hydroponics/infer',headers={'Authorization':f'Bearer {t}'},json={'humedad':65,'ph':5.8,'ec':1.2,'luz_umol':1200}); print('infer', r.status_code)"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

try {
    $testResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/robotics/lab/neuromorphic/hydroponics/infer" `
        -Method POST `
        -Headers @{ "Authorization" = "Bearer $labBearer" } `
        -Body '{"humedad":65,"ph":5.8,"ec":1.2,"luz_umol":1200}' `
        -ContentType "application/json" `
        -ErrorAction Stop
    Write-Host "Endpoint response (HTTP vivo): $($testResponse.inference | Out-String)"
} catch {
    Write-Host "No se pudo conectar al endpoint en localhost:8000. Asegúrese de que el servicio está en ejecución."
}
}

Write-Host "Lab HTTP: uvicorn backend.integrations.robotics.lab_stub_app:app --host 0.0.0.0 --port 8000"
