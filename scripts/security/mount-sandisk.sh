#!/bin/bash
# CASTÚO-SYSTEM™ — Montaje seguro del SanDisk (LUKS + opcional VeraCrypt).
# Requiere: YubiKey/contraseña para desbloquear. No almacenar contraseñas en script.
# Uso: sudo ./scripts/security/mount-sandisk.sh [/dev/sdX]

set -e
DISK="${1:-/dev/sdX}"
MAPPER="${CASTUO_LUKS_MAPPER:-castuo_secure}"
MOUNT_POINT="${CASTUO_SANDISK_MOUNT:-/mnt/sandisk}"
SECURE_ROOT="$MOUNT_POINT/CASTUO_SECURE"

if [ ! -b "$DISK" ]; then
  echo "Uso: $0 /dev/sdX  (dispositivo de bloque del SanDisk)"
  exit 1
fi

read -s -p "Contraseña LUKS del SanDisk: " LUKS_PASS
echo
[ -z "$LUKS_PASS" ] && { echo "Contraseña vacía."; exit 1; }

cryptsetup open --type luks2 "$DISK" "$MAPPER" <<< "$LUKS_PASS" || { unset LUKS_PASS; exit 1; }
unset LUKS_PASS
mkdir -p "$MOUNT_POINT"
mount "/dev/mapper/$MAPPER" "$MOUNT_POINT" 2>/dev/null || true

# Opcional: montar volumen VeraCrypt interno
VC_CONTAINER="$MOUNT_POINT/castuo_veracrypt.hc"
if [ -f "$VC_CONTAINER" ]; then
  echo "Volumen VeraCrypt detectado. Montar manualmente si se desea: veracrypt $VC_CONTAINER $SECURE_ROOT"
fi

[ -d "$SECURE_ROOT" ] || mkdir -p "$SECURE_ROOT"
echo "SanDisk montado en $MOUNT_POINT. Datos sensibles en $SECURE_ROOT."
