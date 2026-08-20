#!/usr/bin/env bash
set -euo pipefail

out_dir="artifacts/operativity/trl9"
out_file="$out_dir/go-nogo-status.md"
mkdir -p "$out_dir"

cat > "$out_file" <<'EOF'
# CASTÚO TRL9 Gate Status

- Operatividad tecnica 48h: REVIEW
- TRL 9 (certificacion externa): NO-GO
- Promotion effect: BLOCKED
- Claim boundary: NO_CERTIFICATION_CLAIM

## Evidence boundary

This artifact is a deterministic gate status record. It does not certify TRL9, field operation, production readiness or external assurance. `GO` requires an independent external certification artifact linked by immutable evidence ID, reviewer, timestamp and scope.

Este artefacto es un registro determinista del gate. No certifica TRL9, operación de campo, readiness de producción ni assurance externo. `GO` requiere un artefacto de certificación externa independiente enlazado por ID de evidencia inmutable, reviewer, timestamp y alcance.
EOF

printf '[OK] TRL9 gate status written: %s\n' "$out_file"
