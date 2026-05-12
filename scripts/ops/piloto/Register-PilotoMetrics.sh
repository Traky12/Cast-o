#!/bin/bash
# scripts/ops/piloto/Register-PilotoMetrics.sh
#
# Scaffolding: Notariza metricas del piloto de Extremadura en GaiaChain
# respetando el contrato minimal del repo para witness:
#   { "hash", "coop_id", "ipfs_cid" }
#
# Entradas:
# - Se asume que los sensores suministran valores via comandos/lecturas que debes adaptar.
# - Este script evita hardcodear rutas especificas; debes mapear tus lecturas reales en el bloque "LECTURAS".
#
# Variables de entorno:
# - GAIA_CHAIN_API_URL: endpoint witness (ej: https://gaiachain.castuo-system.eu)
# - GAIA_CHAIN_API_KEY: token bearer para witness
# - GAIA_COOP_ID: coop id (ej: CASTUO-01-EXTREMADURA)
#
# Uso:
#   GAIA_CHAIN_API_KEY=... GAIA_COOP_ID=... bash Register-PilotoMetrics.sh

set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Falta comando: $1" >&2; exit 1; }
}

require_cmd jq
require_cmd sha256sum
require_cmd curl
require_cmd date

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.eu}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}"
GAIA_COOP_ID="${GAIA_COOP_ID:-CASTUO-01-EXTREMADURA}"

if [[ -z "$GAIA_CHAIN_API_KEY" ]]; then
  echo "[ERROR] GAIA_CHAIN_API_KEY no configurada." >&2
  exit 1
fi

WITNESS_URL="${GAIA_CHAIN_API_URL%/}/api/v1/witness"

COORD_FincaId="${FINCA_ID:-CASTUO-PILOTO-EXTREMADURA-01}"
TS_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "[PilotoMetrics] Lecturas (PLACEHOLDER) - debes adaptar a tus sensores..."

# ==========================
# LECTURAS: adaptar aqui
# ==========================
# Ejemplo de placeholders:
TEMP_EXTERIOR="${TEMP_EXTERIOR:-35.0}"
TEMP_INTERIOR="${TEMP_INTERIOR:-22.5}"
HUMEDAD_RELATIVA="${HUMEDAD_RELATIVA:-70.0}"
PV_POWER_W="${PV_POWER_W:-180.0}"
GEOTERMIA_FLUX="${GEOTERMIA_FLUX_WM2:-25.0}"
PH="${PH:-6.0}"
CE="${CE:-2.0}"
CONSUMO_KWH="${CONSUMO_KWH:-3.2}"
PRODUCCION_KG_MM="${PRODUCCION_KG_MM:-1.1}"

METRICS="$(jq -n \
  --arg finca_id "$COORD_FincaId" \
  --arg temp_exterior "$TEMP_EXTERIOR" \
  --arg temp_interior "$TEMP_INTERIOR" \
  --arg humedad_relativa "$HUMEDAD_RELATIVA" \
  --arg pv_power_w "$PV_POWER_W" \
  --arg geotermia_flux_wm2 "$GEOTERMIA_FLUX" \
  --arg ph "$PH" \
  --arg ce "$CE" \
  --arg consumo_kwh "$CONSUMO_KWH" \
  --arg produccion_kg_m2 "$PRODUCCION_KG_MM" \
  --arg timestamp "$TS_UTC" \
  '{
    finca_id: $finca_id,
    temp_exterior: ($temp_exterior|tonumber),
    temp_interior: ($temp_interior|tonumber),
    humedad_relativa: ($humedad_relativa|tonumber),
    pv_power_w: ($pv_power_w|tonumber),
    geotermia_flux_wm2: ($geotermia_flux_wm2|tonumber),
    ph: ($ph|tonumber),
    ce: ($ce|tonumber),
    consumo_kwh: ($consumo_kwh|tonumber),
    produccion_kg_m2: ($produccion_kg_m2|tonumber),
    timestamp: $timestamp
  }')"

HASH="$(echo "$METRICS" | jq -c . | sha256sum | awk '{print $1}')"

payload="$(python3 - <<'PY'
import json, os
hashv = os.environ["HASH"]
coop = os.environ["GAIA_COOP_ID"]
out = {"hash": hashv, "coop_id": coop, "ipfs_cid": None}
print(json.dumps(out, separators=(",", ":"), sort_keys=True))
PY
)"

echo "[PilotoMetrics] Notarizando witness en GaiaChain..."
response="$(curl -sS -X POST "$WITNESS_URL" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$payload" || true)"

echo "[PilotoMetrics] Done. hash=$HASH response=$response"

