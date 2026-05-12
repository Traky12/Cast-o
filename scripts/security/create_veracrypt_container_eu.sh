#!/bin/bash
# scripts/security/create_veracrypt_container_eu.sh
#
# Crea un contenedor VeraCrypt (modo no interactivo).
# REQUISITOS:
#   - CONTAINER_PATH: ruta del archivo de contenedor (ej: /data/castuo/secure_container.hc)
#   - MOUNT_POINT: (opcional) punto de montaje
#   - PASSWORD_FILE: archivo con la password (una linea)
#
set -euo pipefail

CONTAINER_PATH="${CONTAINER_PATH:-}"
CONTAINER_SIZE="${CONTAINER_SIZE:-1G}"
MOUNT_POINT="${MOUNT_POINT:-/mnt/secure_castuo}"
PASSWORD_FILE="${PASSWORD_FILE:-}"

if [[ -z "$CONTAINER_PATH" ]]; then
  echo "Missing CONTAINER_PATH" >&2
  exit 1
fi
if [[ -z "$PASSWORD_FILE" || ! -f "$PASSWORD_FILE" ]]; then
  echo "Missing/invalid PASSWORD_FILE" >&2
  exit 1
fi

PASSWORD="$(head -n 1 "$PASSWORD_FILE" | tr -d '\r\n')"
if [[ -z "$PASSWORD" ]]; then
  echo "Empty password in PASSWORD_FILE" >&2
  exit 1
fi

echo "Creando contenedor: $CONTAINER_PATH (size=$CONTAINER_SIZE) ..."
sudo mkdir -p "$(dirname "$CONTAINER_PATH")"

veracrypt --create "$CONTAINER_PATH" \
  --size "$CONTAINER_SIZE" \
  --password "$PASSWORD" \
  --pim 0 \
  --keyfiles "" \
  --encryption AES \
  --hash SHA-512 \
  --filesystem ext4 \
  --non-interactive \
  --random-source /dev/urandom

echo "Montando (opcional) en: $MOUNT_POINT"
sudo mkdir -p "$MOUNT_POINT"
veracrypt "$CONTAINER_PATH" "$MOUNT_POINT" \
  --password "$PASSWORD" \
  --pim 0 \
  --keyfiles "" \
  --protect-hidden=no \
  --non-interactive

echo "OK"

