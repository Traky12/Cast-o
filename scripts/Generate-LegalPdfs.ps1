<#
.SYNOPSIS
    Genera documentos legales en PDF y Word desde Markdown.
.DESCRIPTION
    Convierte los .md de docs/legal/TRL10 a PDF y DOCX con Pandoc.
    Requiere Pandoc y un motor PDF (pdflatex recomendado).
.NOTES
    Version: 1.0
    Autor: Gregorio Jimenez Bodes
    Fecha: 20/03/2026
#>

[CmdletBinding()]
param(
    [string]$InputDir = "docs\legal\TRL10",
    [string]$OutputDir = "docs\legal\TRL10\pdfs",
    [string]$PandocPath = "pandoc",
    [string]$TemplateDocx = "scripts\legal_template.docx"
)

$ErrorActionPreference = "Stop"

function Write-Info([string]$Message) { Write-Host $Message -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host $Message -ForegroundColor Green }
function Write-WarnMsg([string]$Message) { Write-Host $Message -ForegroundColor Yellow }
function Write-ErrMsg([string]$Message) { Write-Host $Message -ForegroundColor Red }

if (-not (Test-Path -Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Ok "Directorio de salida creado: $OutputDir"
}

if (-not (Get-Command $PandocPath -ErrorAction SilentlyContinue)) {
    Write-ErrMsg "ERROR: Pandoc no esta instalado o no esta en PATH."
    Write-WarnMsg "Instala Pandoc desde: https://pandoc.org/installing.html"
    exit 1
}

if (-not (Get-Command "pdflatex" -ErrorAction SilentlyContinue)) {
    Write-WarnMsg "No se encontro pdflatex en PATH. Los PDF pueden fallar."
}

if (-not (Test-Path -Path $TemplateDocx)) {
    Write-Info "Creando plantilla Word base..."
    try {
        Invoke-WebRequest `
            -Uri "https://github.com/pandoc/lua-filters/raw/master/templates/template.docx" `
            -OutFile $TemplateDocx
        Write-Ok "Plantilla Word descargada en $TemplateDocx"
    } catch {
        Write-WarnMsg "No se pudo descargar plantilla. Generando una minima con Pandoc."
        $tmpMd = Join-Path $env:TEMP "legal_template_tmp.md"
        "Plantilla legal CASTUO-SYSTEM" | Out-File -FilePath $tmpMd -Encoding utf8
        & $PandocPath $tmpMd -o $TemplateDocx
        Remove-Item $tmpMd -ErrorAction SilentlyContinue
    }
}

$files = Get-ChildItem -Path $InputDir -Filter "*.md" -File -ErrorAction SilentlyContinue
if (-not $files -or $files.Count -eq 0) {
    Write-WarnMsg "No se encontraron archivos .md en $InputDir"
    exit 0
}

foreach ($fileObj in $files) {
    $file = $fileObj.FullName
    $baseName = $fileObj.BaseName
    $pdfOutput = Join-Path -Path $OutputDir -ChildPath "$baseName.pdf"
    $docxOutput = Join-Path -Path $OutputDir -ChildPath "$baseName.docx"

    Write-Info "Generando PDF para $baseName..."
    & $PandocPath `
        "$file" `
        -o "$pdfOutput" `
        --pdf-engine=pdflatex `
        --variable=geometry:margin=1in `
        --variable=fontsize:12pt
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "PDF generado: $pdfOutput"
    } else {
        Write-ErrMsg "ERROR al generar PDF para $file"
    }

    Write-Info "Generando Word para $baseName..."
    & $PandocPath "$file" -o "$docxOutput" --reference-doc="$TemplateDocx"
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Word generado: $docxOutput"
    } else {
        Write-WarnMsg "No se pudo generar Word para $file"
    }
}

$pdfCount = (Get-ChildItem -Path $OutputDir -Filter "*.pdf" -File -ErrorAction SilentlyContinue | Measure-Object).Count
$docxCount = (Get-ChildItem -Path $OutputDir -Filter "*.docx" -File -ErrorAction SilentlyContinue | Measure-Object).Count

Write-Ok ""
Write-Ok "Todos los documentos legales han sido generados en $OutputDir"
Write-Ok "- PDFs: $pdfCount archivos"
Write-Ok "- Word: $docxCount archivos"

