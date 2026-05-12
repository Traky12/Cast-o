#!/usr/bin/env bash
# bootstrap-hetzner.sh — v1.1 — instala unidades Castúo + overrides IoT para REPO en /opt (servidor).
# Documentación: docs/ops/PRONTUARIO-MAESTRO-DEPLOY-REAL-HETZNER.md
#
# Uso (como root en el servidor, con el repo ya en REPO_BASE):
#   CASTUO_REPO_BASE=/opt/castuo-system CASTUO_USER=castuo ./scripts/deploy/bootstrap-hetzner.sh
#   CASTUO_BACKEND_URL=http://127.0.0.1:8000 ./scripts/deploy/bootstrap-hetzner.sh --no-start
#   ./scripts/deploy/bootstrap-hetzner.sh --dry-run
#   ./scripts/deploy/bootstrap-hetzner.sh --verify-only
#
set -euo pipefail

REPO_BASE="${CASTUO_REPO_BASE:-/opt/castuo-system}"
CASTUO_USER="${CASTUO_USER:-castuo}"
BACKEND_URL="${CASTUO_BACKEND_URL:-http://127.0.0.1:8001}"
FORCE_AGENTS_ENV="${CASTUO_FORCE_AGENTS_ENV:-0}"
DRY_RUN=0
NO_START=0
DO_STATUS=0
VERIFY_ONLY=0

_usage() {
  cat <<'HELP'
Uso: bootstrap-hetzner.sh [opciones]
  Instala overrides IoT + unidades systemd (servidor Linux, root).

Opciones:
  --verify-only  Solo systemctl + journalctl (sin tocar /etc ni agents.env)
  --dry-run      Solo muestra acciones
  --no-start     systemctl enable sin --now
  --status       Al final, systemctl status de las unidades
  -h, --help     Esta ayuda

Variables de entorno:
  CASTUO_REPO_BASE=/opt/castuo-system
  CASTUO_USER=castuo
  CASTUO_BACKEND_URL=http://127.0.0.1:8001
  CASTUO_FORCE_AGENTS_ENV=1   sobrescribe /etc/castuo-system/agents.env

Doc: docs/ops/PRONTUARIO-MAESTRO-DEPLOY-REAL-HETZNER.md
HELP
}

_verify_only() {
  echo "==> verify-only: target, unidades y últimas líneas del journal (autonomous)"
  set +e
  if systemctl is-active --quiet castuo-system.target 2>/dev/null; then
    echo "castuo-system.target: active"
  else
    echo "(!) castuo-system.target: inactivo o unidad no cargada"
  fi
  systemctl status castuo-autonomous-agents.service --no-pager || true
  for n in 1 2 3; do
    systemctl status "castuo-iot-coop${n}.service" --no-pager || true
  done
  journalctl -u castuo-autonomous-agents.service -n 20 --no-pager || true
  set -e
}

while [[ "${1:-}" == -* ]]; do
  case "$1" in
    -h|--help) _usage; exit 0 ;;
    --verify-only) VERIFY_ONLY=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --no-start) NO_START=1; shift ;;
    --status) DO_STATUS=1; shift ;;
    *) echo "Opción desconocida: $1" >&2; _usage >&2; exit 1 ;;
  esac
done

if [[ "${EUID:-0}" -ne 0 ]]; then
  echo "Ejecutar como root en el servidor (systemd, /etc)." >&2
  exit 1
fi

if [[ "$VERIFY_ONLY" -eq 1 ]]; then
  _verify_only
  exit 0
fi

_run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] %q\n' "$@"
    return 0
  fi
  "$@"
}

SD="${REPO_BASE}/scripts/systemd"
if [[ ! -d "$SD" ]]; then
  echo "No existe scripts/systemd bajo REPO_BASE=$REPO_BASE (¿repo desplegado?)" >&2
  exit 1
fi

if [[ "$REPO_BASE" != "/opt/castuo-system" ]]; then
  echo "(!) castuo-autonomous-agents.service.example asume rutas /opt/castuo-system en ExecStart; revisa la unidad copiada." >&2
fi

for f in castuo-iot-coop1.service castuo-autonomous-agents.service.example castuo-system.target.example agents.env.example; do
  if [[ ! -f "$SD/$f" ]]; then
    echo "Falta $SD/$f" >&2
    exit 1
  fi
