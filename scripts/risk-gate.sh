#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

has_error=0

ok()   { echo "[OK] $*"; }
warn() { echo "[WARN] $*"; }
err()  { echo "[ERROR] $*"; has_error=1; }

check_file_contains() {
  local file="$1"
  local pattern="$2"
  grep -Eq "$pattern" "$file"
}

echo "[INFO] Risk gate iniciado"

# 1) Puertos de alto riesgo en firewall IaC
if [[ -f "hetzner_infra/main.tf" ]]; then
  if check_file_contains "hetzner_infra/main.tf" 'port\s*=\s*"(3306|5432|6379|27017|6443|9200|5601)"'; then
    err "Firewall IaC expone puertos sensibles (3306/5432/6379/27017/6443/9200/5601)."
  else
    ok "Firewall IaC sin puertos sensibles expuestos."
  fi
else
  warn "No existe hetzner_infra/main.tf; se omite chequeo de puertos IaC."
fi

# 2) n8n debe permanecer en 5678 (nunca 5432)
if [[ -f "docker-compose.yml" ]]; then
  if check_file_contains "docker-compose.yml" '"5432:5678"'; then
    err "Configuracion invalida: n8n mapeado a 5432 detectado en docker-compose.yml."
  elif check_file_contains "docker-compose.yml" '"5678:5678"'; then
    ok "Puerto n8n correcto (5678:5678)."
  else
    warn "No se detecto mapping 5678:5678; revisar compose de n8n."
  fi
fi

# 3) Secretos placeholder en ficheros de entorno
critical_env_vars=(
  HETZNER_API_KEY
  GAIACHAIN_API_KEY
  IPFS_API_KEY
  MISTRAL_API_KEY
  SABIONDA_API_KEY
  N8N_API_KEY
  N8N_PASSWORD
  JWT_SECRET_KEY
  WEBHOOK_URL
  GAIA_CHAIN_PRIVATE_KEY_FILE
)

env_files_raw="${RISK_GATE_ENV_FILES:-.env .env.cloud}"
read -r -a env_files <<< "$env_files_raw"

for env_file in "${env_files[@]}"; do
  if [[ -f "$env_file" ]]; then
    found_placeholder=0
    for key in "${critical_env_vars[@]}"; do
      line="$(grep -E "^${key}=" "$env_file" 2>/dev/null | head -n 1 || true)"
      [[ -z "$line" ]] && continue
      value="${line#*=}"
      if [[ "$value" == "<CHANGE_ME>" || "$value" == "CHANGE_ME" || "$value" == '"<CHANGE_ME>"' || "$value" == '"CHANGE_ME"' ]]; then
        err "Placeholder detectado en variable critica ${key} de ${env_file}."
        found_placeholder=1
      fi
    done
    if [[ "$found_placeholder" -eq 0 ]]; then
      ok "$env_file sin placeholders criticos."
    fi
  fi
done

# 4) Permisos de carpeta secrets (si existe)
if [[ -d "secrets" ]]; then
  # Ficheros de secretos no deben ser world/group writable.
  insecure_files=$(find secrets -type f -perm /022 2>/dev/null || true)
  if [[ -n "$insecure_files" ]]; then
    err "Permisos inseguros en secrets/:\n$insecure_files"
  else
    ok "Permisos de secrets/ sin escritura para group/others."
  fi
fi

# 5) Script remoto debe usar SSH no interactivo para CI/CD
if [[ -f "scripts/connect-and-deploy.sh" ]]; then
  if check_file_contains "scripts/connect-and-deploy.sh" 'BatchMode=yes'; then
    ok "connect-and-deploy usa SSH no interactivo (BatchMode=yes)."
  else
    err "connect-and-deploy no usa BatchMode=yes; puede bloquear pipelines."
  fi
fi

if [[ "$has_error" -eq 1 ]]; then
  echo "[ERROR] Risk gate NO-GO"
  exit 1
fi

echo "[OK] Risk gate GO"