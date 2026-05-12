#!/bin/bash
# scripts/security/install_veracrypt_eu.sh
#
# Instalacion VeraCrypt en Debian/Ubuntu. Version parametrizable pero por defecto 1.26.7.
#
set -euo pipefail

VERACRYPT_VERSION="${VERACRYPT_VERSION:-1.26.7}"
PKG_PATH="/tmp/veracrypt_${VERACRYPT_VERSION}.deb"

echo "Instalando VeraCrypt ${VERACRYPT_VERSION} ..."
sudo apt-get update

sudo apt-get install -y libfuse2 libwxbase3.0-0v5 libwxgtk3.0-gtk3-0v5 ca-certificates curl wget

URL="https://launchpad.net/veracrypt/trunk/${VERACRYPT_VERSION}/+download/veracrypt-${VERACRYPT_VERSION}-Ubuntu-22.04-amd64.deb"
echo "Descargando: $URL"
wget -O "$PKG_PATH" "$URL"

sudo dpkg -i "$PKG_PATH" || sudo apt-get install -f -y

echo -n "Version instalada: "
veracrypt --version || true

echo "OK"

