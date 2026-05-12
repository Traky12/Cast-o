#!/bin/bash
# scripts/security/umount_veracrypt_container_eu.sh
#
set -euo pipefail

MOUNT_POINT="${MOUNT_POINT:-/mnt/secure_castuo}"

echo "Desmontando VeraCrypt en $MOUNT_POINT ..."

# -d == detach
sudo veracrypt -d "$MOUNT_POINT" || true

if mount | grep -q "$MOUNT_POINT"; then
  echo "Still mounted: $MOUNT_POINT" >&2
  exit 1
fi

echo "OK (unmounted)"

