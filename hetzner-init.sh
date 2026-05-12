#!/usr/bin/env bash
# Bootstrap CX22 — Docker, UFW, fail2ban, swap, certbot, backup cron.
# Opcional: CASTUO_DOMAIN=castuo.tudominio.eu → /etc/castuo/domain.env
# Raw (sustituye org/repo): curl -fsSL https://raw.githubusercontent.com/tu-org/Castuo-System/main/hetzner-init.sh | bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

echo "==> Paquetes base + certbot"
apt-get update -y
apt-get install -y --no-install-recommends \
  ca-certificates curl gnupg ufw fail2ban jq rsync cron certbot

echo "==> Docker Engine"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker

echo "==> Swap 2G"
if ! swapon --show | grep -q '/swapfile'; then
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> UFW"
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "==> fail2ban (SSH)"
cat >/etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 6

[sshd]
enabled = true
EOF
systemctl enable --now fail2ban

if [[ -n "${CASTUO_DOMAIN:-}" ]]; then
  echo "==> CASTUO_DOMAIN=$CASTUO_DOMAIN → /etc/castuo/domain.env"
  install -d -m 0755 /etc/castuo
  umask 077
  printf 'CASTUO_DOMAIN=%s\n' "$CASTUO_DOMAIN" >/etc/castuo/domain.env
  umask 022
fi

echo "==> Directorio despliegue"
install -d -m 0755 /opt/castuo-system

echo "==> Cron backup Postgres"
CRON_SH=/usr/local/bin/castuo-pg-backup.sh
cat >"$CRON_SH" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
OUT=/var/backups/castuo
mkdir -p "$OUT"
if docker ps --format '{{.Names}}' | grep -qx castuo-postgres; then
  docker exec castuo-postgres bash -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
    >"$OUT/castuo_$(date +%Y%m%d_%H%M).dump" || true
fi
find "$OUT" -name '*.dump' -mtime +7 -delete 2>/dev/null || true
EOS
chmod 0755 "$CRON_SH"
install -d -m 0700 /var/backups/castuo
printf '17 3 * * * root %s\n' "$CRON_SH" >/etc/cron.d/castuo-pg-backup
chmod 0644 /etc/cron.d/castuo-pg-backup

echo "==> Listo. Clona el repo, crea .env.production, edita castuo.conf, DNS, TLS (CHECKLIST-CURSOR-HETZNER-D1.md)."
