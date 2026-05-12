#!/bin/bash
# CASTÚO-SYSTEM™ | Verificación de integridad (anti-tampering capa 2)
# Comprueba firmas de archivos críticos antes de deploy. Ejecutar: ./verify-integrity.sh || exit 1

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PUBLIC_KEY="${CASTUO_PUBLIC_KEY:-castuo-public.key}"
if [ ! -f "$PUBLIC_KEY" ]; then
  echo "❌ Clave pública no encontrada: $PUBLIC_KEY"
  echo "   Genere con: openssl rsa -in castuo-private.key -pubout -out castuo-public.key"
  exit 1
fi

FAILED=0
for f in docker-compose.yml test-bookstack.sh n8n-workflow-sabionda-bookstack.json; do
  [ -f "$f" ] || continue
  sig="${f}.sig"
  if [ ! -f "$sig" ]; then
    echo "❌ $f SIN FIRMA (.sig)"
    ((FAILED++)) || true
    continue
  fi
  if ! openssl dgst -sha256 -verify "$PUBLIC_KEY" -signature "$sig" "$f" >/dev/null 2>&1; then
    echo "❌ $f MODIFICADO (verificación fallida)"
    ((FAILED++)) || true
  fi
done

if [ "$FAILED" -gt 0 ]; then
  echo "❌ INTEGRIDAD FALLIDA ($FAILED archivos)"
  exit 1
fi
echo "✅ INTEGRIDAD 100%"
