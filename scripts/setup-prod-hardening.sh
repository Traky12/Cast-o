#!/usr/bin/env bash

set -u

REPO_OWNER="Traky12"
REPO_NAME="Castuo-system"
REPO="${REPO_OWNER}/${REPO_NAME}"
BRANCH="main"

CHECKS=(
  "Preflight de robustez"
  "Exportar metricas de sincronizacion"
  "Prueba de caos (drift simulation)"
  "Checklist Sabionda"
  "Certify Operativity TRL9 ON/OFF"
)

REQUIRED_SECRETS=(
  "SABIONDA_API_KEY"
  "SABIONDA_AUTH_HEALTH_URL"
  "MISTRAL_API_KEY"
  "PUSHGATEWAY_URL"
  "OPENCLAW_ENDPOINT"
)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
log_ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
log_err()  { echo -e "${RED}[ERROR]${NC} $*"; }

HAS_ERROR=0

is_truthy() {
  local value="${1:-}"
  case "${value,,}" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log_err "Comando requerido no encontrado: $1"
    HAS_ERROR=1
    return 1
  fi
}

login_if_needed() {
  if gh auth status >/dev/null 2>&1; then
    log_ok "gh autenticado"
    return 0
  fi

  if [[ -n "${GH_TOKEN:-}" ]]; then
    log_info "Intentando login con GH_TOKEN"
    if gh auth login --with-token <<<"${GH_TOKEN}" >/dev/null 2>&1; then
      log_ok "Login con GH_TOKEN completado"
      return 0
    fi
  fi

  log_err "No hay autenticacion gh activa. Define GH_TOKEN o ejecuta: gh auth login"
  HAS_ERROR=1
  return 1
}

prompt_pat_if_needed() {
  if gh auth status >/dev/null 2>&1; then return 0; fi
  if [[ -n "${GH_TOKEN:-}" ]]; then return 0; fi

  echo -e "\n${YELLOW}No hay sesion gh activa.${NC}"
  echo "Genera un PAT en: https://github.com/settings/personal-access-tokens/new"
  echo "  - Repositorio: ${REPO}"
  echo "  - Permiso: Administration -> Read and write"
  echo ""
  read -r -s -p "Pega tu PAT (entrada oculta): " _pat
  echo ""
  if [[ -z "${_pat}" ]]; then
    log_err "No se proporcionó PAT. Abortando."
    exit 1
  fi
  export GH_TOKEN="${_pat}"
  unset _pat
}

prompt_pat_for_admin() {
  if [[ -n "${GH_TOKEN:-}" ]]; then
    return 0
  fi

  echo ""
  echo "Se requiere un PAT con Administration: Read and write para aplicar branch protection."
  read -r -s -p "Pega tu PAT de administrador (entrada oculta): " _pat
  echo ""
  if [[ -z "${_pat}" ]]; then
    log_err "No se proporcionó PAT de administrador."
    return 1
  fi
  export GH_TOKEN="${_pat}"
  unset _pat
}

force_login_with_token() {
  if [[ -z "${GH_TOKEN:-}" ]]; then
    log_err "GH_TOKEN no definido para login con token"
    return 1
  fi

  if gh auth login --with-token <<<"${GH_TOKEN}" >/dev/null 2>&1; then
    log_ok "Login con PAT completado"
    return 0
  fi

  log_err "No se pudo autenticar gh con el PAT proporcionado"
  return 1
}

set_secret_if_present() {
  local name="$1"
  local value="${!name:-}"

  if [[ -z "${value}" ]]; then
    log_info "Secret no provisto en entorno: ${name} (se mantiene como pendiente)"
    return 1
  fi

  if gh secret set "${name}" --repo "${REPO}" --body "${value}" >/dev/null 2>&1; then
    log_ok "Secret configurado: ${name}"
    return 0
  fi

  log_err "No se pudo configurar secret: ${name}"
  HAS_ERROR=1
  return 1
}

apply_branch_protection() {
  local payload
  payload=$(cat <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Preflight de robustez",
      "Exportar metricas de sincronizacion",
      "Prueba de caos (drift simulation)",
      "Checklist Sabionda"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
JSON
)

  log_info "Aplicando branch protection en ${REPO}:${BRANCH}"
  local api_out
  if api_out=$(gh api --method PUT \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "repos/${REPO}/branches/${BRANCH}/protection" \
    --input - <<<"${payload}" 2>&1); then
    log_ok "Branch protection aplicada"
    return 0
  fi

  if grep -Eqi "403|Resource not accessible by integration|must have admin rights|administration" <<<"${api_out}"; then
    log_err "Permisos insuficientes para branch protection"
    return 2
  fi

  log_err "No se pudo aplicar branch protection"
  return 1
}

verify_branch_protection() {
  local response
  if ! response=$(gh api "repos/${REPO}/branches/${BRANCH}/protection" 2>/dev/null); then
    log_err "No se pudo leer branch protection para verificacion"
    HAS_ERROR=1
    return 1
  fi

  local check
  for check in "${CHECKS[@]}"; do
    if grep -Fq "${check}" <<<"${response}"; then
      log_ok "Check presente: ${check}"
    else
      log_err "Check ausente: ${check}"
      HAS_ERROR=1
    fi
  done
}

verify_secrets() {
  local list
  if ! list=$(gh secret list --repo "${REPO}" 2>/dev/null); then
    log_err "No se pudo listar secrets del repositorio"
    HAS_ERROR=1
    return 1
  fi

  local s
  for s in "${REQUIRED_SECRETS[@]}"; do
    if grep -q "^${s}[[:space:]]" <<<"${list}"; then
      log_ok "Secret presente: ${s}"
    else
      log_err "Secret faltante: ${s}"
      HAS_ERROR=1
    fi
  done
}

main() {
  echo -e "\n${YELLOW}===== CONFIGURACION PRODUCCION (GO/NO-GO) =====${NC}"

  if ! is_truthy "${REQUIRE_GITHUB_HARDENING:-0}"; then
    log_info "Modo desacoplado activo: se omite dependencia operativa de GitHub"
    log_info "Para forzar hardening GitHub exporta REQUIRE_GITHUB_HARDENING=1"
    echo
    log_ok "GO: sistema procesable sin conexion obligatoria a GitHub"
    exit 0
  fi

  require_cmd gh || true

  prompt_pat_if_needed
  login_if_needed || true

  log_info "Configurando secrets disponibles desde variables de entorno"
  for s in "${REQUIRED_SECRETS[@]}"; do
    set_secret_if_present "${s}" || true
  done

  apply_branch_protection
  bp_rc=$?
  if [[ "${bp_rc}" -eq 2 ]]; then
    log_info "Intentando reautenticacion con PAT de administrador para reintento"
    prompt_pat_for_admin || HAS_ERROR=1
    force_login_with_token || HAS_ERROR=1
    if ! apply_branch_protection; then
      HAS_ERROR=1
    fi
  elif [[ "${bp_rc}" -ne 0 ]]; then
    HAS_ERROR=1
  fi

  verify_branch_protection || true
  verify_secrets || true

  if [[ "${HAS_ERROR}" -eq 0 ]]; then
    echo
    log_ok "GO: repositorio en estado listo para modo produccion"
    exit 0
  fi

  echo
  log_err "NO-GO: faltan permisos y/o configuraciones por completar"
  echo "Sugerencia: exporta GH_TOKEN con permisos de Administration y define los 5 secrets requeridos."
  exit 1
}

main "$@"
