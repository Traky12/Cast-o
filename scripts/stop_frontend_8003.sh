#!/usr/bin/env bash
set -euo pipefail

FRONTEND_PORT="${FRONTEND_PORT:-5432}"
PURGE="false"
VERBOSE="false"

log_ok() {
  echo "✅ $*"
}

log_warn() {
  echo "⚠️  $*"
}

for arg in "$@"; do
	case "$arg" in
		--check)
			if ! docker ps --format '{{.Names}}' | grep -qx 'castuo-wordpress'; then
				echo "CHECK_OK frontend detenido en ${FRONTEND_PORT}"
				exit 0
			fi
			echo "CHECK_FAIL frontend sigue activo en ${FRONTEND_PORT}" >&2
			exit 1
			;;
		--purge)
			PURGE="true"
			;;
		--verbose)
			VERBOSE="true"
			;;
		*)
			echo "Uso: $0 [--check] [--purge] [--verbose]" >&2
			exit 2
			;;
	esac
done

log() {
  if [[ "$VERBOSE" == "true" ]]; then
    echo "[$(date '+%H:%M:%S')] $*"
  fi
}

log "Deteniendo contenedores CASTÚO..."

docker stop castuo-wordpress >/dev/null 2>&1 || log "castuo-wordpress no estaba corriendo"
docker stop castuo-mariadb >/dev/null 2>&1 || log "castuo-mariadb no estaba corriendo"

log_ok "Contenedores detenidos"

if [[ "$PURGE" == "true" ]]; then
	log "Modo PURGE: eliminando contenedores y volumen..."
	docker rm -f castuo-wordpress >/dev/null 2>&1 || log "castuo-wordpress no existía"
	docker rm -f castuo-mariadb >/dev/null 2>&1 || log "castuo-mariadb no existía"
	docker volume rm castuo_mariadb_data >/dev/null 2>&1 || log_warn "No se pudo eliminar volumen castuo_mariadb_data"
	log_ok "Frontend completamente purgado (contenedores + volumen eliminados)"
	exit 0
fi

log_ok "Frontend local detenido (puerto ${FRONTEND_PORT} liberado, datos preservados)"
