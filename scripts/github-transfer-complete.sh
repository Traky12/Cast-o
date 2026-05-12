#!/usr/bin/env bash
#
# 🚀 TRANSFERENCIA COMPLETA: CASTUO-SYSTEM → goldfish
# Script automatizado para completar los 3 pasos finales
#
# Uso:
#   bash scripts/github-transfer-complete.sh
#   bash scripts/github-transfer-complete.sh --user Traky12 --repo goldfish
#   bash scripts/github-transfer-complete.sh --dry-run
#
# Requisitos:
#   - Git instalado
#   - GitHub CLI (gh) instalado y autenticado (opcional, pero recomendado)
#   - Personal Access Token de GitHub si no usas gh
#

set -euo pipefail

# ======================== CONFIGURACIÓN ========================

GITHUB_USER="${GITHUB_USER:-Traky12}"
REPO_NAME="${REPO_NAME:-goldfish}"
COLORS=true
DRY_RUN=false
AUTO_MODE=false
PAT_PROVIDED=false
GITHUB_PAT=""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ======================== FUNCIONES ========================

log_info() { [ "$COLORS" = true ] && echo -e "${BLUE}[INFO]${NC} $*" || echo "[INFO] $*"; }
log_ok() { [ "$COLORS" = true ] && echo -e "${GREEN}[✓]${NC} $*" || echo "[OK] $*"; }
log_warn() { [ "$COLORS" = true ] && echo -e "${YELLOW}[⚠]${NC} $*" || echo "[WARN] $*"; }
log_err() { [ "$COLORS" = true ] && echo -e "${RED}[✗]${NC} $*" || echo "[ERROR] $*"; }
log_step() { [ "$COLORS" = true ] && echo -e "${CYAN}▶${NC} $*" || echo "➤ $*"; }

show_banner() {
    cat << 'EOF'

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║    🚀 TRANSFERENCIA COMPLETA: CASTUO-SYSTEM → goldfish       ║
║       Script Automatizado - 3 Pasos en 1 Comando             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

EOF
}

show_help() {
    cat << EOF
Uso:
  bash scripts/github-transfer-complete.sh [OPTIONS]

Opciones:
  --user <user>           Usuario de GitHub (default: Traky12)
  --repo <repo>           Nombre del repo (default: goldfish)
  --token <token>         Personal Access Token (si no tienes gh instalado)
  --dry-run               Simular sin hacer cambios
  --auto                  No pedir confirmación (usar defaults)
  --no-color              Deshabilitar colores
  --help                  Mostrar esta ayuda

Primeros pasos:
  # Crear repo en GitHub: https://github.com/new
  #   - Nombre: goldfish
  #   - Privado (recomendado)
  #   - SIN inicializar

  # Ejecutar:
  bash scripts/github-transfer-complete.sh

  # Si no tienes GitHub CLI:
  bash scripts/github-transfer-complete.sh --token "ghp_xxxxx"

Ejemplos:
  bash scripts/github-transfer-complete.sh
  bash scripts/github-transfer-complete.sh --auto
  bash scripts/github-transfer-complete.sh --dry-run

EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --user)
                GITHUB_USER="$2"
                shift 2
                ;;
            --repo)
                REPO_NAME="$2"
                shift 2
                ;;
            --token)
                GITHUB_PAT="$2"
                PAT_PROVIDED=true
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --auto)
                AUTO_MODE=true
                shift
                ;;
            --no-color)
                COLORS=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_err "Opción desconocida: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