done

NOLOGIN="$(command -v nologin 2>/dev/null || command -v false 2>/dev/null || echo /usr/sbin/nologin)"

echo "==> Castúo bootstrap: REPO_BASE=$REPO_BASE USER=$CASTUO_USER BACKEND_URL=$BACKEND_URL"

_run install -d -m 0755 "$REPO_BASE" /etc/castuo-system /var/log/castuo /var/lib/castuo-agents
_run chmod 750 /etc/castuo-system

if ! id -u "$CASTUO_USER" &>/dev/null; then
  _run useradd -r -s "$NOLOGIN" -d "$REPO_BASE" -M "$CASTUO_USER" 2>/dev/null || \
    _run useradd -r -s "$NOLOGIN" -d "$REPO_BASE" "$CASTUO_USER"
fi

_run install -d -m 0755 "$REPO_BASE/backend/logs"
_run chown -R "${CASTUO_USER}:${CASTUO_USER}" "$REPO_BASE" /var/log/castuo /var/lib/castuo-agents
_run chown "${CASTUO_USER}:${CASTUO_USER}" "$REPO_BASE/backend/logs"

for n in 1 2 3; do
  drop="/etc/systemd/system/castuo-iot-coop${n}.service.d"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] override $drop/override.conf"
  else
    install -d "$drop"
    cat >"${drop}/override.conf" <<EOF
[Service]
User=${CASTUO_USER}
Group=${CASTUO_USER}
WorkingDirectory=${REPO_BASE}/backend
Environment=BACKEND_URL=${BACKEND_URL}
Environment=IOT_MONITOR_LOG=${REPO_BASE}/backend/logs/iot-monitor-coop${n}.log
EOF
  fi
done

_run cp -f "$SD/castuo-iot-coop1.service" /etc/systemd/system/
_run cp -f "$SD/castuo-iot-coop2.service" /etc/systemd/system/
_run cp -f "$SD/castuo-iot-coop3.service" /etc/systemd/system/
_run cp -f "$SD/castuo-autonomous-agents.service.example" /etc/systemd/system/castuo-autonomous-agents.service
_run cp -f "$SD/castuo-system.target.example" /etc/systemd/system/castuo-system.target

if [[ ! -f /etc/castuo-system/agents.env ]] || [[ "$FORCE_AGENTS_ENV" == "1" ]]; then
  _run cp -f "$SD/agents.env.example" /etc/castuo-system/agents.env
  _run chmod 640 /etc/castuo-system/agents.env
  _run chown root:"$CASTUO_USER" /etc/castuo-system/agents.env
  if [[ "$FORCE_AGENTS_ENV" == "1" ]]; then
    echo "(!) agents.env sobrescrito (CASTUO_FORCE_AGENTS_ENV=1). Revisa secretos." >&2
  fi
else
  echo "(!) Conservando /etc/castuo-system/agents.env existente (CASTUO_FORCE_AGENTS_ENV=1 para reemplazar)." >&2
fi

_run systemctl daemon-reload
_run systemctl enable castuo-system.target

if [[ "$NO_START" -eq 1 ]]; then
  _run systemctl enable castuo-iot-coop1.service castuo-iot-coop2.service castuo-iot-coop3.service
  _run systemctl enable castuo-autonomous-agents.service
  echo "Unidades habilitadas sin --now. Arranca con: systemctl start ..."
else
  _run systemctl enable --now castuo-iot-coop1.service castuo-iot-coop2.service castuo-iot-coop3.service
  _run systemctl enable --now castuo-autonomous-agents.service
fi

echo "==> Listo. Oneshot autonomous puede verse como inactive (dead) con RemainAfterExit=yes — ver doc."
echo "    Editar secretos: /etc/castuo-system/agents.env"

if [[ "$DO_STATUS" -eq 1 ]] && [[ "$DRY_RUN" -eq 0 ]]; then
  systemctl status castuo-system.target --no-pager || true
  systemctl status castuo-autonomous-agents.service --no-pager || true
  systemctl status castuo-iot-coop1.service castuo-iot-coop2.service castuo-iot-coop3.service --no-pager || true
fi
