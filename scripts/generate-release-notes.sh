#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-${GITHUB_REF_NAME:-unreleased}}"
OUTPUT="${2:-docs/RELEASE-NOTES.md}"
DATE_UTC="$(date -u +"%Y-%m-%d %H:%M UTC")"
mkdir -p "$(dirname "$OUTPUT")"

cat > "$OUTPUT" <<EOF
# Release Notes

## $TAG

Generado automaticamente: $DATE_UTC

### Entregables incluidos
- Automatizacion GitHub Goldfish con workflows E2E.
- Validacion de seguridad, tests y documentacion.
- Artefactos: resumen visual, changelog y PDF de release.
- Integraciones: Slack, Email, FastAPI, n8n y TimescaleDB.

### Validaciones esperadas
- Tests Python y JS en verde.
- make validate exitoso.
- Escaneo Trivy sin vulnerabilidades criticas.
- Healthchecks de staging/produccion operativos.
EOF

echo "Generated $OUTPUT"
