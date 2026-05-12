#!/usr/bin/env bash
# export_trl6_evidence.sh — JUnit + manifiesto JSON (POSIX)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/reports/trl6"
mkdir -p "$OUT"
export PYTHONPATH="$ROOT"
cd "$ROOT"

echo "[TRL6 evidence] pytest -> $OUT/junit.xml"
set +e
python -m pytest -m trl6 -q --junit-xml="$OUT/junit.xml" 2>&1 | tee "$OUT/pytest-console.txt"
XC=$?
set -e

GIT_COMMIT=""
if command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse HEAD >/dev/null 2>&1; then
  GIT_COMMIT="$(git -C "$ROOT" rev-parse HEAD)"
fi
PY_VER="$(python -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"

export ROOT XC GIT_COMMIT PY_VER OUT
python <<'PYCODE'
import json, os, sys, datetime
root = os.environ["ROOT"]
xc = int(os.environ["XC"])
git = (os.environ.get("GIT_COMMIT") or "").strip() or None
py = os.environ["PY_VER"].strip()
out = os.environ["OUT"]
manifest = {
    "schema": "castuo.trl6_evidence.v1",
    "generated_at_utc": datetime.datetime.now(datetime.timezone.utc)
    .replace(microsecond=0)
    .isoformat()
    .replace("+00:00", "Z"),
    "repository_root": root,
    "git_commit": git,
    "python": py,
    "pytest_marker": "trl6",
    "pytest_exit_code": xc,
    "artifacts": {
        "junit_xml": "reports/trl6/junit.xml",
        "console_log": "reports/trl6/pytest-console.txt",
    },
    "legal_note": "Artefactos de prueba; no sustituyen DPIA ni firma DPO.",
}
with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
    f.write("\n")
sys.exit(xc)
PYCODE
