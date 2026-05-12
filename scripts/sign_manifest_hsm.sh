#!/usr/bin/env bash
# Firma PKCS#11 del manifiesto gemelo (Ladanum) — clave no sale del HSM.
set -euo pipefail

GEMELO_ID="${1:?gemelo_id}"
SNAPSHOT="${2:?snapshot}"
DIR="./CASTUO_package/${GEMELO_ID}"
MANIFEST="${DIR}/manifest_${GEMELO_ID}_v${SNAPSHOT}.json"
CANON="${MANIFEST}.canonical.json"

if [[ ! -f "$MANIFEST" ]]; then
  echo "No existe $MANIFEST" >&2
  exit 1
fi

PKCS11_MODULE="${PKCS11_MODULE:-/usr/lib/libcloudhsm_pkcs11.so}"
KEY_LABEL="${HSM_KEY_LABEL:-castuo_manifest_key}"

jq -S . "$MANIFEST" > "$CANON"

pkcs11-tool --module "$PKCS11_MODULE" --login --pin "${HSM_PIN:?}" \
  --sign --mechanism SHA256-RSA-PKCS \
  --keypair-label "$KEY_LABEL" \
  --input-file "$CANON" --output-file "${CANON}.sig"

SIG_B64=$(base64 -w0 "${CANON}.sig" 2>/dev/null || base64 "${CANON}.sig" | tr -d '\n')
jq --arg s "$SIG_B64" --arg k "$KEY_LABEL" \
  '. + {signatures: {manifest: {HSM_ID: $k, signature: $s}}}' "$CANON" > "${MANIFEST}.signed"

echo "Manifiesto firmado: ${MANIFEST}.signed"
