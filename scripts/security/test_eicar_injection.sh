#!/bin/bash
# scripts/security/test_eicar_injection.sh
#
# Crea el archivo de prueba EICAR (estandar de antivirus) y simula una inyeccion segura
# en el repositorio (sin enviar datos a servicios externos).
#
# Opcional:
#   - EICAR_SCAN_CMD: comando shell para validar deteccion local (ej: "clamscan")
#   - EICAR_INJECT_DIR: ruta donde copiar el fichero (por defecto ./tmp/security-eicar)

set -euo pipefail

EICAR_SIGNATURE="X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
EICAR_FILE_TMP="${EICAR_FILE_TMP:-/tmp/eicar_test.txt}"

EICAR_INJECT_DIR="${EICAR_INJECT_DIR:-./tmp/security-eicar}"
SCAN_CMD="${EICAR_SCAN_CMD:-}"

mkdir -p "$EICAR_INJECT_DIR"

echo "$EICAR_SIGNATURE" > "$EICAR_FILE_TMP"

TARGET_FILE="$EICAR_INJECT_DIR/eicar_test_$(date -u +%Y%m%dT%H%M%SZ).txt"
cp "$EICAR_FILE_TMP" "$TARGET_FILE"

echo "EICAR file created:"
echo " - temp: $EICAR_FILE_TMP"
echo " - injected: $TARGET_FILE"

if [[ -n "$SCAN_CMD" ]]; then
  echo "Running scan command: $SCAN_CMD $TARGET_FILE"
  # shellcheck disable=SC2086
  $SCAN_CMD $TARGET_FILE || true
  echo "Scan complete (check output above)."
else
  echo "EICAR_SCAN_CMD not set; skipping scan verification (por validar en despliegue)."
fi

