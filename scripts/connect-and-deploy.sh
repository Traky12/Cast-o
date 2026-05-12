#!/usr/bin/env bash
# scripts/connect-and-deploy.sh
# Ejecutar en el devcontainer DESPUÉS de:
#   1. Abrir puerto 22 en firewall-1 de Hetzner
#   2. Añadir clave SSH al servidor via consola web Hetzner
#
# Uso: bash scripts/connect-and-deploy.sh

set -euo pipefail

SERVER="89.167.5.233"
SSH_KEY="$HOME/.ssh/castuo_hel1"
SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10"
SSH_OPTS="$SSH_OPTS -o BatchMode=yes -o PreferredAuthentications=publickey -o IdentitiesOnly=yes"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC}  $*"; }
warn() { echo -e "${YELLOW}[!!]${NC}  $*"; }
fail() { echo -e "${RED}[XX]${NC}  $*"; exit 1; }
step() { echo -e "\n${YELLOW}───────────────────────────────────────${NC}"; echo "  $*"; }

# ─── 1. Verificar conectividad ────────────────────────────────────────────────
step "1/5  Verificando puerto 22 en $SERVER"
timeout 8 bash -c "echo >/dev/tcp/$SERVER/22" 2>/dev/null \
  && ok "Puerto 22 accesible" \
  || fail "Puerto 22 CERRADO.\n  → Panel Hetzner: Firewalls → firewall-1 → Add rule: TCP 22 0.0.0.0/0\n  → Tambien ELIMINAR la regla 3306 (MySQL expuesto es riesgo de seguridad)"

# ─── 2. Test SSH ──────────────────────────────────────────────────────────────
step "2/5  Probando autenticacion SSH"
ssh $SSH_OPTS root@$SERVER "echo SSH_OK" 2>/dev/null \
  && ok "SSH autenticado correctamente" \
  || fail "SSH fallo.\n  → Añade la clave publica al servidor via consola web Hetzner:\n    echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHiblsqHeic9BoPysOghMdRoFBAo8iKSivQMkxN5ElDr castuo-codespace-20260401' >> ~/.ssh/authorized_keys"

# ─── 3. Info del servidor ────────────────────────────────────────────────────
step "3/5  Estado del servidor"
ssh $SSH_OPTS root@$SERVER bash <<'EOF'
  echo "OS      : $(uname -a)"
  echo "RAM     : $(free -h | awk '/^Mem/{print $2" total / "$3" usado"}')"
  echo "Disco   : $(df -h / | awk 'NR==2{print $2" total / "$4" libre"}')"
  echo "Docker  : $(docker --version 2>/dev/null || echo 'no instalado')"
  echo "Repo    : $([ -d /opt/castuo-system/.git ] && echo 'clonado' || echo 'pendiente')"
  echo "Compose : $([ -f /opt/castuo-system/docker-compose.yml ] && docker ps --format '{{.Names}}' 2>/dev/null | grep -c '' || echo '0') contenedores corriendo"
EOF

# ─── 4. Copiar y ejecutar setup ──────────────────────────────────────────────
step "4/5  Copiando script de setup al servidor"
scp $SSH_OPTS /workspaces/Castuo-system/scripts/hetzner-server-setup.sh root@$SERVER:/root/setup.sh
ssh $SSH_OPTS root@$SERVER "chmod +x /root/setup.sh"
ok "Script copiado. Ejecutando setup completo (puede tardar 5-10 min)..."

ssh $SSH_OPTS root@$SERVER "bash /root/setup.sh 2>&1 | tee /var/log/castuo-deploy.log"

# ─── 5. Health checks finales ────────────────────────────────────────────────
step "5/5  Verificando servicios"
sleep 5

# Puertos esperados del stack — n8n en 5678 (NO 5432, ese es PostgreSQL)
for port_label in "8000:API-SABIONDA" "5678:n8n(workflows)" "3000:Grafana" "9090:Prometheus" "8545:GaiaChain-RPC"; do
  port="${port_label%%:*}"
  label="${port_label##*:}"
  if timeout 5 bash -c "echo >/dev/tcp/$SERVER/$port" 2>/dev/null; then
    ok "$label  http://${SERVER}:${port}"
  else
    warn "$label  puerto $port no responde aun"
  fi
done

echo ""
echo "════════════════════════════════════════════════════"
echo "  CASTUO-SYSTEM  —  Acceso directo"
echo "════════════════════════════════════════════════════"
echo "  API  http://${SERVER}:8000/health"
echo "  n8n  http://${SERVER}:5678"
echo "  Grafana  http://${SERVER}:3000"
echo "════════════════════════════════════════════════════"
echo ""
echo "  SSH directo:"
echo "    ssh -i ~/.ssh/castuo_hel1 root@${SERVER}"
echo ""
echo "  Logs en tiempo real:"
echo "    ssh -i ~/.ssh/castuo_hel1 root@${SERVER} 'docker compose -f /opt/castuo-system/docker-compose.yml logs -f'"
