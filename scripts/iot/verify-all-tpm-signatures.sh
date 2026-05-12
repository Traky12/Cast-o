#!/bin/bash
# CASTÚO-SYSTEM™ — Verificación de firmas TPM en todos los dispositivos IoT listados
# Lista de dispositivos: /etc/castuo/iot-devices.txt (uno por línea)
# Verificador instalado en cada dispositivo: /usr/local/bin/tpm_firmware_verifier

set -e
VERIFIER="/usr/local/bin/tpm_firmware_verifier"
FW_BIN="/firmware/bin/firmware.bin"
FW_PUB="/firmware/keys/firmware.pub.pem"
FW_SIG="/firmware/bin/firmware.sig"
LIST="${1:-/etc/castuo/iot-devices.txt}"

if [ ! -f "$LIST" ]; then
  echo "Uso: $0 [ruta_iot-devices.txt]"
  echo "Crear $LIST con una IP/hostname por línea (ej. 192.168.1.10)."
  exit 1
fi

FAILED=0
while read -r device; do
  [ -z "$device" ] && continue
  if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "admin@$device" "$VERIFIER $FW_BIN $FW_PUB $FW_SIG" 2>/dev/null; then
    echo "✅ $device: Firma válida"
  else
    echo "❌ $device: Falla"
    ((FAILED++)) || true
  fi
done < "$LIST"

[ "$FAILED" -gt 0 ] && exit 1
exit 0
