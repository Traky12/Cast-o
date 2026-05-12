#!/usr/bin/env bash
set -euo pipefail

# Despliegue base en Hetzner Cloud para CASTUO-SYSTEM.
# Mantiene trazabilidad operativa y minimiza riesgo de errores manuales.

PROJECT_NAME="castuo-system"
SERVER_NAME="${SERVER_NAME:-castuo-prod-1}"
SERVER_TYPE="${SERVER_TYPE:-cx21}"
SERVER_LOCATION="${SERVER_LOCATION:-fsn1}"
IMAGE_NAME="${IMAGE_NAME:-ubuntu-22.04}"
FIREWALL_NAME="${FIREWALL_NAME:-castuo-fw}"
DOMAIN_NAME="${DOMAIN_NAME:-tu-dominio.com}"
CONTACT_EMAIL="${CONTACT_EMAIL:-admin@castuo-system.com}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"
SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/id_rsa.pub}"
HETZNER_API_TOKEN="${HETZNER_API_TOKEN:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
  local level="$1"
  local message="$2"
  local timestamp
  timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
  case "$level" in
    INFO) echo -e "[${timestamp}] ${GREEN}[INFO]${NC} ${message}" ;;
    WARN) echo -e "[${timestamp}] ${YELLOW}[WARN]${NC} ${message}" ;;
    ERROR) echo -e "[${timestamp}] ${RED}[ERROR]${NC} ${message}" ;;
    *) echo "[${timestamp}] [LOG] ${message}" ;;
  esac
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { log ERROR "Falta comando requerido: $1"; exit 1; }
}

validate_env() {
  require_cmd curl
  require_cmd jq
  require_cmd ssh
  if [[ -z "${HETZNER_API_TOKEN}" ]]; then
    log ERROR "Define HETZNER_API_TOKEN en el entorno antes de ejecutar."
    exit 1
  fi
  if [[ ! -f "${SSH_KEY_PATH}" ]]; then
    log ERROR "No se encontro la clave publica SSH en ${SSH_KEY_PATH}."
    exit 1
  fi
}

api() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  if [[ -n "${body}" ]]; then
    curl -sS -X "${method}" "https://api.hetzner.cloud/v1/${path}" \
      -H "Authorization: Bearer ${HETZNER_API_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "${body}"
  else
    curl -sS -X "${method}" "https://api.hetzner.cloud/v1/${path}" \
      -H "Authorization: Bearer ${HETZNER_API_TOKEN}"
  fi
}

ensure_firewall() {
  log INFO "Asegurando firewall ${FIREWALL_NAME}..."
  local fw_id
  fw_id="$(api GET "firewalls" | jq -r --arg name "${FIREWALL_NAME}" '.firewalls[]? | select(.name==$name) | .id' | head -n 1)"
  local rules
  rules='[
    {"direction":"in","protocol":"tcp","port":"22","source_ips":["0.0.0.0/0","::/0"]},
    {"direction":"in","protocol":"tcp","port":"80","source_ips":["0.0.0.0/0","::/0"]},
    {"direction":"in","protocol":"tcp","port":"443","source_ips":["0.0.0.0/0","::/0"]},
    {"direction":"in","protocol":"icmp","source_ips":["0.0.0.0/0","::/0"]}
  ]'
  if [[ -z "${fw_id}" ]]; then
    fw_id="$(api POST "firewalls" "$(jq -n --arg n "${FIREWALL_NAME}" --argjson r "${rules}" '{name:$n, rules:$r}')" | jq -r '.firewall.id')"
  else
    api POST "firewalls/${fw_id}/actions/set_rules" "$(jq -n --argjson r "${rules}" '{rules:$r}')" >/dev/null
  fi
  echo "${fw_id}" > .hetzner_fw_id
  log INFO "Firewall listo (id=${fw_id})."
}

