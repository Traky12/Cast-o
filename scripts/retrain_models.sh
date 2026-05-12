#!/bin/bash
# scripts/retrain_models.sh
# Script de reentrenamiento automatizado con auditoría y federación

set -euo pipefail

TIMESTAMP=$(date +"%Y%m%d%H%M%S")
LOG_DIR="/var/log/forestownershiptoken"
MODELS_DIR="/opt/forestownershiptoken/models"
BACKUP_DIR="/opt/forestownershiptoken/model_backups"
FEDERATION_ENDPOINT="https://federation.juntaextremadura.es/api/update-model"

mkdir -p "${LOG_DIR}" "${MODELS_DIR}" "${BACKUP_DIR}"

LOG_FILE="${LOG_DIR}/retrain_${TIMESTAMP}.log"
AUDIT_FILE="${LOG_DIR}/audit_retrain_${TIMESTAMP}.json"

echo "{\"timestamp\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\", \"action\": \"retrain_start\", \"models\": []}" > "${AUDIT_FILE}"

log_audit() {
  local model_name=$1
  local status=$2
  local details=$3
  jq --arg mn "$model_name" --arg st "$status" --arg dt "$details" \
     '.models += [{"model": $mn, "status": $st, "details": $dt, "timestamp": "'$(date -u +'%Y-%m-%dT%H:%M:%SZ')'"}]' \
     "${AUDIT_FILE}" > "${AUDIT_FILE}.tmp" && mv "${AUDIT_FILE}.tmp" "${AUDIT_FILE}"
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [${model_name}] ${status}: ${details}" >> "${LOG_FILE}"
}

echo "Reentrenando modelos comerciales (${TIMESTAMP})..." | tee -a "${LOG_FILE}"

cd /opt/forestownershiptoken/bots || exit 1

python3 -m offer_bot.train \
  --feedback-data /opt/forestownershiptoken/feedback/feedback_log.json \
  --output-model "${MODELS_DIR}/carbon_offer_model_${TIMESTAMP}.pkl" \
  --backup-dir "${BACKUP_DIR}" >> "${LOG_FILE}" 2>&1 || true

if grep -q "carbon_offer_model_${TIMESTAMP}" "${LOG_FILE}"; then
  log_audit "carbon_offer_model" "success" "Modelo reentrenado con nuevos datos de feedback"
  curl -sS -X POST "${FEDERATION_ENDPOINT}" \
    -H "Authorization: Bearer $(cat /opt/forestownershiptoken/federation_token 2>/dev/null || echo '')" \
    -H "Content-Type: application/json" \
    -d "{\"model_type\": \"carbon_offer\", \"model_version\": \"${TIMESTAMP}\", \"model_path\": \"${MODELS_DIR}/carbon_offer_model_${TIMESTAMP}.pkl\"}" >> "${LOG_FILE}" 2>&1 || true
else
  log_audit "carbon_offer_model" "error" "Fallo en el reentrenamiento"
fi

python3 -m negotiation_bot.train \
  --feedback-data /opt/forestownershiptoken/feedback/negotiation_feedback.json \
  --output-qtable "${MODELS_DIR}/negotiation_qtable_${TIMESTAMP}.json" \
  --backup-dir "${BACKUP_DIR}" >> "${LOG_FILE}" 2>&1 || true

if grep -q "negotiation_qtable_${TIMESTAMP}" "${LOG_FILE}"; then
  log_audit "negotiation_qtable" "success" "Tabla Q actualizada con nuevos datos de negociación"
  curl -sS -X POST "${FEDERATION_ENDPOINT}" \
    -H "Authorization: Bearer $(cat /opt/forestownershiptoken/federation_token 2>/dev/null || echo '')" \
    -H "Content-Type: application/json" \
    -d "{\"model_type\": \"negotiation_qtable\", \"model_version\": \"${TIMESTAMP}\", \"model_path\": \"${MODELS_DIR}/negotiation_qtable_${TIMESTAMP}.json\"}" >> "${LOG_FILE}" 2>&1 || true
else
  log_audit "negotiation_qtable" "error" "Fallo en la actualización de la tabla Q"
fi

python3 -m loyalty_bot.train \
  --feedback-data /opt/forestownershiptoken/feedback/loyalty_feedback.json \
  --output-model "${MODELS_DIR}/loyalty_clusters_${TIMESTAMP}.pkl" \
  --backup-dir "${BACKUP_DIR}" >> "${LOG_FILE}" 2>&1 || true

if grep -q "loyalty_clusters_${TIMESTAMP}" "${LOG_FILE}"; then
  log_audit "loyalty_clusters" "success" "Clusters de clientes actualizados con nuevos datos"
  curl -sS -X POST "${FEDERATION_ENDPOINT}" \
    -H "Authorization: Bearer $(cat /opt/forestownershiptoken/federation_token 2>/dev/null || echo '')" \
    -H "Content-Type: application/json" \
    -d "{\"model_type\": \"loyalty_clusters\", \"model_version\": \"${TIMESTAMP}\", \"model_path\": \"${MODELS_DIR}/loyalty_clusters_${TIMESTAMP}.pkl\"}" >> "${LOG_FILE}" 2>&1 || true
else
  log_audit "loyalty_clusters" "error" "Fallo en el reentrenamiento de clusters"
fi

python3 -m tools.register_retraining \
  --audit-file "${AUDIT_FILE}" \
  --chain-endpoint "https://gaiachain.castuo-system.com" \
  --private-key /opt/forestownershiptoken/gaiachain_key.pem >> "${LOG_FILE}" 2>&1 || true

log_audit "gaiachain_registration" "info" "Intento de registro del reentrenamiento en GaiaChain"

echo "Limpiando modelos antiguos..." | tee -a "${LOG_FILE}"
find "${MODELS_DIR}" -maxdepth 1 \( -name "*.pkl" -o -name "*.json" \) | sort | head -n -3 | xargs -r rm -f

echo "Reiniciando servicios de bots comerciales..." | tee -a "${LOG_FILE}"
docker-compose -f /opt/forestownershiptoken/commercial_bots/docker-compose.yml restart >> "${LOG_FILE}" 2>&1 || true

echo "Reentrenamiento completado. Ver logs en ${LOG_FILE} y auditoría en ${AUDIT_FILE}" | tee -a "${LOG_FILE}"

