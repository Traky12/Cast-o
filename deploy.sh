#!/usr/bin/env bash
# Despliegue CASTÚO producción (este script vive en la raíz del repo).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.prod.yml"
ENV_FILE="$ROOT_DIR/.env.production"
COMPOSE=(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE")

REMOTE_PATH="${REMOTE_PATH:-/opt/castuo-system}"
HETZNER_USER="${HETZNER_USER:-root}"

_usage() {
  cat <<'HELP'
Uso:
  ./deploy.sh --full              # build+up local, o rsync+compose si HETZNER_IP está definida
  ./deploy.sh --remote            # rsync repo → servidor + compose
  ./deploy.sh --status            # docker compose ps + /health
  ./deploy.sh --api               # rebuild + up solo api
  ./deploy.sh --n8n               # pull + up solo n8n
  ./deploy.sh --nginx            # recrea solo nginx (tras editar castuo.conf)
  ./deploy.sh --rollback         # imagen castuo-api:previous (etiquetar antes)
  ./deploy.sh --local            # up -d sin build
  ./deploy.sh --build            # build api + up -d

Variables:
  HETZNER_IP     IP CX22 (--full / --remote)
  HETZNER_USER   default root
  REMOTE_PATH    default /opt/castuo-system
  CASTUO_VERIFY_TOKENS_BEFORE_UP=1  opcional: ejecuta scripts/verify_castuo_tokens.py antes de compose
  CASTUO_TOKENS_PATH  ruta comprobada por verify (default /mnt/castuo_secure/tokens)

Rollback:
  docker tag castuo-api:prod castuo-api:previous
HELP
}

_ensure_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Falta .env.production (cp .env.production.example .env.production)" >&2
    exit 1
  fi
}

_maybe_verify_tokens() {
  if [[ "${CASTUO_VERIFY_TOKENS_BEFORE_UP:-}" != "1" ]]; then
    return 0
  fi
  if [[ ! -f "$ROOT_DIR/scripts/verify_castuo_tokens.py" ]]; then
    echo "Advertencia: No se encontró scripts/verify_castuo_tokens.py (se omite verificación)" >&2
    return 0
  fi
  python3 "$ROOT_DIR/scripts/verify_castuo_tokens.py" || exit 1
}

_do_local() {
  cd "$ROOT_DIR"
  _ensure_env
  _maybe_verify_tokens
  "${COMPOSE[@]}" "$@"
}

_do_remote() {
  [[ -n "${HETZNER_IP:-}" ]] || { echo "Define HETZNER_IP" >&2; exit 1; }
  RSYNC_TARGET="${HETZNER_USER}@${HETZNER_IP}:${REMOTE_PATH}"
  echo "==> rsync → $RSYNC_TARGET"
  rsync -az --delete \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '.venv' \
    --exclude 'node_modules' \
    "$ROOT_DIR/" "$RSYNC_TARGET/"
  echo "==> compose remoto"
  ssh "${HETZNER_USER}@${HETZNER_IP}" bash -s <<REMOTE
set -euo pipefail
cd "$REMOTE_PATH"
docker compose -f docker-compose.prod.yml --env-file .env.production pull n8n nginx postgres 2>/dev/null || true
docker compose -f docker-compose.prod.yml --env-file .env.production build --no-cache api
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
docker compose -f docker-compose.prod.yml ps
REMOTE
}

_do_status() {
  cd "$ROOT_DIR"
  _ensure_env
  "${COMPOSE[@]}" ps
  echo ""
  echo "==> Health (nginx :80):"
  curl -fsS "http://127.0.0.1/health" 2>/dev/null || echo "(sin respuesta en :80)"
}

_do_rollback() {
  cd "$ROOT_DIR"
  _ensure_env
  if ! docker image inspect castuo-api:previous >/dev/null 2>&1; then
    echo "No existe castuo-api:previous. Antes del deploy: docker tag castuo-api:prod castuo-api:previous" >&2
    exit 1
  fi
  docker tag castuo-api:prod castuo-api:rollback-broken 2>/dev/null || true
  docker tag castuo-api:previous castuo-api:prod
  "${COMPOSE[@]}" up -d --no-build api
  echo "==> API restaurada desde castuo-api:previous."
}

case "${1:-}" in
  --help|-h) _usage; exit 0 ;;
  --remote) shift; _do_remote "$@" ;;
  --local) shift; _do_local up -d "$@" ;;
  --build) shift; _do_local build --no-cache "$@" && _do_local up -d "$@" ;;
  --status) _do_status ;;
  --api) _do_local build --no-cache api && _do_local up -d api ;;
  --n8n) _do_local pull n8n && _do_local up -d n8n ;;
  --nginx) _do_local up -d --force-recreate nginx ;;
  --rollback) _do_rollback ;;
  --full)
    if [[ -n "${HETZNER_IP:-}" ]]; then
      _do_remote
    else
      _do_local build --no-cache api && _do_local up -d
    fi
    ;;
  *)
    _usage
    exit 1
    ;;
esac

echo "==> Listo."
