#!/usr/bin/env bash
# EvidenceHash SHA-256(manifest||zip) + firma HSM (Dron 360 / Nodo Zero-Water).
set -euo pipefail

GEMELO_ID="${1:?gemelo_id}"
SNAPSHOT="${2:?snapshot}"
DIR="./CASTUO_package/${GEMELO_ID}"
MANIFEST="${DIR}/manifest_${GEMELO_ID}_v${SNAPSHOT}.json"

if [[ ! -f "$MANIFEST" ]]; then
  echo "No existe $MANIFEST" >&2
  exit 1
fi

ARTIFACTS_ZIP=$(ls -1 "${DIR}"/artefacts_"${GEMELO_ID}"_v*.zip 2>/dev/null | head -n1 || true)
if [[ -z "${ARTIFACTS_ZIP}" || ! -f "$ARTIFACTS_ZIP" ]]; then
  echo "No se encontró artefacts_${GEMELO_ID}_v*.zip en $DIR" >&2
  exit 1
fi

EVIDENCE_HASH=$( (cat "$MANIFEST"; printf '\n'; cat "$ARTIFACTS_ZIP") | sha256sum | awk '{print $1}')
echo "$EVIDENCE_HASH" > "${DIR}/evidencehash_${GEMELO_ID}.txt"

# 32 bytes para mecanismos que firman digest pre-hash
if command -v xxd >/dev/null 2>&1; then
  printf '%s' "$EVIDENCE_HASH" | xxd -r -p > "${DIR}/evidencehash_raw.bin"
else
  python3 -c "import sys; sys.stdout.buffer.write(bytes.fromhex('$EVIDENCE_HASH'))" > "${DIR}/evidencehash_raw.bin"
fi

PKCS11_MODULE="${PKCS11_MODULE:?}"
HSM_PIN="${HSM_PIN:?}"
HSM_KEY_LABEL="${HSM_KEY_LABEL:?}"

pkcs11-tool --module "$PKCS11_MODULE" --login --pin "$HSM_PIN" \
  --sign --mechanism RSA-PKCS \
  --keypair-label "$HSM_KEY_LABEL" \
  --input-file "${DIR}/evidencehash_raw.bin" \
  --output-file "${DIR}/evidencehash_${GEMELO_ID}.sig"

echo "EvidenceHash $EVIDENCE_HASH firmado en ${DIR}/evidencehash_${GEMELO_ID}.sig"
