#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# CASTÚO-SYSTEM™ — LLMNR/NBT-NS Hardening Script
# ─────────────────────────────────────────────────────────────────────────────
# Propósito:
#   Desactiva LLMNR (Link-Local Multicast Name Resolution) y NBT-NS
#   (NetBIOS Name Service) en hosts edge Linux para eliminar vectores
#   de envenenamiento de red (MITM/Responder attacks).
#
# Referencia:
#   - PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §4 (hardening de red)
#   - DPIA-Robotics-2026 §3.2 (medidas técnicas)
#   - CIS Benchmark Linux — Control 3.3
#
# Uso:
#   sudo bash scripts/llmnr_hardening.sh
#
# Requisitos: systemd-resolved, nmcli (NetworkManager) o /etc/hosts fallback
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── colores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

echo "─────────────────────────────────────────────────────────────"
echo " CASTÚO-SYSTEM — LLMNR/NBT-NS Hardening"
echo " Host: $(hostname) | $(date -u '+%Y-%m-%d %H:%M UTC')"
echo "─────────────────────────────────────────────────────────────"

# ── 1. systemd-resolved — deshabilitar LLMNR ─────────────────────────────────
if systemctl is-active --quiet systemd-resolved 2>/dev/null; then
    RESOLVED_CONF="/etc/systemd/resolved.conf"

    # Backup antes de modificar
    if [[ ! -f "${RESOLVED_CONF}.bak" ]]; then
        cp "$RESOLVED_CONF" "${RESOLVED_CONF}.bak"
        ok "Backup creado: ${RESOLVED_CONF}.bak"
    fi

    # Desactivar LLMNR
    if grep -q "^LLMNR=" "$RESOLVED_CONF"; then
        sed -i 's/^LLMNR=.*/LLMNR=no/' "$RESOLVED_CONF"
    elif grep -q "^\[Resolve\]" "$RESOLVED_CONF"; then
        sed -i '/^\[Resolve\]/a LLMNR=no' "$RESOLVED_CONF"
    else
        echo -e "[Resolve]\nLLMNR=no" >> "$RESOLVED_CONF"
    fi

    # Desactivar MulticastDNS también (hardening adicional)
    if grep -q "^MulticastDNS=" "$RESOLVED_CONF"; then
        sed -i 's/^MulticastDNS=.*/MulticastDNS=no/' "$RESOLVED_CONF"
    else
        sed -i '/^LLMNR=no/a MulticastDNS=no' "$RESOLVED_CONF"
    fi

    systemctl restart systemd-resolved
    ok "systemd-resolved: LLMNR=no + MulticastDNS=no"
else
    warn "systemd-resolved no activo — omitido"
fi

# ── 2. NetworkManager — deshabilitar LLMNR ───────────────────────────────────
if command -v nmcli &>/dev/null; then
    NM_CONF_DIR="/etc/NetworkManager/conf.d"
    mkdir -p "$NM_CONF_DIR"
    cat > "$NM_CONF_DIR/castuo-llmnr-off.conf" <<'NMEOF'
[connection]
# CASTÚO-SYSTEM: LLMNR desactivado (hardening)
# Ref: PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §4
llmnr=0
mdns=0
NMEOF
    systemctl reload NetworkManager 2>/dev/null || true
    ok "NetworkManager: LLMNR=0 (castuo-llmnr-off.conf)"
else
    warn "NetworkManager no encontrado — omitido"
fi

# ── 3. NBT-NS — deshabilitar en Samba/nmbd ───────────────────────────────────
if command -v nmbd &>/dev/null; then
    if systemctl is-active --quiet nmbd 2>/dev/null; then
        systemctl stop nmbd
        systemctl disable nmbd 2>/dev/null || true
        ok "nmbd (NBT-NS) detenido y desactivado"
    else
        ok "nmbd ya estaba inactivo"
    fi
else
    ok "nmbd no instalado — NBT-NS no expuesto"
fi

# ── 4. Verificación ───────────────────────────────────────────────────────────
echo ""
echo "── Verificación post-hardening ──────────────────────────────"

# Comprobar que LLMNR puerto 5355/UDP no escucha
if ss -ulnp 2>/dev/null | grep -q ":5355 "; then
    warn "Puerto 5355/UDP sigue en escucha — revisar manualmente"
else
    ok "Puerto 5355/UDP: cerrado"
fi

# Comprobar NBT-NS 137/UDP
if ss -ulnp 2>/dev/null | grep -q ":137 "; then
    warn "Puerto 137/UDP (NBT-NS) sigue en escucha — revisar nmbd/winbind"
else
    ok "Puerto 137/UDP: cerrado"
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo " LLMNR/NBT-NS hardening completado."
echo " Vectores eliminados: MITM/Responder DNS poisoning"
echo " Para revertir: restaurar ${RESOLVED_CONF}.bak"
echo "─────────────────────────────────────────────────────────────"
