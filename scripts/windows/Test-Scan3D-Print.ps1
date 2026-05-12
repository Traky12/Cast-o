# Test-Scan3D-Print.ps1 — Scan simulado (JSON) → print job (lab stub unificado)
# Requiere: uvicorn lab_stub_app (mismo proceso que neuromorphic/snapshot).

$ErrorActionPreference = "Stop"

if (-not $env:CASTUO_ROBOTICS_LAB_BEARER_TOKEN) {
    $env:CASTUO_ROBOTICS_LAB_BEARER_TOKEN = "dev-secreto"
    Write-Warning "Usando CASTUO_ROBOTICS_LAB_BEARER_TOKEN por defecto."
}
$Base = if ($env:CASTUO_ROBOTICS_LAB_URL) { $env:CASTUO_ROBOTICS_LAB_URL.TrimEnd('/') } else { "http://127.0.0.1:8011" }
$Hdr = @{
    "Authorization" = "Bearer $($env:CASTUO_ROBOTICS_LAB_BEARER_TOKEN)"
    "Content-Type"    = "application/json; charset=utf-8"
}

Write-Host "Scan3D lab: $Base" -ForegroundColor Cyan

$scanBody = @{
    filename = "hydro_prototipo_v1.ply"
    points   = 125000
    format   = "pointcloud"
} | ConvertTo-Json -Compress

$scanResp = Invoke-RestMethod -Uri "$Base/api/robotics/lab/scan3d/scan" -Method Post -Headers $Hdr -Body $scanBody
Write-Host ("SCAN: {0} pts, {1} cm3, seal len={2}" -f $scanResp.result.mesh_points, $scanResp.result.volume_cm3, $scanResp.chain_seal.Length) -ForegroundColor Green

$vol = $scanResp.result.volume_cm3
$printBody = @{
    scan_id           = "scan_20260322_0153"
    printer_model     = "Bambu Lab H2D"
    infill            = 25
    layer_height      = 0.2
    material          = "PLA+"
    nozzle_temp       = 220
    volume_cm3        = $vol
    apply_neuro_hints = $true
} | ConvertTo-Json -Compress

$printResp = Invoke-RestMethod -Uri "$Base/api/robotics/lab/scan3d/print" -Method Post -Headers $Hdr -Body $printBody
Write-Host ("PRINT: {0} h, {1} g, neuro infill hint={2}" -f $printResp.print_job.print_time_h, $printResp.print_job.material_usage_g, $printResp.neuro_hints.infill) -ForegroundColor Cyan
Write-Host "Scan-to-Print lab OK (sin GCode binario ni OctoPrint en este paso)." -ForegroundColor Green
