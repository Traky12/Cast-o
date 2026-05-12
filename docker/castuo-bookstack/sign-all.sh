#!/bin/bash
# CASTÚO-SYSTEM™ | Firma de archivos críticos (anti-tampering capa 2)
# Ejecutar tras generar claves: openssl genrsa -out castuo-private.key 4096

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PRIVATE_KEY="${CASTUO_PRIVATE_KEY:-castuo-private.key}"
if [ ! -f "$PRIVATE_KEY" ]; then
  echo "❌ Clave privada no encontrada: $PRIVATE_KEY"
  echo "   Genere con: openssl genrsa -out castuo-private.key 4096"
  exit 1
fi

echo "Firmando archivos críticos..."
for f in docker-compose.yml test-bookstack.sh n8n-workflow-sabionda-bookstack.json .env.example; do
  [ -f "$f" ] || continue
  openssl dgst -sha256 -sign "$PRIVATE_KEY" -out "${f}.sig" "$f"
  echo "  ✓ ${f} → ${f}.sig"
done
echo "✅ Firmado completado. Verifique con: ./verify-integrity.sh"
echo "   No commitear castuo-private.key. Sí puede commitear .sig y castuo-public.key."
