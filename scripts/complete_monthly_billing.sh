#!/usr/bin/env bash
# Facturación del mes natural **anterior** (ejecutar día 1), reset de cuotas, recordatorios opcionales.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}:${PYTHONPATH:-}"

read -r YEAR MONTH <<< "$(python -c "import datetime as dt; t=dt.date.today().replace(day=1)-dt.timedelta(days=1); print(t.year, t.month)")"

echo "[castuo] Facturación período ${YEAR}-${MONTH}"
python scripts/reset_quotas.py
python scripts/generate_invoices.py --year "$YEAR" --month "$MONTH"
python scripts/send_invoices.py --year "$YEAR" --month "$MONTH"
python scripts/send_reminders.py || true
echo "[castuo] Hecho."
