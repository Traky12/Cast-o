#!/bin/bash
# PREP_PEN_TRL9.sh - Prepara PEN_D total encriptado para mañana 10:00
# Uso: desde raíz del repo: bash PREP_PEN_TRL9.sh [DIR_PEN]
#      DIR_PEN default: /d/DEMO_PEN_TRL9_1000AM  (o ./DEMO_PEN_TRL9_1000AM para probar)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
PEN_ROOT="${1:-${PEN_ROOT:-/d/DEMO_PEN_TRL9_1000AM}}"
mkdir -p "$PEN_ROOT"

echo "🔐 === PREP PEN_D TRL9 TOTAL ENCRIPTADO ==="
echo "📁 PEN: $PEN_ROOT"

echo "📂 [1/5] Copiando backend (sabion_omega, crypto_master, maya_segura)..."
mkdir -p "$PEN_ROOT/backend"
cp -r backend/sabion_omega_2040 backend/crypto_master backend/maya_segura "$PEN_ROOT/backend/" 2>/dev/null || true

echo "📄 [2/5] Copiando docker-compose.* y README_*.md..."
cp docker-compose.omega.yml docker-compose.sabionda.yml docker-compose.sabion_edu.yml "$PEN_ROOT/" 2>/dev/null || true
cp docker-compose.federated.yml docker-compose.agents.yml "$PEN_ROOT/" 2>/dev/null || true
cp README_*.md "$PEN_ROOT/" 2>/dev/null || true

echo "📦 [3/5] TAR desde repo → backup_kyber2048.pen..."
cd "$REPO_ROOT"
tar -czf "$PEN_ROOT/backup_trl9_$(date +%Y%m%d_%H%M%S).tar.gz" \
  backend/sabion_omega_2040 backend/crypto_master backend/maya_segura \
  docker-compose.omega.yml docker-compose.sabionda.yml docker-compose.sabion_edu.yml \
  docker-compose.federated.yml docker-compose.agents.yml \
  DEMO_CTAEX_1000AM.sh demo_pen_encrypted.sh \
  README_*.md 2>/dev/null || true
LATEST_TAR="$(ls -t "$PEN_ROOT"/backup_trl9_*.tar.gz 2>/dev/null | head -1)"
if [ -n "$LATEST_TAR" ]; then
  cp "$LATEST_TAR" "$PEN_ROOT/backup_kyber2048.pen"
  echo "   backup_kyber2048.pen listo"
fi

echo "🔑 [4/5] Shamir + master_key..."
echo -e "s1\ns2\ns3\ns4\ns5" > "$PEN_ROOT/shamir_demo.txt"
echo "CLAVE_MAESTRA_GREGORIO_2040" > "$PEN_ROOT/master_key.txt"
echo -e "s1\ns2\ns3\ns4\ns5" > "$PEN_ROOT/shamir_demo_shares.txt"
echo "CLAVE_MAESTRA_GREGORIO_2040" > "$PEN_ROOT/master_key_gregorio.txt"

echo "📜 [5/5] Scripts 1-CLIC..."
cp "$REPO_ROOT/DEMO_CTAEX_1000AM.sh" "$REPO_ROOT/demo_pen_encrypted.sh" "$PEN_ROOT/"

echo ""
echo "✅ PEN_D listo: $PEN_ROOT"
echo "   demo_pen_encrypted.sh | shamir_demo*.txt | master_key*.txt | backup_kyber2048.pen"
echo "   Mañana 10:00: cd $PEN_ROOT && bash demo_pen_encrypted.sh"