confirm() {
    if [ "$AUTO_MODE" = true ]; then
        return 0
    fi

    local prompt="$1"
    read -p "$prompt (y/n): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

check_prerequisites() {
    log_step "Verificando prerequisitos..."

    # Verificar git
    if ! command -v git &>/dev/null; then
        log_err "Git no está instalado"
        exit 1
    fi
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    log_ok "Git disponible (v$GIT_VERSION)"

    # Verificar si estamos en repo git
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_err "No estamos en un repositorio git"
        exit 1
    fi
    log_ok "Repositorio git detectado"

    # Verificar GitHub CLI (opcional pero preferido)
    if command -v gh &>/dev/null; then
        GH_VERSION=$(gh --version | head -1)
        log_ok "GitHub CLI disponible ($GH_VERSION)"

        # Verificar autenticación
        if gh auth status >/dev/null 2>&1; then
            log_ok "GitHub CLI autenticado"
        else
            log_warn "GitHub CLI no autenticado. Necesitará PAT manualmente"
        fi
    else
        log_warn "GitHub CLI no disponible (no es obligatorio)"
        if [ "$PAT_PROVIDED" = false ]; then
            log_warn "Sin --token, Git solicitará credenciales"
        fi
    fi

    # Verificar que no hay cambios sin commitear
    if ! git diff --quiet || ! git diff --cached --quiet; then
        log_err "Hay cambios sin commitear. Hazlo primero:"
        echo "  git add ."
        echo "  git commit -m 'mensaje'"
        exit 1
    fi
    log_ok "Repository limpio (sin cambios pendientes)"
}

show_config() {
    echo ""
    log_step "Configuración:"
    echo "  GitHub User:    $GITHUB_USER"
    echo "  Repo Name:      $REPO_NAME"
    echo "  Remote URL:     https://github.com/$GITHUB_USER/$REPO_NAME.git"
    echo "  Current Branch: $(git branch --show-current)"
    echo "  Commits:        $(git rev-list --count HEAD)"
    if [ "$DRY_RUN" = true ]; then
        echo "  Mode:           DRY-RUN (sin cambios)"
    fi
    echo ""
}

step1_verify_remote_exists() {
    log_step "PASO 1: Verificar que repositorio existe en GitHub..."

    REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"

    if timeout 10 git ls-remote "$REMOTE_URL" >/dev/null 2>&1; then
        log_ok "Repositorio accesible: $REMOTE_URL"
    else
        log_warn "No se puede acceder a $REMOTE_URL"
        echo ""
        echo "⚠️  El repositorio podría no existir."
        echo ""
        echo "Crea el repositorio en GitHub:"
        echo "  1. Ve a: https://github.com/new"
        echo "  2. Nombre: $REPO_NAME"
        echo "  3. Visibilidad: Private"
        echo "  4. NO inicializar con README"
        echo "  5. Create repository"
        echo ""

        if ! confirm "¿Ya creaste el repositorio en GitHub?"; then
            log_info "Abre https://github.com/new y crea el repositorio, luego vuelve a ejecutar este script"
            exit 0
        fi
    fi
}

step2_configure_remote() {
    log_step "PASO 2: Configurar repositorio remoto..."

    REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"

    # Verificar si remoto ya existe
    if git remote | grep -q "^origin\$"; then
        EXISTING_URL=$(git remote get-url origin)
        if [ "$EXISTING_URL" = "$REMOTE_URL" ]; then
            log_ok "Remoto 'origin' ya está configurado correctamente"
        else
            log_warn "Remoto 'origin' apunta a URL diferente: $EXISTING_URL"
            if confirm "¿Actualizar a $REMOTE_URL?"; then
                git remote set-url origin "$REMOTE_URL"
                log_ok "URL remoto actualizada"
            fi
        fi
    else
        if [ "$DRY_RUN" = true ]; then
            log_info "DRY-RUN: git remote add origin $REMOTE_URL"
        else
            git remote add origin "$REMOTE_URL"
            log_ok "Remoto 'origin' agregado"
        fi
    fi

    # Verificar
    REMOTE_CHECK=$(git remote get-url origin 2>/dev/null || echo "")
    if [ -n "$REMOTE_CHECK" ]; then
        log_ok "Remoto configurado: $REMOTE_CHECK"
    else
        log_warn "No se pudo verificar remoto"
    fi
}

step3_push_files() {
    log_step "PASO 3: Transferir archivos a GitHub..."

    CURRENT_BRANCH=$(git branch --show-current)
    COMMIT_COUNT=$(git rev-list --count HEAD)

    echo ""
    echo "  Rama a subir:   $CURRENT_BRANCH"
    echo "  Commits:        $COMMIT_COUNT"
    echo "  Remoto:         origin ($REMOTE_URL)"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        log_info "DRY-RUN: Simulando push sin hacer cambios"
        echo ""
        echo "Comandos que se ejecutarían:"
        echo "  git push -u origin $CURRENT_BRANCH"
        return 0
    fi

    if ! confirm "¿Hacer push de '$CURRENT_BRANCH' a origin?"; then
        log_info "Push cancelado por usuario"
        return 1
    fi

    echo ""
    log_info "Haciendo push (esto puede tardar unos segundos)..."

    # Configurar credenciales si se proporciona PAT
    if [ "$PAT_PROVIDED" = true ] && [ -n "$GITHUB_PAT" ]; then
        # Usar credenciales embebidas en URL temporalmente
        SECURE_URL="https://$GITHUB_USER:$GITHUB_PAT@github.com/$GITHUB_USER/$REPO_NAME.git"
        git push -u origin "$CURRENT_BRANCH"
        if [ $? -eq 0 ]; then
            log_ok "Push completado exitosamente"
            return 0
        fi
    else
        # Push normal (Git pedirá credenciales si es necesario)
        git push -u origin "$CURRENT_BRANCH" 2>&1 | tee /tmp/git_push.log
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            log_ok "Push completado exitosamente"
            return 0
        fi
    fi

    log_err "Fallo en push. Posibles causas:"
    echo "  • Token de acceso (Personal Access Token) inválido"
    echo "  • Permisos incorrectos del usuario"
    echo "  • Conectividad de red"
    return 1
}

verify_transfer() {
    log_step "Verificando transferencia..."

    BRANCH=$(git branch --show-current)
    echo ""
    echo "✨ Ramas en remoto origin:"
    git ls-remote --heads origin 2>/dev/null | sed 's/^/  /'

    if [ "$DRY_RUN" = false ]; then
        echo ""
        echo "✅ Próximos pasos:"
        echo ""
        echo "1. 📍 Verificar archivos en GitHub:"
        echo "   https://github.com/$GITHUB_USER/$REPO_NAME/commits/$BRANCH"
        echo ""
        echo "2. 🔐 Configurar Secrets (CRÍTICO para CI/CD):"
        echo "   Settings > Secrets and variables > Actions > New"
        echo ""
        echo "   Secrets necesarios:"
        echo "   • MISTRAL_API_KEY"
        echo "   • SABIONDA_API_KEY"
        echo "   • HETZNER_TOKEN"
        echo "   • HETZNER_SSH_KEY_ID"
        echo "   • JWT_SECRET_KEY"
        echo "   • GAIACHAIN_PRIVATE_KEY"
        echo "   • DB_PASSWORD"
        echo "   • ENCRYPTION_KEY"
        echo ""
        echo "3. ⚙️  Habilitar GitHub Actions:"
        echo "   Settings > Actions > General"
        echo ""
        echo "4. 📚 Ver documentación completa:"
        echo "   GITHUB-TRANSFER.md"
        echo "   HERRAMIENTAS-INTEGRACION.md"
        echo ""
    fi
}

main() {
    show_banner
    parse_args "$@"

    check_prerequisites
    show_config

    step1_verify_remote_exists
    step2_configure_remote
    step3_push_files || exit 1

    verify_transfer

    echo ""
    log_ok "✨ Transferencia completada!"
    echo ""
}

# Ejecutar
main "$@"