create_server() {
  log INFO "Creando servidor ${SERVER_NAME}..."
  local public_key
  public_key="$(<"${SSH_KEY_PATH}")"

  local key_name
  key_name="${PROJECT_NAME}-bootstrap-key"
  local key_id
  key_id="$(api GET "ssh_keys" | jq -r --arg n "${key_name}" '.ssh_keys[]? | select(.name==$n) | .id' | head -n 1)"
  if [[ -z "${key_id}" ]]; then
    key_id="$(api POST "ssh_keys" "$(jq -n --arg n "${key_name}" --arg k "${public_key}" '{name:$n, public_key:$k}')" | jq -r '.ssh_key.id')"
  fi

  local fw_id
  fw_id="$(<.hetzner_fw_id)"

  local payload
  payload="$(jq -n \
    --arg name "${SERVER_NAME}" \
    --arg st "${SERVER_TYPE}" \
    --arg image "${IMAGE_NAME}" \
    --arg loc "${SERVER_LOCATION}" \
    --argjson ssh_keys "[${key_id}]" \
    --argjson firewalls "[{\"firewall\":${fw_id}}]" \
    '{name:$name, server_type:$st, image:$image, location:$loc, ssh_keys:$ssh_keys, firewalls:$firewalls, labels:{project:"castuo-system"}}')"

  local response
  response="$(api POST "servers" "${payload}")"
  local server_id
  server_id="$(echo "${response}" | jq -r '.server.id')"
  local server_ip
  server_ip="$(echo "${response}" | jq -r '.server.public_net.ipv4.ip')"
  if [[ -z "${server_id}" || "${server_id}" == "null" ]]; then
    log ERROR "No se pudo crear servidor: ${response}"
    exit 1
  fi

  echo "${server_id}" > .hetzner_server_id
  echo "${server_ip}" > .hetzner_ip
  log INFO "Servidor creado id=${server_id}, ip=${server_ip}."
}

wait_for_ssh() {
  local server_ip
  server_ip="$(<.hetzner_ip)"
  log INFO "Esperando disponibilidad SSH en ${server_ip}..."
  for _ in $(seq 1 60); do
    if ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5 "root@${server_ip}" "echo ok" >/dev/null 2>&1; then
      log INFO "SSH disponible."
      return 0
    fi
    sleep 5
  done
  log ERROR "El servidor no quedo accesible por SSH a tiempo."
  exit 1
}

bootstrap_server() {
  local server_ip
  server_ip="$(<.hetzner_ip)"
  log INFO "Bootstrap del servidor ${server_ip}..."
  ssh -o StrictHostKeyChecking=no "root@${server_ip}" <<EOF
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq ca-certificates curl git docker.io docker-compose-plugin jq ufw fail2ban nginx certbot python3-certbot-nginx
systemctl enable docker --now
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable
systemctl enable fail2ban --now
if [[ ! -d /opt/${PROJECT_NAME} ]]; then
  git clone https://github.com/tu-usuario/castuo-system.git /opt/${PROJECT_NAME}
fi
cd /opt/${PROJECT_NAME}
if [[ -f .env.production ]]; then cp .env.production .env; fi
if [[ -f ${DOCKER_COMPOSE_FILE} ]]; then
  docker compose -f ${DOCKER_COMPOSE_FILE} pull || true
  docker compose -f ${DOCKER_COMPOSE_FILE} up -d
fi
cat >/etc/nginx/sites-available/${PROJECT_NAME} <<NGINX
server {
  listen 80;
  server_name ${DOMAIN_NAME};
  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
  location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
}
NGINX
ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/${PROJECT_NAME}
nginx -t
systemctl restart nginx
certbot --nginx -d ${DOMAIN_NAME} --non-interactive --agree-tos -m ${CONTACT_EMAIL} || true
EOF
  log INFO "Bootstrap completado."
}

verify_deployment() {
  local server_ip
  server_ip="$(<.hetzner_ip)"
  log INFO "Verificando despliegue..."
  curl -fsS "http://${server_ip}" >/dev/null || log WARN "Frontend no responde por IP (puede depender de DNS)."
  curl -fsS "http://${server_ip}:8000/health" >/dev/null || log WARN "Health backend no disponible por puerto directo."
  log INFO "Revision final completada. Revisa DNS y variables .env en produccion."
}

main() {
  log INFO "=== INICIO DESPLIEGUE HETZNER ==="
  validate_env
  ensure_firewall
  create_server
  wait_for_ssh
  bootstrap_server
  verify_deployment
  log INFO "=== FIN DESPLIEGUE HETZNER ==="
}

main "$@"

