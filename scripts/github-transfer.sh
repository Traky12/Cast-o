#!/usr/bin/env bash
#
# GitHub Transfer Script: CASTUO-SYSTEM → goldfish
# Automatización completa de transferencia a nuevo repositorio
#
# Uso:
#   bash scripts/github-transfer.sh [--user <user>] [--repo <repo>] [--dry-run]
#
# Ejemplos:
#   bash scripts/github-transfer.sh                    # Usar defaults (Traky12/goldfish)
#   bash scripts/github-transfer.sh --user myuser      # User personalizado
#   bash scripts/github-transfer.sh --repo mynewrepo   # Repo personalizado
#   bash scripts/github-transfer.sh --dry-run          # Simular sin hacer push
#

set -euo pipefail

# ============================== CONFIGURACIÓN ==============================

GITHUB_USER="${GITHUB_USER:-Traky12}"
REPO_NAME="${REPO_NAME:-goldfish}"
DRY_RUN=false
REMOTE_NAME="goldfish"
COLORS_ENABLED=true

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# ============================== FUNCIONES ==============================

log_info() {
    if [ "$COLORS_ENABLED" = true ]; then
        echo -e "${BLUE}[INFO]${NC} $*"
    else
        echo "[INFO] $*"
    fi
}

log_success() {
    if [ "$COLORS_ENABLED" = true ]; then
        echo -e "${GREEN}[✓]${NC} $*"
    else
        echo "[OK] $*"
    fi
}

log_warn() {
    if [ "$COLORS_ENABLED" = true ]; then
        echo -e "${YELLOW}[⚠]${NC} $*"
    else
        echo "[WARN] $*"
    fi
}

log_error() {
    if [ "$COLORS_ENABLED" = true ]; then
        echo -e "${RED}[✗]${NC} $*"
    else
        echo "[ERROR] $*"
    fi
}

show_usage() {
    cat <<EOF
Uso: $(basename "$0") [OPTIONS]

Opciones:
  --user <user>         Usuario de GitHub (default: $GITHUB_USER)
  --repo <repo>         Nombre del repo (default: $REPO_NAME)
  --dry-run             Simular sin hacer push efectivo
  --no-color            Deshabilitar colores en output
  --help                Mostrar esta ayuda y salir

Ejemplos:
  bash scripts/github-transfer.sh
  bash scripts/github-transfer.sh --user myuser --repo mynewrepo
  bash scripts/github-transfer.sh --dry-run

Requisitos:
  • Git instalado y configurado
  • Acceso a GitHub (SSH o HTTPS con token)
  • Repositorio local ya inicializado
  • Conexión a internet

EOF
}

# Parse command-line arguments
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
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --no-color)
                COLORS_ENABLED=false
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Opción desconocida: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Verificar prerequisitos
check_prerequisites() {
    log_info "Verificando prerequisitos..."

    # Verificar git
    if ! command -v git &>/dev/null; then
        log_error "Git no está instalado"
        exit 1
    fi
    log_success "Git encontrado: $(git --version)"

    # Verificar que estamos en repo git
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "No estamos en un repositorio git"
        exit 1
    fi
    log_success "Repo git detectado"

    # Verificar que hay commits
    if ! git rev-parse HEAD >/dev/null 2>&1; then
        log_error "Repositorio git vacío (sin commits)"
        exit 1
    fi
    CURRENT_BRANCH=$(git branch --show-current)
    COMMIT_COUNT=$(git rev-list --count HEAD)
    log_success "Rama actual: $CURRENT_BRANCH ($COMMIT_COUNT commits)"

    # Verificar que no hay cambios sin commitear
    if ! git diff --quiet || ! git diff --cached --quiet; then
        log_warn "Hay cambios sin commitear. Considera hacer commit antes."
        read -p "¿Continuar de todas formas? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Transferencia cancelada"
            exit 0
        fi
    fi
}

# Mostrar configuración
show_config() {
    log_info "Configuración de transferencia:"
    echo "  GitHub User:  $GITHUB_USER"
    echo "  Repo Name:    $REPO_NAME"
    echo "  Remote URL:   https://github.com/$GITHUB_USER/$REPO_NAME.git"
    echo "  Current Branch: $CURRENT_BRANCH"
    echo "  Commits Total: $COMMIT_COUNT"
    if [ "$DRY_RUN" = true ]; then
        echo "  Mode:         DRY-RUN (sin escribir cambios)"
    fi
    echo ""
}

