#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

compose_file="docker-compose.cloud.yml"
env_file=".env.cloud.example"

fail() {
  echo "[ERROR] $*" >&2
  exit 1
}

warn() {
  echo "[WARN] $*"
}

ok() {
  echo "[OK] $*"
}

[[ -f "$compose_file" ]] || fail "No existe $compose_file"
[[ -f "$env_file" ]] || fail "No existe $env_file"

# 1) OpenClaw service must exist and be explicitly configured for secure defaults.
grep -qE '^\s*openclaw-agente:' "$compose_file" || fail "Servicio openclaw-agente no definido en $compose_file"
grep -qE '^\s*- RAG_ENABLED=true\s*$' "$compose_file" || fail "RAG_ENABLED=true es obligatorio para openclaw-agente"
grep -qE '^\s*- AI_ENGINE=\$\{AI_ENGINE:-mistral-large-latest\}\s*$' "$compose_file" || \
  fail "AI_ENGINE debe usar variable de entorno con default soberano"
grep -qE '^\s*- OPENCLAW_SOVEREIGN_MODE=\$\{OPENCLAW_SOVEREIGN_MODE:-strict\}\s*$' "$compose_file" || \
  fail "OPENCLAW_SOVEREIGN_MODE no configurado en openclaw-agente"
grep -qE '^\s*- OPENCLAW_DATA_RESIDENCY=\$\{OPENCLAW_DATA_RESIDENCY:-eu-only\}\s*$' "$compose_file" || \
  fail "OPENCLAW_DATA_RESIDENCY no configurado en openclaw-agente"
grep -qE '^\s*- OPENCLAW_ALLOWED_REGION=\$\{OPENCLAW_ALLOWED_REGION:-eu-\*\}\s*$' "$compose_file" || \
  fail "OPENCLAW_ALLOWED_REGION no configurado en openclaw-agente"

# 2) .env cloud profile must expose sovereignty knobs with secure defaults.
grep -qE '^AI_ENGINE=mistral-large-latest\s*$' "$env_file" || fail "AI_ENGINE no tiene default soberano"
grep -qE '^GAIA_X_RPC=https://[^[:space:]]+\s*$' "$env_file" || fail "GAIA_X_RPC debe usar HTTPS"
grep -qE '^OPENCLAW_SOVEREIGN_MODE=strict\s*$' "$env_file" || fail "OPENCLAW_SOVEREIGN_MODE=strict requerido"
grep -qE '^OPENCLAW_DATA_RESIDENCY=eu-only\s*$' "$env_file" || fail "OPENCLAW_DATA_RESIDENCY=eu-only requerido"
grep -qE '^OPENCLAW_ALLOWED_REGION=eu-\*\s*$' "$env_file" || fail "OPENCLAW_ALLOWED_REGION=eu-* requerido"

# 3) Optional runtime endpoint validation if provided in environment.
if [[ -n "${OPENCLAW_ENDPOINT:-}" ]]; then
  if [[ ! "${OPENCLAW_ENDPOINT}" =~ ^https:// ]]; then
    fail "OPENCLAW_ENDPOINT debe usar HTTPS"
  fi
  if [[ ! "${OPENCLAW_ENDPOINT}" =~ (\.eu|gaia-x|castuo-system\.cloud) ]]; then
    fail "OPENCLAW_ENDPOINT no parece soberano EU"
  fi
  ok "OPENCLAW_ENDPOINT validado como HTTPS/EU"
else
  warn "OPENCLAW_ENDPOINT no definido; se omite validacion runtime"
fi

ok "Validacion de soberania OpenClaw completada"