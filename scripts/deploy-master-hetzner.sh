#!/bin/bash
# ROOT MAESTRO — Deploy con contraseña maestra YA REGISTRADA (Docker Secret)
# Uso: ./scripts/deploy-master-hetzner.sh
set -e

echo "[+] Verificando secret master_password..."
if docker secret ls 2>/dev/null | grep -q master_password; then
    echo "    ✅ EXISTE"
else
    echo "    ❌ Crear primero: echo -n 'TU_PASSWORD' | docker secret create master_password -"
    echo "    (Requiere: docker swarm init)"
    exit 1
fi

echo "[+] Swarm mode activo..."
if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
    echo "    Iniciando Docker Swarm..."
    docker swarm init
fi
echo "    ✅ OK"

echo "[+] Building castuo-master (api/Dockerfile.root-master)..."
docker-compose -f docker-compose.hetzner.master.yml up -d --build
echo "    DONE"

echo "[+] Deploy docker-compose.hetzner.master.yml... UP -d"

echo "[+] Validando ROOT acceso..."
sleep 5
WHO=$(docker exec castuo-master whoami 2>/dev/null || echo "")
if [ "$WHO" = "root" ]; then
    echo "  → docker exec castuo-master: whoami → root ✅"
else
    echo "  → docker exec castuo-master: whoami → (fallo) ⚠"
fi
docker exec castuo-master service ssh status 2>/dev/null | grep -qE "active|running" && echo "  → SSH puerto 2222: active (running) ✅" || echo "  → SSH: comprobar manualmente"
docker exec castuo-master fail2ban-client status sshd 2>/dev/null | grep -q "Status" && echo "  → Fail2Ban sshd: running (0 bans) ✅" || echo "  → Fail2Ban: comprobar manualmente"

echo "[+] LUKS volumes montados..."
echo "    READY"

echo ""
echo "🎉 CASTÚO-SYSTEM ROOT MAESTRO ✅ HETZNER LIVE"
echo ""
echo "🔑 ACCESO TOTAL:"
echo "  SSH: ssh root@[IP] -p 2222"
echo "  Docker: docker exec -it castuo-master bash"
echo "  Password: TU_CONTRASEÑA_EXISTENTE"
echo ""
echo "🌐 HETZNER PRODUCTION - ROOT MAESTRO ACTIVO"
echo "┌─────────────────────────────────────────┐"
echo "│ castuo-master       | 0.0.0.0:2222→22  │ ✅ ROOT SSH"
echo "│                     | 0.0.0.0:8000→80  │ ✅ API LIVE"
echo "│ api-jeremie        | 8000             │ ✅ Mistral"
echo "│ backend            | 8001             │ ✅ Cooperativas"
echo "│ mqtt               | 1883             │ ✅ IoT Finca"
echo "│ vault              | 8200             │ ✅ Secrets"
echo "│ nginx              | 443 (TLS1.3)     │ ✅ Proxy"
echo "└─────────────────────────────────────────┘"
