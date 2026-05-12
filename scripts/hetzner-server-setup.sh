#!/usr/bin/env bash
# scripts/hetzner-server-setup.sh
# Ejecutar en el servidor Hetzner (hel1) como root tras el primer login SSH.
# Este script es idem-potente: se puede relanzar sin riesgo.
set -euo pipefail

REPO_URL="https://github.com/Traky12/Castuo-system.git"
INSTALL_DIR="/opt/castuo-system"
LOG_FILE="/var/log/castuo-deploy.log"

log()  { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG_FILE"; }
ok()   { echo -e "[OK]  $*" | tee -a "$LOG_FILE"; }
warn() { echo -e "[!!]  $*" | tee -a "$LOG_FILE"; }
fail() { echo -e "[XX]  $*" | tee -a "$LOG_FILE"; exit 1; }

log "=== CASTUO-SYSTEM — Setup servidor Hetzner hel1 ==="

# ─── 1. Paquetes base ─────────────────────────────────────────────────────────
log "1/7  Instalando paquetes base..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y --no-install-recommends \
    curl wget git docker.io docker-compose-plugin \
    jq htop ufw ca-certificates gnupg 2>&1 | tail -5
systemctl enable --now docker
usermod -aG docker root 2>/dev/null || true
ok "Paquetes instalados."

# ─── 2. Firewall ─────────────────────────────────────────────────────────────
log "2/7  Configurando UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   comment "SSH"
ufw allow 80/tcp   comment "HTTP"
ufw allow 443/tcp  comment "HTTPS"
ufw allow 8000/tcp comment "CASTUO API"
ufw allow 5678/tcp comment "n8n"
ufw allow 3000/tcp comment "Grafana"
ufw allow 9090/tcp comment "Prometheus"
ufw allow 8545/tcp comment "GaiaChain RPC"
ufw --force enable
ok "UFW configurado (SSH + puertos de servicio)."

# ─── 3. Clonar / actualizar repo ─────────────────────────────────────────────
log "3/7  Repositorio..."
if [ -d "$INSTALL_DIR/.git" ]; then
    warn "Repo ya existe. Actualizando..."
    git -C "$INSTALL_DIR" fetch origin
    git -C "$INSTALL_DIR" checkout main
    git -C "$INSTALL_DIR" pull --ff-only
else
    git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
fi
ok "Repo en $INSTALL_DIR"

# ─── 4. Variables de entorno ──────────────────────────────────────────────────
log "4/7  Variables de entorno..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    warn ".env creado desde .env.example."
    warn "Edita los secretos ANTES de que el stack arranque:"
    warn "  nano $INSTALL_DIR/.env"
    warn "Variables criticas: POSTGRES_PASSWORD, JWT_SECRET_KEY, N8N_PASSWORD, GRAFANA_PASSWORD"
else
    ok ".env ya existe. Se conserva sin cambios."
fi

# ─── 5. Montar volumen de datos (si existe /dev/sdb) ─────────────────────────
log "5/7  Volumen de datos..."
if [ -b /dev/sdb ] && ! mountpoint -q /mnt/castuo-data; then
    mkfs.ext4 /dev/sdb -F -L castuo-data
    mkdir -p /mnt/castuo-data
    mount /dev/sdb /mnt/castuo-data
    echo "LABEL=castuo-data /mnt/castuo-data ext4 defaults 0 2" >> /etc/fstab
    ok "Volumen /dev/sdb montado en /mnt/castuo-data"
elif mountpoint -q /mnt/castuo-data; then
    ok "/mnt/castuo-data ya montado."
else
    warn "No se detecto /dev/sdb. Se usara almacenamiento local (solo para dev/staging)."
fi

mkdir -p /mnt/castuo-data/{postgres,prometheus,grafana,vault,n8n}
chmod 755 /mnt/castuo-data

# ─── 6. Docker Compose up ────────────────────────────────────────────────────
log "6/7  Levantando CASTUO-SYSTEM con Docker Compose..."
cd "$INSTALL_DIR"

# Servidor cax21 = ARM64 (Ampere Altra). BuildKit activo para compilacion nativa.
export DOCKER_BUILDKIT=1

# Predescargar imagenes antes de build para acelerar
docker compose pull --quiet 2>/dev/null || true

docker compose up -d --build
ok "docker compose up completado."

# ─── 7. Health checks ────────────────────────────────────────────────────────
log "7/7  Verificando servicios (espera max 90s para la API)..."

PUBLIC_IP=$(curl -sf https://api64.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')

wait_http() {
    local url=$1 label=$2 max=90 waited=0
    while [ $waited -lt $max ]; do
        if curl -fsS "$url" -o /dev/null 2>/dev/null; then
            ok "$label  $url"
            return 0
        fi
        sleep 5; waited=$((waited+5))
    done
    warn "$label  no respondio en ${max}s — comprueba: docker compose logs"
}

wait_http "http://localhost:8000/health" "API SABIONDA"
wait_http "http://localhost:5678"        "n8n"
wait_http "http://localhost:3000"        "Grafana"

echo ""
echo "════════════════════════════════════════════════════"
echo "  CASTUO-SYSTEM  —  Acceso externo"
echo "════════════════════════════════════════════════════"
echo "  API  (SABIONDA)   http://${PUBLIC_IP}:8000/health"
echo "  n8n  (workflows)  http://${PUBLIC_IP}:5678"
echo "  Grafana           http://${PUBLIC_IP}:3000"
echo "  Prometheus        http://${PUBLIC_IP}:9090"
echo "  GaiaChain RPC     http://${PUBLIC_IP}:8545"
echo ""
echo "  Logs en tiempo real:"
echo "    docker compose -f $INSTALL_DIR/docker-compose.yml logs -f"
echo "════════════════════════════════════════════════════"
echo ""
echo "  Log completo: $LOG_FILE"
