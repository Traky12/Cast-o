#!/usr/bin/env bash
# Montaje LUKS con frase de paso por teclado (no queda en historial de bash como comando echo).
# Uso: ./mount_secure.example.sh [/dev/disk/by-id/...]  (por defecto CASTUO_LUKS_DEVICE o primer argumento)
set -euo pipefail

DEVICE="${1:-${CASTUO_LUKS_DEVICE:-}}"
MAPPER_NAME="${CASTUO_LUKS_MAPPER:-castuo_usb}"
MOUNT_POINT="${CASTUO_CASTUO_SECURE_MOUNT:-/mnt/castuo_secure}"

if [[ -z "$DEVICE" ]]; then
  echo "Uso: $0 /dev/disk/by-id/usb-...-part1   o   export CASTUO_LUKS_DEVICE=..." >&2
  exit 1
fi

if [[ ! -b "$DEVICE" ]]; then
  echo "Error: dispositivo no encontrado: $DEVICE" >&2
  exit 1
fi

if [[ -e "/dev/mapper/${MAPPER_NAME}" ]]; then
  echo "Error: ya existe /dev/mapper/${MAPPER_NAME} (¿cerrar con cryptsetup close antes?)" >&2
  exit 1
fi

read -r -s -p "Frase de paso LUKS: " PASSWORD
echo "" >&2

if ! printf '%s\n' "$PASSWORD" | sudo cryptsetup open --type luks "$DEVICE" "$MAPPER_NAME" --key-file -; then
  echo "Error: no se pudo abrir LUKS (frase incorrecta o dispositivo dañado)" >&2
  exit 1
fi

sudo mkdir -p "$MOUNT_POINT"
if ! sudo mount "/dev/mapper/${MAPPER_NAME}" "$MOUNT_POINT"; then
  sudo cryptsetup close "$MAPPER_NAME" 2>/dev/null || true
  exit 1
fi

TOK="$MOUNT_POINT/tokens"
if [[ -f "$TOK/admin_general.token" ]]; then
  echo "Pendrive montado en $MOUNT_POINT" >&2
  ls -la "$TOK" >&2
else
  echo "Error: falta $TOK/admin_general.token" >&2
  sudo umount "$MOUNT_POINT" 2>/dev/null || true
  sudo cryptsetup close "$MAPPER_NAME" 2>/dev/null || true
  exit 1
fi
