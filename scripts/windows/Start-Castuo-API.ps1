param(
    [string]$RepoPath = "C:\Users\traky\Castuo-system",
    [string]$Branch = "feat/excelencia-operativa",
    [switch]$SkipInstall,
    [switch]$NoReload,
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

function Find-GitRepository {
    param([string]$BasePath)

    $gitDirs = Get-ChildItem $BasePath -Force -Recurse -Directory -Filter .git -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty FullName

    foreach ($gitDir in $gitDirs) {
        $repoRoot = Split-Path $gitDir -Parent
        if (Test-Path (Join-Path $repoRoot "api\main.py")) {
            return $repoRoot
        }
    }

    return $null
}

if (-not (Test-CommandAvailable git)) {
    throw "git no está disponible en PATH. Instala Git for Windows antes de continuar."
}

if (-not (Test-CommandAvailable python)) {
    throw "python no está disponible en PATH. Instala Python 3 antes de continuar."
}

Write-Step "Resolviendo ruta del repositorio"
if (-not (Test-Path $RepoPath)) {
    $parentPath = Split-Path $RepoPath -Parent
    if (-not (Test-Path $parentPath)) {
        New-Item -ItemType Directory -Path $parentPath -Force | Out-Null
    }

    Write-Step "El repositorio no existe en $RepoPath. Clonando..."
    git clone https://github.com/Traky12/Castuo-system.git $RepoPath
}

$resolvedRepo = $RepoPath
if (-not (Test-Path (Join-Path $resolvedRepo ".git"))) {
    Write-Warn "No se encontró .git en $resolvedRepo. Buscando repositorio válido con api\\main.py..."
    $foundRepo = Find-GitRepository -BasePath (Split-Path $resolvedRepo -Parent)
    if ($null -eq $foundRepo) {
        throw "No se encontró un repositorio Git válido de Castuo-system cerca de $resolvedRepo"
    }
    $resolvedRepo = $foundRepo
}

Set-Location $resolvedRepo
Write-Ok "Repositorio activo: $resolvedRepo"

Write-Step "Verificando estructura esperada"
if (-not (Test-Path ".\api\main.py")) {
    throw "No existe api\\main.py en $resolvedRepo. Esta no es la raíz correcta del proyecto."
}

Write-Step "Sincronizando rama $Branch"
git fetch origin
git checkout $Branch
git pull origin $Branch

$venvPython = Join-Path $resolvedRepo ".venv\Scripts\python.exe"
$venvActivate = Join-Path $resolvedRepo ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $venvPython)) {
    Write-Step "Creando entorno virtual en .venv"
    python -m venv .venv
}

if (-not (Test-Path $venvActivate)) {
    throw "No se pudo crear correctamente el entorno virtual en .venv"
}

Write-Step "Activando entorno virtual"
. $venvActivate

if (-not $SkipInstall) {
    Write-Step "Actualizando pip e instalando dependencias de la API"
    python -m pip install --upgrade pip
    pip install -r .\api\requirements.txt
}

Write-Step "Mostrando estado Git"
git status --short

$reloadFlag = "--reload"
if ($NoReload) {
    $reloadFlag = ""
}

Write-Ok "Arrancando API correcta: api.main:app"
Write-Host "" 
Write-Host "Comando equivalente:" -ForegroundColor DarkGray
Write-Host "python -m uvicorn api.main:app --host 0.0.0.0 --port $Port $reloadFlag" -ForegroundColor DarkGray
Write-Host ""

if ([string]::IsNullOrWhiteSpace($reloadFlag)) {
    python -m uvicorn api.main:app --host 0.0.0.0 --port $Port
} else {
    python -m uvicorn api.main:app --host 0.0.0.0 --port $Port --reload
}