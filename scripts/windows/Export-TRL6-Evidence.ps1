# Export-TRL6-Evidence.ps1 — JUnit + manifiesto JSON verificable (gate trl6)
# Ejecutar desde cualquier cwd; usa raíz del repo automáticamente.

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$outDir = Join-Path $root "reports\trl6"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Set-Location $root
$env:PYTHONPATH = $root

$junit = Join-Path $outDir "junit.xml"
$console = Join-Path $outDir "pytest-console.txt"
$manifest = Join-Path $outDir "manifest.json"

Write-Host "[TRL6 evidence] pytest -m trl6 -> $junit" -ForegroundColor Cyan
$pytestArgs = @("-m", "trl6", "-q", "--junit-xml=$junit")
& python -m pytest @pytestArgs 2>&1 | Tee-Object -FilePath $console
$exitCode = $LASTEXITCODE

$gitCommit = $null
try {
    Push-Location $root
    $gitCommit = (git rev-parse HEAD 2>$null).Trim()
    if (-not $gitCommit) { $gitCommit = $null }
} catch { }
finally { Pop-Location }

$pyVer = (python -c "import sys; print('%d.%d.%d' % sys.version_info[:3])" 2>$null).Trim()

$obj = [ordered]@{
    schema            = "castuo.trl6_evidence.v1"
    generated_at_utc  = (Get-Date).ToUniversalTime().ToString("o")
    repository_root   = $root
    git_commit        = $gitCommit
    python            = $pyVer
    pytest_marker     = "trl6"
    pytest_exit_code  = $exitCode
    artifacts         = @{
        junit_xml     = "reports/trl6/junit.xml"
        console_log   = "reports/trl6/pytest-console.txt"
    }
    legal_note        = "Artefactos de prueba; no sustituyen DPIA ni firma DPO. Ver docs/legal/INFORME-EVIDENCIA-TRL6-PLANTILLA.md"
}
($obj | ConvertTo-Json -Depth 6) | Set-Content -Path $manifest -Encoding UTF8

Write-Host "[TRL6 evidence] manifest -> $manifest (exit=$exitCode)" -ForegroundColor $(if ($exitCode -eq 0) { "Green" } else { "Red" })
exit $exitCode
