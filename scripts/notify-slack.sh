#!/usr/bin/env bash
set -euo pipefail

MESSAGE="${1:-}"
WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
CHANNEL="${SLACK_CHANNEL:-}"

if [[ -z "$MESSAGE" ]]; then
  echo "Usage: SLACK_WEBHOOK_URL=... $0 <message>"
  exit 1
fi

if [[ -z "$WEBHOOK_URL" ]]; then
  echo "SLACK_WEBHOOK_URL not configured, skipping Slack notification."
  exit 0
fi

python3 - <<'PY' "$WEBHOOK_URL" "$MESSAGE" "$CHANNEL"
import json
import sys
import urllib.request

url, message, channel = sys.argv[1], sys.argv[2], sys.argv[3]
payload = {"text": message}
if channel:
    payload["channel"] = channel

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=15) as response:
    print(f"Slack notification sent: {response.status}")
PY
