#!/bin/sh
# entrypoint.sh — Espera dependencias y arranca el agente según AGENT_TYPE
set -e

RABBITMQ_HOST="${RABBITMQ_HOST:-localhost}"
RABBITMQ_PORT="${RABBITMQ_PORT:-5672}"

# Esperar a que RabbitMQ esté disponible
until nc -z -w 2 "$RABBITMQ_HOST" "$RABBITMQ_PORT" 2>/dev/null; do
  echo "Esperando a RabbitMQ en $RABBITMQ_HOST:$RABBITMQ_PORT..."
  sleep 2
done

# Esperar a Vault (opcional)
if [ -n "$VAULT_ADDR" ]; then
  until curl -sf "${VAULT_ADDR}/v1/sys/health" | grep -q '"initialized":true'; do
    echo "Esperando a Vault en $VAULT_ADDR..."
    sleep 2
  done
fi

# Ejecutar el agente según tipo
case "${AGENT_TYPE:-master}" in
  master)
    exec python -m backend.agents.master_agent
    ;;
  selfhealing)
    exec python -m backend.agents.selfhealing_agent
    ;;
  ai)
    exec python -m backend.agents.ai_agent
    ;;
  *)
    echo "Tipo de agente no reconocido: $AGENT_TYPE"
    exit 1
    ;;
esac
