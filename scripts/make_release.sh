#!/usr/bin/env bash
# Paquete de despliegue sin secretos (runner seguro / air-gapped).
set -euo pipefail
VER="${1:-$(date +%Y%m%d)}"
OUT="dist/castuo-5pro-ladanum-${VER}"
mkdir -p "$OUT"
cp -r contracts "$OUT/" 2>/dev/null || true
cp -r scripts "$OUT/"
chmod +x "$OUT/scripts/hash_expediente_zip.py" 2>/dev/null || true
cp -r docs "$OUT/" 2>/dev/null || true
mkdir -p "$OUT/docs/sql"
cp -f docs/sql/*.sql "$OUT/docs/sql/" 2>/dev/null || true
cp -r tools "$OUT/" 2>/dev/null || true
find "$OUT" -name "*.pem" -delete 2>/dev/null || true
find "$OUT" -name ".env*" -delete 2>/dev/null || true
tar -czvf "${OUT}.tar.gz" -C dist "$(basename "$OUT")"
echo "Release: ${OUT}.tar.gz"
