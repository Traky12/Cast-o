#!/usr/bin/env bash
# Desmonta el volumen montado en CASTUO_CASTUO_SECURE_MOUNT y cierra el mapper LUKS.
set -euo pipefail

MAPPER_NAME="${CASTUO_LUKS_MAPPER:-castuo_usb}"
MOUNT_POINT="${CASTUO_CASTUO_SECURE_MOUNT:-/mnt/castuo_secure}"

if mountpoint -q "$MOUNT_POINT" 2>/dev/null || findmnt "$MOUNT_POINT" &>/dev/null; then
  sudo umount "$MOUNT_POINT"
elif mount | grep -q " ${MOUNT_POINT} "; then
  sudo umount "$MOUNT_POINT"
else
  echo "No hay montaje activo en $MOUNT_POINT" >&2
  exit 1
fi

if [[ -e "/dev/mapper/${MAPPER_NAME}" ]]; then
  sudo cryptsetup close "$MAPPER_NAME"
fi

echo "Pendrive desmontado."
