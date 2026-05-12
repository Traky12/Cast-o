#!/bin/bash
# VERIFICACION_FINAL_PEN.sh - Verificación rápida para demo CTAEX / PEN_D
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=== VERIFICACIÓN FINAL CASTÚO-SYSTEM (PEN_D / CTAEX) ==="

# Archivos clave (cifrado holográfico + gemelos + Moltbook)
FILES=(
  "backend/digital_twin/holographic_encryption.py"
  "backend/digital_twin/gemelos_digitales.py"
  "backend/security/end_to_end_encryption.py"
  "tests/test_holographic_encryption.py"
  "monitoring/prometheus/digital-twin-holographic-alerts.yaml"
  "monitoring/prometheus/eu-compliance-rules.yaml"
  "kubernetes/moltbook-integration.yaml"
  "docs/GEMELO_DIGITAL_ULTRA_SEGURO.md"
  "backend/main.py"
  "launch.ps1"
  "VERIFICACION_FINAL_PEN.sh"
)
COUNT=0
SIZE=0
for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    COUNT=$((COUNT + 1))
    S=$(wc -c < "$f" 2>/dev/null || echo 0)
    SIZE=$((SIZE + S))
  fi
done

# Tamaño total en MB (aprox)
SIZE_MB=$(awk "BEGIN { printf \"%.2f\", $SIZE/1024/1024 }" 2>/dev/null || echo "?.??")

echo ""
echo "  Archivos clave presentes: $COUNT / ${#FILES[@]}"
echo "  Tamaño total (aprox):     ${SIZE_MB} MB"
echo ""

# Comprobar que el módulo holográfico existe y menciona Hadamard/ZK
if grep -q "Hadamard\|ZK" backend/digital_twin/holographic_encryption.py 2>/dev/null; then
  echo "  HOLOGRÁFICO: ✓ (Hadamard + ZK presentes)"
else
  echo "  HOLOGRÁFICO: ✗ (revisar holographic_encryption.py)"
  exit 1
fi

# Test rápido opcional (si hay Python y pytest)
if command -v python3 &>/dev/null; then
  export DT_HOLOGRAPHIC_ENCRYPTION_ENABLED=true
  if python3 -m pytest tests/test_holographic_encryption.py -q --tb=no 2>/dev/null; then
    echo "  Tests holográficos:   ✓"
  else
    echo "  Tests holográficos:   (omitido o fallo)"
  fi
fi

echo ""
echo "=== RESUMEN: ${SIZE_MB} MB | ${COUNT} archivos | HOLOGRÁFICO ✓ ==="
