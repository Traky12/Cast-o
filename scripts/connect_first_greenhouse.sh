#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_ROOT_PASSWORD="${WP_DB_ROOT_PASSWORD:-${MYSQL_ROOT_PASSWORD:-castuo_root}}"
FARM_UID="${FARM_UID:-farm-123e4567-e89b-12d3-a456-426614174000}"
USER_UID="${USER_UID:-pilot-user-001}"
LOTE_ID="${LOTE_ID:-lote-001-2026}"
MQTT_TOPIC="${MQTT_TOPIC:-castuo/sensors/$FARM_UID}"

info() { echo "[INFO] $*"; }
ok() { echo "[OK] $*"; }
warn() { echo "[WARN] $*"; }

find_mqtt_container() {
  docker ps --format '{{.Names}}' | grep -E '(castuo-mqtt|mosquitto|mqtt|castuo-mqtt-bridge)' | head -n1 || true
}

info "Conectando primer invernadero prototipo..."

info "1/5 Upsert de usuario piloto..."
docker exec castuo-mariadb mariadb -uroot -p"$DB_ROOT_PASSWORD" -e "
USE castuo_system;
INSERT INTO users (user_uid, email, role, full_name)
VALUES ('$USER_UID', 'piloto@castuo-system.cloud', 'admin', 'Usuario Piloto')
ON DUPLICATE KEY UPDATE
  email='piloto@castuo-system.cloud',
  role='admin',
  full_name='Usuario Piloto';
"
ok "Usuario piloto listo"

info "2/5 Upsert de granja piloto..."
docker exec castuo-mariadb mariadb -uroot -p"$DB_ROOT_PASSWORD" -e "
USE castuo_system;
INSERT INTO farms (farm_uid, owner_user_uid, farm_name, location_geojson, surface_hectares, status)
VALUES (
  '$FARM_UID',
  '$USER_UID',
  'Invernadero Demo',
  JSON_OBJECT('type','Point','coordinates', JSON_ARRAY(2.18, 41.38)),
  1000.00,
  'active'
)
ON DUPLICATE KEY UPDATE
  owner_user_uid='$USER_UID',
  farm_name='Invernadero Demo',
  surface_hectares=1000.00,
  status='active';
"
ok "Granja piloto lista"

info "3/5 Validando registro en DB..."
docker exec castuo-mariadb mariadb -uroot -p"$DB_ROOT_PASSWORD" -e "
USE castuo_system;
SELECT farm_uid, owner_user_uid, farm_name, status FROM farms WHERE farm_uid='$FARM_UID';
"

MQTT_CONTAINER="$(find_mqtt_container)"
if [[ -z "$MQTT_CONTAINER" ]]; then
  warn "No se detecto contenedor MQTT. Se omite prueba de telemetria."
  exit 0
fi

info "4/5 Publicando telemetria de prueba en $MQTT_TOPIC ..."
docker exec "$MQTT_CONTAINER" sh -lc "mosquitto_pub -h localhost -t '$MQTT_TOPIC' -q 1 -m '{\"farm_uid\":\"$FARM_UID\",\"lote_id\":\"$LOTE_ID\",\"temperature\":22.5,\"humidity\":65.0,\"co2\":400,\"ph\":6.0,\"ec\":1.5,\"light_par\":350,\"vpd\":1.0}'"
ok "Telemetria publicada"

info "5/5 Verificando recepcion en topic castuo/sensors/# ..."
docker exec "$MQTT_CONTAINER" sh -lc "mosquitto_sub -h localhost -t 'castuo/sensors/#' -C 1 -W 3"
ok "Primer invernadero prototipo conectado"

echo "farm_uid=$FARM_UID"
echo "lote_id=$LOTE_ID"
