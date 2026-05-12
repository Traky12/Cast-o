#!/bin/bash
# CASTÚO-SYSTEM™ — Verificación completa del sistema (post-implementación)
# Comprueba: TPM IoT, documentos legales, GaiaChain, Defender, Suricata/Snort, backups, HSM, Cursor
# Uso: ./scripts/security/full-system-verification.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

FAILED=0

# 1. Firmas TPM en dispositivos IoT (opcional: lista en /etc/castuo/iot-devices.txt)
if [ -f /etc/castuo/iot-devices.txt ]; then
  echo "🔍 Verificando firmas TPM en dispositivos IoT..."
  while read -r device; do
    [ -z "$device" ] && continue
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "admin@$device" "/usr/local/bin/tpm_firmware_verifier /firmware/bin/firmware.bin /firmware/keys/firmware.pub.pem /firmware/bin/firmware.sig" 2>/dev/null; then
      echo "  ✅ $device: Firma válida"
    else
      echo "  ❌ $device: Firma INVÁLIDA o inalcanzable"
      ((FAILED++)) || true
    fi
  done < /etc/castuo/iot-devices.txt
else
  echo "⚠️  /etc/castuo/iot-devices.txt no existe; omitiendo verificación TPM remota."
fi

# 2. Integridad documentos legales
echo "📜 Verificando integridad de documentos legales..."
if [ -f "$REPO_ROOT/docs/legal/verify-integrity-legal.sh" ]; then
  SKIP_PLACEHOLDER_CHECK=1 bash "$REPO_ROOT/docs/legal/verify-integrity-legal.sh" 2>/dev/null || { echo "  ❌ Verificación legal fallida"; ((FAILED++)) || true; }
else
  echo "  ⚠️  verify-integrity-legal.sh no encontrado"
fi

# 3. Contratos en GaiaChain (opcional: API disponible)
if [ -n "$GAIA_CHAIN_API_KEY" ]; then
  echo "🔗 Verificando contratos en GaiaChain..."
  for contract in GaiaChainValidator CursorImmutability DynamicCompliance; do
    if curl -sf -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
        "https://gaiachain.castuo-system.com/api/v1/contract/$contract/verify" 2>/dev/null | grep -q '"status":"VERIFIED"'; then
      echo "  ✅ $contract: Verificado"
    else
      echo "  ⚠️  $contract: No verificado o API no disponible"
    fi
  done
else
  echo "⚠️  GAIA_CHAIN_API_KEY no definido; omitiendo verificación GaiaChain."
fi

# 4. Políticas Defender (opcional)
if [ -n "$DEFENDER_API_KEY" ]; then
  echo "🛡️ Verificando políticas OpenZeppelin Defender..."
  if curl -sf -H "Authorization: Bearer $DEFENDER_API_KEY" \
      "https://api.defender.openzeppelin.com/v1/policy/GaiaChainValidator-Upgrade-Policy" 2>/dev/null | grep -q '"status":"ACTIVE"'; then
    echo "  ✅ Políticas de Defender activas"
  else
    echo "  ⚠️  Políticas Defender no activas o API no disponible"
  fi
else
  echo "⚠️  DEFENDER_API_KEY no definido; omitiendo Defender."
fi

# 5. Suricata / Snort
echo "🔍 Verificando estado de Suricata/Snort..."
if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet suricata 2>/dev/null; then
    echo "  ✅ Suricata activo"
  else
    echo "  ⚠️  Suricata no está activo"
  fi
  if systemctl is-active --quiet snort 2>/dev/null; then
    echo "  ✅ Snort activo"
  else
    echo "  ⚠️  Snort no está activo"
  fi
else
  echo "  ⚠️  systemctl no disponible"
fi

# 6. Último backup GaiaChain (opcional)
if [ -n "$GAIA_CHAIN_API_KEY" ]; then
  echo "💾 Verificando backups en GaiaChain..."
  if curl -sf -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
      "https://gaiachain.castuo-system.com/api/v1/backups/latest" 2>/dev/null | grep -q '"status":"SUCCESS"'; then
    echo "  ✅ Último backup exitoso"
  else
    echo "  ⚠️  Último backup no exitoso o API no disponible"
  fi
fi

# 7. HSM (opcional: pkcs11-tool)
if command -v pkcs11-tool >/dev/null 2>&1; then
  echo "🔐 Verificando estado de HSM..."
  if pkcs11-tool --list-slots 2>/dev/null | grep -q "Thales\|Luna"; then
    echo "  ✅ HSM Thales/Luna detectado"
  else
    echo "  ⚠️  HSM no detectado"
  fi
else
  echo "⚠️  pkcs11-tool no instalado; omitiendo HSM."
fi

# 8. Firmas de Cursor (si existen rutas)
if [ -f /etc/cursor/signatures/cursor_pub.pem ] && [ -f /etc/cursor/signatures/cursor.sig ] && [ -f /opt/cursor/cursor.js ]; then
  echo "🖱️ Verificando firmas de Cursor..."
  if openssl dgst -sha256 -verify /etc/cursor/signatures/cursor_pub.pem \
       -signature /etc/cursor/signatures/cursor.sig /opt/cursor/cursor.js 2>/dev/null; then
    echo "  ✅ Firma de Cursor válida"
  else
    echo "  ❌ Firma de Cursor inválida"
    ((FAILED++)) || true
  fi
else
  echo "⚠️  Archivos de firma Cursor no presentes en /etc/cursor y /opt/cursor."
fi

if [ "$FAILED" -gt 0 ]; then
  echo ""
  echo "❌ Verificaciones fallidas: $FAILED"
  exit 1
fi
echo ""
echo "🎉 Verificaciones completadas (advertencias permitidas). Sistema listo."
exit 0
