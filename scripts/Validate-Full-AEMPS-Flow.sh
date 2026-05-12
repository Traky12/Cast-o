#!/bin/bash
# scripts/Validate-Full-AEMPS-Flow.sh
#
# Flujo staging (repo-verificable):
#  1) Levantar backend staging + preparar AEMPS_WEBHOOK_SECRET
#  2) Generar certificado de prueba AEMPS (backend staging)
#  3) Auditar (detallado) usando evidencia disponible
#  4) Verificacion publica del certificado (alias /api/certificates/verify/{tx_hash})
#  5) Simular notificacion AEMPS (webhook) con validacion de firma
#  6) Emitir VALIDATION_REPORT.md

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TrialId="${TrialId:-CT-2026-001}"
BackendUrl="${BackendUrl:-http://localhost:8000}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.staging}"

PS_BIN="${PS_BIN:-powershell}"
if command -v pwsh >/dev/null 2>&1; then
  PS_BIN="pwsh"
elif command -v powershell >/dev/null 2>&1; then
  PS_BIN="powershell"
fi

GEN_SCRIPT="$ROOT_DIR/scripts/Generate-AEMPS-TrialCertificate.ps1"
SETUP_SCRIPT="$ROOT_DIR/scripts/Setup-AEMPS-Webhook-Staging.sh"
AUCHEK_SCRIPT="$ROOT_DIR/scripts/Audit-CannabisTrial-Detailed.ps1"
VERIFY_SCRIPT="$ROOT_DIR/scripts/Verify-PublicCertificate.ps1"

REPORT_PATH="$ROOT_DIR/VALIDATION_REPORT.md"

log() {
  echo "[ValidateFullAEMPS] $*"
}

require_file() {
  if [[ ! -f "$1" ]]; then
    echo "Missing: $1" >&2
    exit 1
  fi
}

require_file "$GEN_SCRIPT"
require_file "$SETUP_SCRIPT"
require_file "$AUCHEK_SCRIPT"
require_file "$VERIFY_SCRIPT"

log "1) Setup staging (backend + AEMPS_WEBHOOK_SECRET)"
"$SETUP_SCRIPT"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

AEMPS_WEBHOOK_SECRET="$(grep -E '^AEMPS_WEBHOOK_SECRET=' "$ENV_FILE" | tail -n 1 | cut -d'=' -f2-)"
if [[ -z "$AEMPS_WEBHOOK_SECRET" ]]; then
  echo "AEMPS_WEBHOOK_SECRET not found in $ENV_FILE" >&2
  exit 1
fi

log "2) Generate certificate (staging backend)"

"$PS_BIN" -NoProfile -ExecutionPolicy Bypass -File "$GEN_SCRIPT" `
  -TrialId "$TrialId" `
  -BackendUrl "$BackendUrl" `
  -LogEventInBackend:$true `
  | cat

CERT_JSON_PATH="$ROOT_DIR/certificates/aemps/$TrialId/certificate.json"
if [[ ! -f "$CERT_JSON_PATH" ]]; then
  echo "Missing certificate json: $CERT_JSON_PATH" >&2
  exit 1
fi

log "3) Extract tx_hash from certificate.json"
TX_HASH="$("$PS_BIN" -NoProfile -ExecutionPolicy Bypass -Command "($json = Get-Content -Raw -Path '$CERT_JSON_PATH' | ConvertFrom-Json); $json.sovereign_certificate.gaiachain_tx" )"
TX_HASH="$(echo "$TX_HASH" | tr -d '\r\n' | xargs || true)"
if [[ -z "$TX_HASH" ]]; then
  echo "Could not extract gaiachain_tx from $CERT_JSON_PATH" >&2
  exit 1
fi

log "4) Audit detailed (using tx_hash)"
"$PS_BIN" -NoProfile -ExecutionPolicy Bypass -File "$AUCHEK_SCRIPT" `
  -TrialId "$TrialId" `
  -BackendUrl "$BackendUrl" `
  -TxHash "$TX_HASH" `
  | cat

log "5) Public verification (alias /api/certificates/verify/{tx_hash})"
"$PS_BIN" -NoProfile -ExecutionPolicy Bypass -File "$VERIFY_SCRIPT" `
  -TxHash "$TX_HASH" `
  -BackendUrl "$BackendUrl" `
  | cat

log "6) Simulate webhook AEMPS (signature valid)"

WEBHOOK_URL="$BackendUrl/api/aemps/webhook"
payload='{"event_type":"certificate_verification","trial_id":"'"$TrialId"'","tx_id":"'"$TX_HASH"'","status":"verified","timestamp":"'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}'

expected_sig="$(printf "%s%s" "$payload" "$AEMPS_WEBHOOK_SECRET" | sha256sum | awk '{print $1}')"

curl -sS -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-AEMPS-Event: certificate_verification" \
  -H "X-AEMPS-Signature: $expected_sig" \
  -d "$payload" | cat

log "7) Write VALIDATION_REPORT.md"
cat > "$REPORT_PATH" <<EOF
VALIDATION_REPORT (staging)
=============================
TrialId: $TrialId
BackendUrl: $BackendUrl
TX_HASH: $TX_HASH

1) Certificate generated:
  - $ROOT_DIR/certificates/aemps/$TrialId/certificate.json
  - $ROOT_DIR/certificates/aemps/$TrialId/CERTIFICADO-$TrialId.md

2) Detailed audit:
  - $ROOT_DIR/audits/detailed/$TrialId/audit_report.json
  - $ROOT_DIR/audits/detailed/$TrialId/AUDITORIA-DETALLADA-$TrialId.md

3) Webhook endpoint:
  - POST $WEBHOOK_URL

EOF

log "Done. Report: $REPORT_PATH"

