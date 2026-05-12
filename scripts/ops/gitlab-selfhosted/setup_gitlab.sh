#!/bin/bash
# scripts/ops/gitlab-selfhosted/setup_gitlab.sh
#
# Plantilla (scaffolding) para instalar GitLab self-hosted.
# Evita valores sensibles. Define:
# - EXTERNAL_URL
# - SSH port si aplica
#
# Script de apoyo a la doc:
#   docs/ops/gitlab-selfhosted/README.md

set -euo pipefail

EXTERNAL_URL="${EXTERNAL_URL:-https://gitlab.castuo-system.eu}"
GITLAB_SSH_PORT="${GITLAB_SSH_PORT:-22}"

if [[ $EUID -ne 0 ]]; then
  echo "Este script requiere ejecutar como root o con sudo." >&2
  exit 1
fi

echo "[setup_gitlab] Preparando dependencias..."
apt-get update
apt-get install -y curl openssh-server ca-certificates tzdata perl

echo "[setup_gitlab] Instalando GitLab (plantilla)..."
curl https://packages.gitlab.com/install/repositories/gitlab/gitlab-ee/script.deb.sh | bash

# Nota: GitLab usa config interna; el instalador lee EXTERNAL_URL.
EXTERNAL_URL="$EXTERNAL_URL" apt-get install -y gitlab-ee

echo "[setup_gitlab] Ajustando SSH port (si aplica)..."
# Placeholder: en entornos reales se configura /etc/gitlab/gitlab.rb.
# Este script no toca configuraciones sensibles/irreversibles.

echo "[setup_gitlab] Instalando script de backup (a IPFS + witness opcional)..."
SRC_BACKUP_SCRIPT="$PWD/docs/ops/gitlab-selfhosted/backup_to_ipfs.sh"
if [[ ! -f "$SRC_BACKUP_SCRIPT" ]]; then
  # fallback: buscar desde el directorio del script
  ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
  SRC_BACKUP_SCRIPT="$ROOT_DIR/docs/ops/gitlab-selfhosted/backup_to_ipfs.sh"
fi

DEST_BACKUP_SCRIPT="/usr/local/bin/backup_to_ipfs.sh"
cp "$SRC_BACKUP_SCRIPT" "$DEST_BACKUP_SCRIPT"
chmod +x "$DEST_BACKUP_SCRIPT"

echo "[setup_gitlab] Configura la variable GAIA_CHAIN_API_KEY y IPFS en entorno del sistema."
echo "[setup_gitlab] Luego agrega cron (ejemplo) al crontab de root:"
echo "  0 3 * * * /usr/local/bin/backup_to_ipfs.sh >> /var/log/gitlab/backup_cron.log 2>&1"

echo "[setup_gitlab] Fin. Revisa estado de GitLab con: gitlab-ctl status"

