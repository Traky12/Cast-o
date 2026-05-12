#!/usr/bin/env bash
set -euo pipefail

: "${VAULT_ADDR:?VAULT_ADDR is required}"
: "${VAULT_TOKEN:?VAULT_TOKEN is required}"

vault token renew -address="$VAULT_ADDR" "$VAULT_TOKEN" >/dev/null
echo "Vault token renewed successfully"
