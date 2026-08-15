#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p logs
log_file="logs/preflight-$(date +%Y%m%d).log"

echo "[INFO] Iniciando preflight" | tee -a "$log_file"

# 0) Validacion de soberania OpenClaw (configuracion y endpoint opcional)
if [[ -x "scripts/validate_openclaw_sovereignty.sh" ]]; then
  if bash scripts/validate_openclaw_sovereignty.sh | tee -a "$log_file"; then
    echo "[OK] Validacion OpenClaw soberano completada" | tee -a "$log_file"
  else
    echo "[ERROR] Fallo validacion OpenClaw soberano" | tee -a "$log_file"
    exit 1
  fi
else
  echo "[WARN] scripts/validate_openclaw_sovereignty.sh no existe o no es ejecutable" | tee -a "$log_file"
fi

# 1) Conectividad AI soberana (si hay API key)
if [[ -n "${MISTRAL_API_KEY:-}" ]]; then
  if curl -fsS --max-time 8 "https://api.mistral.ai/v1/models" \
    -H "Authorization: Bearer ${MISTRAL_API_KEY}" > /dev/null; then
    echo "[OK] Mistral API accesible" | tee -a "$log_file"
  else
    echo "[ERROR] Mistral API no accesible" | tee -a "$log_file"
    exit 1
  fi
else
  echo "[WARN] MISTRAL_API_KEY no definida, se omite chequeo de Mistral" | tee -a "$log_file"
fi

# 2) Validar entorno cloud (si existe validador)
# En CI se valida la estructura y el modo seguro, pero no se simula un
# despliegue cloud con secretos inexistentes. La validación operativa completa
# permanece bloqueante cuando CASTUO_CI_MODE no está activo.
if [[ -f "tests/cloud/cloud_validator.py" ]]; then
  if [[ "${CASTUO_CI_MODE:-}" == "1" ]]; then
    echo "[INFO] CI mode: cloud validator omitido; requiere secretos y servicios externos" | tee -a "$log_file"
  elif python tests/cloud/cloud_validator.py --profiles core,iot,ai,observability; then
    echo "[OK] Validacion cloud completada" | tee -a "$log_file"
  else
    echo "[ERROR] Entorno cloud no valido" | tee -a "$log_file"
    exit 1
  fi
else
  echo "[WARN] tests/cloud/cloud_validator.py no existe, se omite" | tee -a "$log_file"
fi

# 3) Estado Git
if [[ -n "$(git status --porcelain)" ]]; then
  echo "[WARN] Working tree no limpio" | tee -a "$log_file"
else
  echo "[OK] Working tree limpio" | tee -a "$log_file"
fi

# 4) Autenticacion Sabionda (opcional, recomendada)
if [[ -n "${CASTUO_SABIONDA_API_KEY:-}" && -n "${SABIONDA_AUTH_HEALTH_URL:-}" ]]; then
  if curl -fsS --max-time 8 \
    -H "Authorization: Bearer ${CASTUO_SABIONDA_API_KEY}" \
    "${SABIONDA_AUTH_HEALTH_URL}" > /dev/null; then
    echo "[OK] Autenticacion Sabionda valida" | tee -a "$log_file"
  else
    echo "[ERROR] Autenticacion Sabionda fallida" | tee -a "$log_file"
    exit 1
  fi
else
  echo "[WARN] Variables Sabionda incompletas, se omite auth health" | tee -a "$log_file"
fi

# 5) Risk gate (bloquea configuraciones operativas inseguras)
if [[ -x "scripts/risk-gate.sh" ]]; then
  if bash scripts/risk-gate.sh | tee -a "$log_file"; then
    echo "[OK] Risk gate completado" | tee -a "$log_file"
  elif [[ "${CASTUO_CI_MODE:-}" == "1" ]]; then
    echo "[WARN] Risk gate operativo no ejecutado en CI por ausencia de secretos; no se declara GO" | tee -a "$log_file"
  else
    echo "[ERROR] Risk gate NO-GO" | tee -a "$log_file"
    exit 1
  fi
else
  echo "[WARN] scripts/risk-gate.sh no existe o no es ejecutable" | tee -a "$log_file"
fi

echo "[OK] Preflight finalizado" | tee -a "$log_file"
