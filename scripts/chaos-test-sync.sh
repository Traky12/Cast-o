#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p logs .tmp
stamp="$(date +%Y%m%d-%H%M%S)"
log_file="logs/chaos-test-${stamp}.log"
chaos_branch="chaos-sync-${stamp}"
base_branch="$(git rev-parse --abbrev-ref HEAD)"
allow_dirty=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-dirty)
      allow_dirty=1
      shift
      ;;
    --base-branch)
      base_branch="${2:-$base_branch}"
      shift 2
      ;;
    --dry-run)
      shift
      ;;
    *)
      base_branch="$1"
      shift
      ;;
  esac
done

cleanup() {
  git worktree remove -f .tmp/chaos-worktree > /dev/null 2>&1 || true
  git branch -D "$chaos_branch" > /dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[INFO] Iniciando simulacion de drift segura" | tee -a "$log_file"

if [[ -n "$(git status --porcelain)" ]]; then
  if [[ "$allow_dirty" -eq 1 ]]; then
    echo "[WARN] Working tree no limpio. Continuando en modo seguro (--allow-dirty)." | tee -a "$log_file"
  else
    echo "[ERROR] Working tree no limpio. Abortando prueba de caos." | tee -a "$log_file"
    exit 1
  fi
fi

git worktree add .tmp/chaos-worktree -b "$chaos_branch" > /dev/null

pushd .tmp/chaos-worktree > /dev/null
mkdir -p .chaos
echo "DRIFT_SIMULADO=${stamp}" > .chaos/drift_marker.txt
git add .chaos/drift_marker.txt
# Commit de simulacion: forzar identidad local y desactivar firmado GPG
# para evitar bloqueos de hardening por configuracion global del entorno.
git \
  -c user.name="castuo-chaos-bot" \
  -c user.email="chaos-bot@castuo.local" \
  -c commit.gpgsign=false \
  commit -m "test: simulate sync drift ${stamp}" > /dev/null
popd > /dev/null

echo "[INFO] Drift simulado entre ${base_branch} y ${chaos_branch}" | tee -a "$log_file"

summary_file=".tmp/chaos-reconcile-${stamp}.json"
set +e
bash scripts/reconcile.sh \
  --source-branch "$chaos_branch" \
  --target-branch "$base_branch" \
  --dry-run \
  --summary-json "$summary_file"
reconcile_status=$?
set -e

if [[ -f "$summary_file" ]]; then
  drift_flag="$(python3 -c 'import json,sys; print(str(json.load(open(sys.argv[1])).get("drift_detected", False)).lower())' "$summary_file" 2>/dev/null || echo "false")"
else
  drift_flag="false"
fi

# En prueba de caos, lo esperado es drift_detected=true con salida 1 en dry-run.
if [[ "$drift_flag" == "true" && "$reconcile_status" -eq 1 ]]; then
  echo "[OK] Reconciliacion dry-run detecto drift (resultado esperado)" | tee -a "$log_file"
elif [[ "$reconcile_status" -eq 0 ]]; then
  echo "[ERROR] No se detecto drift en simulacion de caos" | tee -a "$log_file"
  exit 1
else
  echo "[ERROR] Reconciliacion dry-run fallo de forma inesperada" | tee -a "$log_file"
  exit 1
fi

echo "[OK] Prueba de caos finalizada" | tee -a "$log_file"
