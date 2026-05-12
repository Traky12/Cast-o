#!/usr/bin/env bash
# Genera CA (una vez) y certificado de servidor; opcionalmente cliente.
# Uso desde la raíz del repositorio:
#   chmod +x deploy/mqtt-tls/scripts/gen-certs.sh
#   MQTT_CN=mqtt.tu-dominio.com CLIENT_CN=esp32-water-01 ./deploy/mqtt-tls/scripts/gen-certs.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CERT_DIR="${CERT_DIR:-$ROOT/deploy/mqtt-tls/mosquitto/certs}"
MQTT_CN="${MQTT_CN:-mqtt.castuo-system.es}"
DAYS_CA="${DAYS_CA:-3650}"
DAYS_CERT="${DAYS_CERT:-365}"

mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

if [ ! -f ca.key ]; then
  echo "Generando CA..."
  openssl genrsa -out ca.key 2048
  openssl req -new -x509 -days "$DAYS_CA" -key ca.key -out ca.crt \
    -subj "/O=CASTUO/CN=CASTÚO MQTT CA"
fi

echo "Generando certificado de servidor ($MQTT_CN)..."
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/O=CASTUO/CN=$MQTT_CN"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days "$DAYS_CERT"
rm -f server.csr

if [ -n "${CLIENT_CN:-}" ]; then
  echo "Generando certificado de cliente ($CLIENT_CN)..."
  openssl genrsa -out client.key 2048
  openssl req -new -key client.key -out client.csr -subj "/O=CASTUO/CN=$CLIENT_CN"
  openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out client.crt -days "$DAYS_CERT"
  rm -f client.csr
  chmod 600 client.key
fi

chmod 600 ca.key server.key
echo "Certificados en $CERT_DIR"
