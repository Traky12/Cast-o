param(
    [string]$RepoPath = "C:\Users\traky\Castuo-system",
    [string]$Branch = "feat/excelencia-operativa",
    [string]$CommitMessage = "chore: update local changes and start api",
    [switch]$SkipInstall,
    [switch]$NoReload,
    [switch]$NoGpgSign,
    [switch]$SkipPush,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Test-CommandAvailable {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandAvailable git)) {
    throw "git no está disponible en PATH. Instala Git for Windows antes de continuar."
}

if (-not (Test-CommandAvailable powershell)) {
    throw "PowerShell no está disponible."
}

$startScript = Join-Path $PSScriptRoot "Start-Castuo-API.ps1"
if (-not (Test-Path $startScript)) {
    throw "No se encontró Start-Castuo-API.ps1 en $PSScriptRoot"
}

Write-Step "Preparando repositorio en $RepoPath"
if (-not (Test-Path $RepoPath)) {
    throw "La ruta del repositorio no existe: $RepoPath. Ejecuta primero Start-Castuo-API.ps1 o clona el repo."
}

Set-Location $RepoPath

if (-not (Test-Path ".git")) {
    throw "La ruta $RepoPath no es un repositorio Git válido."
}

Write-Step "Sincronizando rama $Branch"
git fetch origin
$null = git checkout $Branch

Write-Step "Revisando cambios locales"
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Warn "No hay cambios locales para commitear. Se omitirá add/commit."
} else {
    Write-Step "Haciendo git add -A"
    git add -A

    $commitArgs = @("commit", "-m", $CommitMessage)
    if ($NoGpgSign) {
        $commitArgs = @("commit", "--no-gpg-sign", "-m", $CommitMessage)
    }

    Write-Step "Creando commit"
    try {
        & git @commitArgs
        Write-Ok "Commit creado correctamente"
    }
    catch {
        throw "Falló el commit. Revisa user.name, user.email y firma GPG si aplica."
    }
}

if (-not $SkipPush) {
    Write-Step "Haciendo push a origin/$Branch"
    git push origin $Branch
    Write-Ok "Push completado"
} else {
    Write-Warn "SkipPush activado. No se hará push."
}

Write-Step "Arrancando API reutilizando Start-Castuo-API.ps1"
$startArgs = @(
    "-ExecutionPolicy", "Bypass",
    "-File", $startScript,
    "-RepoPath", $RepoPath,
    "-Branch", $Branch,
    "-Port", $Port
)
if ($SkipInstall) {
    $startArgs += "-SkipInstall"
}
if ($NoReload) {
    $startArgs += "-NoReload"
}

& powershell @startArgs
