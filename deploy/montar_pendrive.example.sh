#!/usr/bin/env bash
# Montaje LUKS interactivo (cryptsetup pedirá la frase de paso en TTY). Alternativa con stdin: mount_secure.example.sh.
# Punto de montaje por defecto /mnt/usb; flujo “secure” usa /mnt/castuo_secure (ver PRONTUARIO-AGROTECH-TLS §8.2).
set -euo pipefail

LUKS_PARTITION="${LUKS_PARTITION:-}"
MAPPER_NAME="${CASTUO_LUKS_MAPPER:-castuo_usb}"
MOUNT_POINT="${CASTUO_USB_MOUNT:-/mnt/usb}"

if [[ -z "$LUKS_PARTITION" ]]; then
  echo "Error: Definir LUKS_PARTITION (ej: /dev/disk/by-id/usb-...)" >&2
  exit 1
fi

sudo mkdir -p "$MOUNT_POINT"

sudo cryptsetup luksOpen "$LUKS_PARTITION" "$MAPPER_NAME"
sudo mount "/dev/mapper/${MAPPER_NAME}" "$MOUNT_POINT"

if [[ ! -f "$MOUNT_POINT/tokens/admin_general.token" ]]; then
  echo "Error: No se encuentra admin_general.token en $MOUNT_POINT/tokens" >&2
  sudo umount "$MOUNT_POINT" 2>/dev/null || true
  sudo cryptsetup luksClose "$MAPPER_NAME" 2>/dev/null || true
  exit 1
fi

echo "Pendrive montado correctamente en $MOUNT_POINT"
