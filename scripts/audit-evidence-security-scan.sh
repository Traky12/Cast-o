#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-}"
if [[ -z "$TARGET_DIR" || ! -d "$TARGET_DIR" ]]; then
  echo "[ERROR] Usage: $0 <evidence_dir>" >&2
  exit 2
fi

# Patrones de alto riesgo para evitar filtrado de secretos en bundle
PATTERN='(ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN[[:space:]]+PRIVATE[[:space:]]+KEY|xox[baprs]-[A-Za-z0-9-]{10,})'

if grep -RIE --exclude='*.png' --exclude='*.jpg' --exclude='*.jpeg' --exclude='*.gif' "$PATTERN" "$TARGET_DIR" >/tmp/audit-evidence-security-scan.out 2>/dev/null; then
  echo "[ERROR] Posibles secretos detectados en evidencia:" >&2
  cat /tmp/audit-evidence-security-scan.out >&2
  exit 1
fi

echo "[OK] No se detectaron patrones de secretos en evidencia"
exit 0