# Verificar conexión
check_connectivity() {
    log_info "Verificando conectividad con GitHub..."

    REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"

    # Probar conexión (sin auth requerida para ver si repo existe)
    if timeout 5 git ls-remote "$REMOTE_URL" >/dev/null 2>&1; then
        log_success "Repositorio accesible: $REMOTE_URL"
        return 0
    else
        log_warn "No se puede acceder a $REMOTE_URL"
        log_info "¿El repositorio existe en GitHub?"
        read -p "¿Continuar de todas formas? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Transferencia cancelada"
            exit 0
        fi
    fi
}

# Añadir remoto
add_remote() {
    log_info "Configurando remoto '$REMOTE_NAME'..."

    REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"

    # Verificar si remoto ya existe
    if git remote | grep -q "^$REMOTE_NAME\$"; then
        log_warn "Remoto '$REMOTE_NAME' ya existe"
        EXISTING_URL=$(git remote get-url "$REMOTE_NAME")
        echo "  URL actual: $EXISTING_URL"

        if [ "$EXISTING_URL" != "$REMOTE_URL" ]; then
            read -p "¿Actualizar URL? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git remote set-url "$REMOTE_NAME" "$REMOTE_URL"
                log_success "URL remoto actualizada"
            fi
        fi
    else
        git remote add "$REMOTE_NAME" "$REMOTE_URL"
        log_success "Remoto '$REMOTE_NAME' añadido"
    fi

    # Verificar
    git remote -v | grep "$REMOTE_NAME" || log_error "Fallo al añadir remoto"
}

# Hacer push
do_push() {
    log_info "Preparando push..."

    REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"
    BRANCH_TO_PUSH="${CURRENT_BRANCH}"

    echo "  Remoto:    $REMOTE_NAME"
    echo "  URL:       $REMOTE_URL"
    echo "  Rama:      $BRANCH_TO_PUSH"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        log_info "DRY-RUN: Simulando push sin escribir cambios"
        echo "Command que se ejecutaría:"
        echo "  git push -u $REMOTE_NAME $BRANCH_TO_PUSH"
        return 0
    fi

    read -p "¿Hacer push de '${BRANCH_TO_PUSH}' a '$REMOTE_NAME'? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Push cancelado por usuario"
        return 1
    fi

    log_info "Haciendo push (esto puede tardar unos segundos)..."

    if git push -u "$REMOTE_NAME" "$BRANCH_TO_PUSH"; then
        log_success "Push completado exitosamente"
        return 0
    else
        log_error "Fallo en push. Verifica:"
        echo "  • Token de acceso (Personal Access Token en GitHub)"
        echo "  • Permisos del usuario '$GITHUB_USER'"
        echo "  • Conectividad de red"
        return 1
    fi
}

# Verificación final
verify_transfer() {
    log_info "Verificando transferencia..."

    # Listar ramas en remoto
    log_info "Ramas en remoto $REMOTE_NAME:"
    git ls-remote --heads "$REMOTE_NAME" | sed 's/^/  /'

    if [ "$DRY_RUN" = false ]; then
        echo ""
        echo "✨ Próximos pasos:"
        echo "  1. Ve a: https://github.com/$GITHUB_USER/$REPO_NAME/commits/$CURRENT_BRANCH"
        echo "  2. Verifica que los archivos estén presentes"
        echo "  3. Configura GitHub Secrets en: Settings > Secrets and variables > Actions"
        echo "  4. Habilita GitHub Actions si es necesario"
        echo "  5. Ver: GITHUB-TRANSFER.md para pasos post-transferencia"
    fi
}

# Main
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  GitHub Transfer: CASTUO-SYSTEM → goldfish                ║"
    echo "║  Script automatizado v1.0                                  ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    parse_args "$@"
    check_prerequisites
    show_config

    check_connectivity
    add_remote

    if do_push; then
        log_success "Transferencia completada"
        verify_transfer
    else
        log_error "Transferencia falló"
        exit 1
    fi

    echo ""
}

# Ejecutar
main "$@"
