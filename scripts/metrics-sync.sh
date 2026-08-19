#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p logs

count_sync_errors=0
if ls logs/sync-failure-*.log > /dev/null 2>&1; then
  count_sync_errors=$( (grep -h -c "ERROR" logs/sync-failure-*.log || true) | awk '{s+=$1} END {print s+0}')
fi

count_retries=0
if [[ -f "logs/agent-actions.log" ]]; then
  count_retries=$(grep -c "retry_count" logs/agent-actions.log || true)
fi

count_mgt_errors=0
if ls logs/*.log > /dev/null 2>&1; then
  count_mgt_errors=$( (grep -h -c "mgt.clearMarks" logs/*.log || true) | awk '{s+=$1} END {print s+0}')
fi

drift=0
# metrics.prom is the generated output of this script and must not self-report drift.
# Keep every other working-tree change fail-closed.
working_tree_changes=$(git status --porcelain --untracked-files=all | awk '$2 != "metrics.prom"')
if [[ -n "$working_tree_changes" ]]; then
  drift=1
fi

echo "# HELP castuo_agent_sync_errors Numero de errores de sincronizacion"
echo "# TYPE castuo_agent_sync_errors gauge"
echo "castuo_agent_sync_errors ${count_sync_errors}"

echo "# HELP castuo_agent_sync_retries Numero de reintentos por agente"
echo "# TYPE castuo_agent_sync_retries gauge"
echo "castuo_agent_sync_retries ${count_retries}"

echo "# HELP castuo_agent_drift_detection Drift detectado (0=OK, 1=DRIFT)"
echo "# TYPE castuo_agent_drift_detection gauge"
echo "castuo_agent_drift_detection ${drift}"

echo "# HELP castuo_agent_mgt_clearmarks_errors Errores mgt.clearMarks observados"
echo "# TYPE castuo_agent_mgt_clearmarks_errors gauge"
echo "castuo_agent_mgt_clearmarks_errors ${count_mgt_errors}"
