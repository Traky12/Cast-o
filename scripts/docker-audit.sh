#!/usr/bin/env bash
set -euo pipefail

SHOW_ALL=false
STRICT=false

for arg in "$@"; do
  case "$arg" in
    --all)
      SHOW_ALL=true
      ;;
    --strict)
      STRICT=true
      ;;
    -h|--help)
      echo "Uso: $0 [--all] [--strict]"
      echo "  --all     Audita tambien contenedores detenidos"
      echo "  --strict  Devuelve exit code 2 si hay advertencias"
      exit 0
      ;;
    *)
      echo "Argumento no soportado: $arg" >&2
      echo "Uso: $0 [--all] [--strict]" >&2
      exit 2
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] docker no esta disponible en PATH." >&2
  exit 1
fi

if "$SHOW_ALL"; then
  mapfile -t CONTAINERS < <(docker ps -aq)
else
  mapfile -t CONTAINERS < <(docker ps -q)
fi

if [[ ${#CONTAINERS[@]} -eq 0 ]]; then
  echo "[INFO] No hay contenedores para auditar."
  exit 0
fi

warn_count=0
ok_count=0

echo "=== Docker Audit Report ==="
echo "Fecha: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "Modo: $([[ "$SHOW_ALL" == true ]] && echo "all" || echo "running-only")"
echo

for cid in "${CONTAINERS[@]}"; do
  name="$(docker inspect -f '{{.Name}}' "$cid" | sed 's#^/##')"
  image="$(docker inspect -f '{{.Config.Image}}' "$cid")"
  status="$(docker inspect -f '{{.State.Status}}' "$cid")"
  restart="$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$cid")"
  health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid")"
  mem_limit="$(docker inspect -f '{{.HostConfig.Memory}}' "$cid")"
  cpu_limit="$(docker inspect -f '{{.HostConfig.NanoCpus}}' "$cid")"

  echo "- Contenedor: $name"
  echo "  Imagen: $image"
  echo "  Estado: $status"
  echo "  RestartPolicy: ${restart:-none}"
  echo "  Healthcheck: $health"

  # Regla 1: evitar latest o tag ausente
  if [[ "$image" == *":latest" ]] || [[ "$image" != *":"* ]]; then
    echo "  [WARN] Imagen mutable (usa latest o no tiene tag fijo)."
    ((warn_count+=1))
  fi

  # Regla 2: restart policy recomendada
  if [[ -z "$restart" || "$restart" == "no" ]]; then
    echo "  [WARN] Sin restart policy (recomendado: unless-stopped)."
    ((warn_count+=1))
  fi

  # Regla 3: healthcheck recomendado
  if [[ "$health" == "none" ]]; then
    echo "  [WARN] Sin healthcheck definido."
    ((warn_count+=1))
  fi

  # Regla 4: limites de recursos
  if [[ "$mem_limit" == "0" ]]; then
    echo "  [WARN] Sin limite de memoria."
    ((warn_count+=1))
  fi
  if [[ "$cpu_limit" == "0" ]]; then
    echo "  [WARN] Sin limite de CPU."
    ((warn_count+=1))
  fi

  # Regla 5: puertos expuestos en todas las interfaces
  while IFS= read -r line; do
    if [[ "$line" == *"0.0.0.0:"* || "$line" == *":::"* ]]; then
      echo "  [WARN] Puerto expuesto globalmente: $line"
      ((warn_count+=1))
    fi
  done < <(docker port "$cid" 2>/dev/null || true)

  # Regla 6: nombre no descriptivo (heuristica)
  if [[ "$name" =~ ^[a-z]+$ || "$name" =~ ^[a-z]+_[a-z]+$ ]]; then
    echo "  [WARN] Nombre potencialmente poco descriptivo: $name"
    ((warn_count+=1))
  else
    ((ok_count+=1))
  fi

  echo

done

echo "Resumen:"
echo "  Contenedores evaluados: ${#CONTAINERS[@]}"
echo "  Checks OK (nombre descriptivo): $ok_count"
echo "  Advertencias totales: $warn_count"

if "$STRICT" && [[ $warn_count -gt 0 ]]; then
  echo "[RESULT] FAIL (strict): hay advertencias." >&2
  exit 2
fi

echo "[RESULT] OK: auditoria completada."
