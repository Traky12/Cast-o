#!/usr/bin/env bash
# Agrega documentos clave del repo en un único Markdown (due diligence / Serie A).
# Salida: CASTUO_REPORT_OUT o <raíz>/agri_brain_series_a_report.md
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${CASTUO_REPORT_OUT:-$ROOT/agri_brain_series_a_report.md}"
TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

{
  printf '%s\n\n' "# CASTÚO-SYSTEM — informe técnico agregado (generado ${TS} UTC)"
  printf '%s\n\n' "Este fichero es una **copia de lectura** de rutas versionadas; la fuente de verdad sigue siendo cada documento en su ruta original."

  for f in \
    "docs/INTEGRACION-MAESTRA-N8N-GEMELO-DIGITAL.md" \
    "docs/ops/failover-strategy.md" \
    "docs/ops/opex-trillizo-integration.md" \
    "n8n/README-AGRI-BRAIN.md" \
    "n8n/README-MULTI-N8N.md"
  do
    if [[ -f "$ROOT/$f" ]]; then
      printf '%s\n\n' "## --- Inicio: $f ---"
      cat "$ROOT/$f"
      printf '\n\n%s\n\n' "## --- Fin: $f ---"
    fi
  done
} >"$OUT"

echo "Escrito: $OUT"
