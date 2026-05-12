#!/bin/bash
# CASTÚO-SYSTEM™ — Punto de acceso único: autenticación biométrica + YubiKey + HSM, luego despacho a sistema.
# Uso: ./scripts/security/secure-access.sh [gaiachain|cursor|hsm|backup|destroy]

set -e
CASTUO_ROOT="${CASTUO_ROOT:-/opt/castuo}"
SECURITY="$CASTUO_ROOT/scripts/security"
[ -d "$SECURITY" ] || SECURITY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Autenticación (biométrica o YubiKey+contraseña)
if [ -f "$SECURITY/biometric_auth.py" ]; then
  python3 "$SECURITY/biometric_auth.py" || exit 1
elif [ -f "$SECURITY/authenticate_with_yubikey.py" ]; then
  python3 "$SECURITY/authenticate_with_yubikey.py" || exit 1
elif [ -f "$SECURITY/authenticate.py" ]; then
  python3 "$SECURITY/authenticate.py" || exit 1
else
  echo "Ningún script de autenticación encontrado."
  exit 1
fi
if [ ! -f "${CASTUO_SESSION_FILE:-/tmp/gaiachain_biometric_session.token}" ] && [ ! -f "/tmp/gaiachain_session.token" ]; then
  echo "No se encontró token de sesión."
  exit 1
fi

# 2. Despacho según argumento
case "${1:-}" in
  gaiachain)
    kubectl exec -n gaiachain -it gaiachain-master-0 -- /opt/gaiachain/bin/gaiachain-admin 2>/dev/null || \
      echo "kubectl o pod gaiachain no disponible."
    ;;
  cursor)
    docker exec -it cursor-sandbox /opt/cursor/bin/cursor-admin 2>/dev/null || \
      echo "Docker o contenedor cursor no disponible."
    ;;
  hsm)
    echo "Listar objetos HSM (PIN por entorno HSM_USER_PIN o interactivo):"
    pkcs11-tool --login --list-objects 2>/dev/null || true
    ;;
  backup)
    [ -x "$SECURITY/encrypted-backup.sh" ] && "$SECURITY/encrypted-backup.sh" || echo "encrypted-backup.sh no encontrado."
    ;;
  destroy)
    read -p "Centro a destruir (caceres_dc/madrid_dc/satellite/local): " target
    if [ "$target" = "satellite" ]; then
      python3 "$SECURITY/satellite-destruction.py" 2>/dev/null || true
    elif [ "$target" = "local" ]; then
      [ -x "$SECURITY/secure-destruction-protocol.sh" ] && sudo "$SECURITY/secure-destruction-protocol.sh" || true
    else
      [ -x "$SECURITY/secure-wipe-disks.sh" ] && sudo "$SECURITY/secure-wipe-disks.sh" || true
    fi
    ;;
  *)
    echo "Uso: $0 [gaiachain|cursor|hsm|backup|destroy]"
    exit 0
    ;;
esac
