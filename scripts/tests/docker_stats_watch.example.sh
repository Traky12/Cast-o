#!/usr/bin/env bash
# Ejemplo: monitorizar contenedores durante stress_gateway_injection.py
# Sustituye los nombres por los de `docker ps --format '{{.Names}}'` en tu host.
#
# Standalone n8n (docker-compose.n8n-castuo.yml): suele ser solo n8n-castuo
# Multi-instancia: ver docker-compose.multi-n8n.yml y n8n/README-MULTI-N8N.md
#
# Linux (paquete procps):
#   watch -n 1 'docker stats --no-stream n8n-castuo'
#
# Sin watch (bucle portable):
INTERVAL="${CASTUO_STATS_INTERVAL:-1}"
NAMES="${CASTUO_DOCKER_STATS_NAMES:-n8n-castuo}"
while true; do
  clear
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  # shellcheck disable=SC2086
  docker stats --no-stream $NAMES
  sleep "$INTERVAL"
done
