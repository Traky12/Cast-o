#!/bin/bash
# scripts/security/mount_veracrypt_container_eu.sh
#
# Monta un contenedor VeraCrypt no interactivo.
#
set -euo pipefail

CONTAINER_PATH="${CONTAINER_PATH:-}"
MOUNT_POINT="${MOUNT_POINT:-/mnt/secure_castuo}"
PASSWORD_FILE="${PASSWORD_FILE:-}"

if [[ -z "$CONTAINER_PATH" || -z "$PASSWORD_FILE" ]]; then
  echo "Missing CONTAINER_PATH or PASSWORD_FILE" >&2
  exit 1
fi
if [[ ! -f "$CONTAINER_PATH" ]]; then
  echo "Container not found: $CONTAINER_PATH" >&2
  exit 1
fi
if [[ ! -f "$PASSWORD_FILE" ]]; then
  echo "Invalid PASSWORD_FILE: $PASSWORD_FILE" >&2
  exit 1
fi

PASSWORD="$(head -n 1 "$PASSWORD_FILE" | tr -d '\r\n')"
if [[ -z "$PASSWORD" ]]; then
  echo "Empty password" >&2
  exit 1
fi

sudo mkdir -p "$MOUNT_POINT"

veracrypt "$CONTAINER_PATH" "$MOUNT_POINT" \
  --password "$PASSWORD" \
  --pim 0 \
  --keyfiles "" \
  --protect-hidden=no \
  --non-interactive

echo "OK (mounted at $MOUNT_POINT)"

