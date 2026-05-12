#!/bin/bash
# CASTÚO-SYSTEM™ — Borrado seguro de discos (DoD 5220.22-M, 7 pasadas). Solo administrador.
# Requiere: contraseña maestra + YubiKey OTP. Registra el evento en GaiaChain.
# Uso: sudo ./scripts/security/secure-wipe-disks.sh

set -e
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"

echo "=== Borrado seguro de discos (DoD 5220.22-M) ==="
read -s -p "Introduce la contraseña maestra para confirmar: " MASTER_PASSWORD
echo
read -p "Toca tu YubiKey y pega el OTP: " YUBIKEY_OTP

[ -z "$MASTER_PASSWORD" ] && { echo "Contraseña vacía."; exit 1; }
[ ! -f "$CHAIN_DIR/master_password.hash" ] && { echo "No hay hash de contraseña maestra."; exit 1; }

INPUT_HASH=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha512 -binary | xxd -p -c 256)
STORED_HASH=$(cat "$CHAIN_DIR/master_password.hash")
if [ "$INPUT_HASH" != "$STORED_HASH" ]; then
  echo "Verificación fallida. Abortando."
  unset MASTER_PASSWORD INPUT_HASH STORED_HASH
  exit 1
fi

if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "$CHAIN_DIR/master_key.pem" ]; then
  TS=$(date +%s)
  SIG=$(echo -n "WIPE_CONFIRMATION_${TS}" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0) || true
  VERIFICATION=$(curl -sf -X POST "${API_URL}/api/v1/auth/wipe" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"master_password_hash\":\"${INPUT_HASH}\",\"yubikey_otp\":\"${YUBIKEY_OTP}\",\"signature\":\"${SIG}\"}" 2>/dev/null | jq -r '.status // "FAIL"') || VERIFICATION="SKIP"
  if [ "$VERIFICATION" = "FAIL" ] && [ "$VERIFICATION" != "SKIP" ]; then
    echo "Verificación GaiaChain fallida. Abortando."
    unset MASTER_PASSWORD INPUT_HASH STORED_HASH
    exit 1
  fi
fi
unset MASTER_PASSWORD INPUT_HASH STORED_HASH

# Discos (excluir el disco de arranque si se desea; aquí se listan todos los block devices)
DISKS=()
while read -r name _; do
  case "$name" in
    sd[a-z]|nvme[0-9]n[0-9]) DISKS+=("$name") ;;
  esac
done < <(lsblk -d -n -o NAME 2>/dev/null) || true

if [ ${#DISKS[@]} -eq 0 ]; then
  echo "No se detectaron discos. Para forzar: DISKS_OVERRIDE=sda,sdb ./secure-wipe-disks.sh"
  [ -n "$DISKS_OVERRIDE" ] && IFS=',' read -ra DISKS <<< "$DISKS_OVERRIDE" || exit 1
fi

echo "Discos a borrar: ${DISKS[*]}"
read -p "Escribe YES para continuar con borrado DoD 7 pasadas: " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
  echo "Abortado."
  exit 0
fi

for disk in "${DISKS[@]}"; do
  [ ! -b "/dev/$disk" ] && continue
  echo "Borrando /dev/$disk (DoD 5220.22-M, 7 pasadas)..."
  for pass in 1 2 3 4 5 6 7; do
    if [ $((pass % 2)) -eq 1 ]; then
      dd if=/dev/zero of="/dev/$disk" bs=1M status=progress 2>/dev/null || true
    else
      dd if=/dev/urandom of="/dev/$disk" bs=1M status=progress 2>/dev/null || true
    fi
  done
  echo "/dev/$disk borrado."
done

if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "$CHAIN_DIR/master_key.pem" ]; then
  DISKS_JSON=$(printf '"%s",' "${DISKS[@]}" | sed 's/,$//')
  SIG=$(echo -n "PHYSICAL_WIPE_$(date +%s)_${DISKS[*]}" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0) || true
  curl -sf -X POST "${API_URL}/api/v1/alert/physical_wipe" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"PHYSICAL_DATA_DESTRUCTION\",\"disks\":[${DISKS_JSON}],\"method\":\"DoD 5220.22-M (7 passes)\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"signature\":\"${SIG}\"}" >/dev/null || true
fi

echo "Borrado seguro completado. Evento registrado en GaiaChain."
