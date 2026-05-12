#!/usr/bin/env bash
# Preparación inicial: partición LUKS + ext4 + árbol tokens (Linux). Destruye datos del dispositivo objetivo.
# No ejecutar sobre el disco equivocado. En Windows la letra "D:" no es este nodo; en el servidor Linux usar lsblk / /dev/disk/by-id/.
set -euo pipefail

DEVICE="${CASTUO_LUKS_DEVICE:-}"
MAPPER_NAME="${CASTUO_LUKS_MAPPER:-castuo_usb}"
TEMP_MOUNT="${CASTUO_LUKS_PREP_MOUNT:-/mnt/castuo_prep}"

if [[ -z "$DEVICE" ]]; then
  echo "Definir partición LUKS, ej.: export CASTUO_LUKS_DEVICE=/dev/disk/by-id/usb-SanDisk_..." >&2
  exit 1
fi

if [[ ! -b "$DEVICE" ]]; then
  echo "Error: $DEVICE no es un dispositivo de bloque" >&2
  exit 1
fi

echo "Se va a cifrar (LUKS) y formatear: $DEVICE" >&2
echo "Escribe YES en mayúsculas para continuar:" >&2
read -r confirm
if [[ "$confirm" != "YES" ]]; then
  echo "Cancelado." >&2
  exit 1
fi

sudo cryptsetup luksFormat "$DEVICE"
sudo cryptsetup open --type luks "$DEVICE" "$MAPPER_NAME"
sudo mkfs.ext4 -L castuo_tokens "/dev/mapper/${MAPPER_NAME}"

sudo mkdir -p "$TEMP_MOUNT"
sudo mount "/dev/mapper/${MAPPER_NAME}" "$TEMP_MOUNT"
sudo install -d -m 0700 "$TEMP_MOUNT/tokens"
sudo chmod 700 "$TEMP_MOUNT/tokens"

echo "Montado en $TEMP_MOUNT — crea los ficheros en tokens/ (ver deploy/PENDRIVE-CONTENIDO.md), luego:" >&2
echo "  sudo umount $TEMP_MOUNT && sudo cryptsetup close $MAPPER_NAME" >&2
