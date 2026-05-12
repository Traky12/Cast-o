#!/bin/bash
# CASTÚO-SYSTEM v1.7.0 - Ritual de cierre: sellar el Manifiesto de Soberanía en el búnker.
# Uso: ./scripts/sellar_manifiesto.sh
# Requiere: SOPS instalado, PGP del Administrador configurado en .sops.yaml (TU_FINGERPRINT_PGP_AQUÍ sustituido).

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MANIFIESTO_PLAIN="security/MANIFIESTO_SOBERANIA.md"
MANIFIESTO_SOPS="security/MANIFIESTO_SOBERANIA.md.sops"
AUDIT_LOG="security/audit_manifiesto.log"

if [ ! -f "$MANIFIESTO_PLAIN" ]; then
  echo "[ERROR] No existe $MANIFIESTO_PLAIN. Crea el manifiesto en texto plano antes de sellar."
  exit 1
fi

echo "[SISTEMA] Sellando Manifiesto de Soberanía bajo Root of Trust..."

# Cifrado con SOPS (usa .sops.yaml; la regla security/.*\.sops$ aplica al destino)
sops --encrypt --output "$MANIFIESTO_SOPS" "$MANIFIESTO_PLAIN"

# Trazabilidad: hash SHA-256 en log de auditoría
HASH=$(sha256sum "$MANIFIESTO_SOPS" | awk '{print $1}')
echo "$(date -Iseconds) MANIFIESTO_SOBERANIA.md.sops SHA-256=$HASH" >> "$AUDIT_LOG"
echo "[AUDITORÍA] Hash registrado: $HASH"

# Eliminar rastro en texto plano (opcional; comentar la siguiente línea si quieres conservar el .md)
# rm -f "$MANIFIESTO_PLAIN"

# Validar el sello
./security/verify-nft-stack.sh && echo "🔒 MANIFIESTO SELLADO EN EL BÚNKER"
