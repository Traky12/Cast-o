# Empaquetado CASTUO_GOLD_V1.zip (raíz del repo Castuo-System)
# Excluir manualmente venv/node_modules si existen bajo docs/contracts
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$dest = Join-Path $root "CASTUO_GOLD_V1.zip"
if (Test-Path $dest) { Remove-Item $dest -Force }
$items = @(
    "SYSTEM_PROMPT.md", "SUMMARY.md", "FINAL_VALIDATION_REPORT.md",
    "SABIONDA-AUTH-V1.cert", "SABIONDA_FINAL_RELEASE.log",
    "castuo_manifest", "contracts", "docs", ".cursor"
)
Compress-Archive -Path ($items | ForEach-Object { Join-Path $root $_ }) -DestinationPath $dest -Force
Write-Host "Generado: $dest"
Get-FileHash $dest -Algorithm SHA256 | Format-List
