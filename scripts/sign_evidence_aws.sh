#!/usr/bin/env bash
# AWS CloudHSM: exportar PKCS11_MODULE al .so del cliente y elegir script.
set -euo pipefail
export PKCS11_MODULE="${PKCS11_MODULE:-/opt/cloudhsm/lib/libcloudhsm_pkcs11.so}"
MODE="${3:-manifest}"
if [[ "$MODE" == "evidence" ]]; then
  exec "$(dirname "$0")/sign_evidencehash_hsm_generic.sh" "${1:?}" "${2:?}"
fi
exec "$(dirname "$0")/sign_manifest_hsm.sh" "${1:?}" "${2:?}"
