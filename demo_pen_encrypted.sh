#!/bin/bash
# demo_pen_encrypted.sh - 1-CLIC ejecutable desde PEN_D (tras desencriptar)
# Ejecutar: tar -xzf demo_backup.tar.gz && bash demo_pen_encrypted.sh
# (o desde carpeta extraída: cd DEMO_CTAEX_1000AM && bash ../demo_pen_encrypted.sh)
# PEN_D: ENCRIPTADO KYBER2048 + BACKUP TRL9 EXECUTABLE → CTAEX €500K

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
export DEMO_ROOT="${DEMO_ROOT:-$REPO_ROOT/DEMO_CTAEX_1000AM}"
exec bash "$SCRIPT_DIR/DEMO_CTAEX_1000AM.sh" "$DEMO_ROOT"
