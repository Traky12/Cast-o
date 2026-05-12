#!/usr/bin/env bash
# Plantilla → copiar a init-passwd.sh y ejecutar desde la raíz del repo.
# Exporta contraseñas fuertes antes de ejecutar (ver variables abajo).
#
#   cp deploy/mqtt-tls/scripts/init-passwd.example.sh deploy/mqtt-tls/scripts/init-passwd.sh
#   export CASTUO_MQTT_ADMIN_PASS='...'
#   export CASTUO_MQTT_ORP_PASS='...'
#   ... (resto)
#   ./deploy/mqtt-tls/scripts/init-passwd.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CFG_DIR="$ROOT/deploy/mqtt-tls/mosquitto/config"
PASSWD_FILE="$CFG_DIR/passwd"
PW_IN="/mosquitto/config/passwd"
IMAGE="${MOSQUITTO_IMAGE:-eclipse-mosquitto:2.0.15}"

: "${CASTUO_MQTT_ADMIN_PASS:?export CASTUO_MQTT_ADMIN_PASS}"
: "${CASTUO_MQTT_ORP_PASS:?export CASTUO_MQTT_ORP_PASS}"
: "${CASTUO_MQTT_TDS_PASS:?export CASTUO_MQTT_TDS_PASS}"
: "${CASTUO_MQTT_PH_PASS:?export CASTUO_MQTT_PH_PASS}"
: "${CASTUO_MQTT_OZONE_PASS:?export CASTUO_MQTT_OZONE_PASS}"
: "${CASTUO_MQTT_OSMOSIS_PASS:?export CASTUO_MQTT_OSMOSIS_PASS}"
: "${CASTUO_MQTT_N8N_PASS:?export CASTUO_MQTT_N8N_PASS}"

mkdir -p "$CFG_DIR"

run_mosquitto_passwd() {
  if command -v mosquitto_passwd >/dev/null 2>&1; then
    mosquitto_passwd "$@"
  else
    local args=()
    for a in "$@"; do
      if [[ "$a" == "$PASSWD_FILE" ]]; then
        args+=("$PW_IN")
      else
        args+=("$a")
      fi
    done
    docker run --rm -v "$CFG_DIR:/mosquitto/config" "$IMAGE" mosquitto_passwd "${args[@]}"
  fi
}

if [ ! -s "$PASSWD_FILE" ]; then
  run_mosquitto_passwd -c -b "$PASSWD_FILE" admin "$CASTUO_MQTT_ADMIN_PASS"
else
  run_mosquitto_passwd -b "$PASSWD_FILE" admin "$CASTUO_MQTT_ADMIN_PASS"
fi

run_mosquitto_passwd -b "$PASSWD_FILE" sensor_orp "$CASTUO_MQTT_ORP_PASS"
run_mosquitto_passwd -b "$PASSWD_FILE" sensor_tds "$CASTUO_MQTT_TDS_PASS"
run_mosquitto_passwd -b "$PASSWD_FILE" sensor_ph "$CASTUO_MQTT_PH_PASS"
run_mosquitto_passwd -b "$PASSWD_FILE" actuator_ozone "$CASTUO_MQTT_OZONE_PASS"
run_mosquitto_passwd -b "$PASSWD_FILE" actuator_osmosis "$CASTUO_MQTT_OSMOSIS_PASS"
run_mosquitto_passwd -b "$PASSWD_FILE" n8n_system "$CASTUO_MQTT_N8N_PASS"

echo "passwd: $PASSWD_FILE"
