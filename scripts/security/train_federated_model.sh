#!/bin/bash
# CASTÚO-SYSTEM™ — Entrena el modelo federado de autenticación por comportamiento.
# Requiere autenticación previa. Usuarios por env o argumentos (sin nombres personales en script).
# Uso: ./scripts/security/train_federated_model.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Autenticación opcional
if [ -f "$SCRIPT_DIR/biometric_auth.py" ]; then
  python3 "$SCRIPT_DIR/biometric_auth.py" || true
elif [ -f "$SCRIPT_DIR/authenticate_with_yubikey.py" ]; then
  python3 "$SCRIPT_DIR/authenticate_with_yubikey.py" || true
fi

# 2. Entrenar con datos (en producción: leer eventos/labels desde GaiaChain o archivos)
# Usuarios por defecto o CASTUO_FEDERATED_USERS (lista separada por comas)
USERS="${CASTUO_FEDERATED_USERS:-user1,user2,user3}"
EVENTS_FILE="${CASTUO_FEDERATED_EVENTS_FILE:-/opt/castuo/data/behavioral_events.json}"
LABELS_FILE="${CASTUO_FEDERATED_LABELS_FILE:-/opt/castuo/data/behavioral_labels.json}"

if [ ! -f "$EVENTS_FILE" ] || [ ! -f "$LABELS_FILE" ]; then
  echo "Archivos de datos no encontrados. Generando datos sintéticos para prueba."
  python3 -c "
import json
import numpy as np
import os
os.makedirs('/tmp/castuo_federated', exist_ok=True)
events = [{'type': 'keyboard', 'speed': 2.5 + np.random.normal(0, 0.3), 'time_since_last': 0.1, 'time_of_day': 10} for _ in range(100)]
labels = [False] * 100
labels[50] = True
with open('/tmp/castuo_federated/events.json', 'w') as f:
    json.dump(events, f)
with open('/tmp/castuo_federated/labels.json', 'w') as f:
    json.dump(labels, f)
print('Datos sintéticos en /tmp/castuo_federated/')
"
  EVENTS_FILE="/tmp/castuo_federated/events.json"
  LABELS_FILE="/tmp/castuo_federated/labels.json"
fi

# 2b. Un solo proceso Python: añadir datos por usuario y promediado federado
MODEL_PATH="${CASTUO_FEDERATED_MODEL_PATH:-/opt/castuo/models/behavioral_auth_federated_v1.h5}"
mkdir -p "$(dirname "$MODEL_PATH")"
IFS=',' read -ra UIDS <<< "$USERS"
python3 -c "
import sys
import json
sys.path.insert(0, '$SCRIPT_DIR')
from behavioral_auth_federated import FederatedBehavioralAuth

fba = FederatedBehavioralAuth()
users = [u.strip() for u in '$USERS'.split(',')]
events_file = '$EVENTS_FILE'
labels_file = '$LABELS_FILE'
try:
    with open(events_file) as f:
        events = json.load(f)
    with open(labels_file) as f:
        labels = json.load(f)
    for u in users:
        fba.add_user_data(u, events, labels)
    fba.federated_average(users)
    if fba.global_model is not None:
        fba.global_model.save_weights('$MODEL_PATH')
        print('Modelo guardado en $MODEL_PATH')
except FileNotFoundError as e:
    print('Archivo no encontrado:', e)
except Exception as e:
    print('Error:', e)
"

# 4. Registrar en GaiaChain
if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "${GAIA_CHAIN_DIR:-/etc/gaiachain}/master_key.pem" ] && [ -f "$MODEL_PATH" ]; then
  HASH=$(sha256sum "$MODEL_PATH" 2>/dev/null | awk '{print $1}')
  SIG=$(echo -n "FEDERATED_GLOBAL_UPDATE_$(date +%s)" | openssl dgst -sha512 -sign "${GAIA_CHAIN_DIR:-/etc/gaiachain}/master_key.pem" 2>/dev/null | base64 -w0) || true
  curl -sf -X POST "${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}/api/v1/federated_learning/global_update" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model_version\":\"TRANSFORMER-LSTM-FEDERATED-v1\",\"participants\":[\"${USERS}\"],\"timestamp\":\"$(date +%s)\",\"model_hash\":\"$HASH\",\"signature\":\"$SIG\"}" >/dev/null || true
fi

echo "Modelo federado entrenado. Participantes: ${USERS}. Hash registrado en GaiaChain si aplica."
