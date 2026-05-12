#!/bin/bash
# ROOT MAESTRO — Activa root con contraseña existente (Docker Secret)
set -e
MASTER_PWD=""
if [ -f /run/secrets/master_password ]; then
    MASTER_PWD=$(cat /run/secrets/master_password)
fi
if [ -n "$MASTER_PWD" ]; then
    echo "root:${MASTER_PWD}" | chpasswd
fi
# SSH root habilitado
for f in /etc/ssh/sshd_config; do
    [ -f "$f" ] && sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' "$f" || true
    [ -f "$f" ] && sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' "$f" || true
done
# Fail2Ban
mkdir -p /etc/fail2ban
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
bantime = 3600
maxretry = 3
EOF
exec "$@"
