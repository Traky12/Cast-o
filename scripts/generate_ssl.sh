#!/bin/bash
# Generar certificados SSL para PostgreSQL y OpenEPCIS (JEREMIE/CTAEX)
set -euo pipefail
mkdir -p ssl
cd ssl

# 1. CA Root (10 años)
openssl req -new -x509 -days 3650 -nodes \
  -out ca.crt -keyout ca.key \
  -subj "/C=ES/ST=Extremadura/L=Badajoz/O=CASTUO-SYSTEM/CN=CASTUO Root CA" \
  -addext "subjectAltName = DNS:castuo-system.arsys,DNS:localhost,IP:127.0.0.1"

# 2. Certificado servidor (PostgreSQL)
openssl req -new -nodes -out server.csr -keyout server.key \
  -subj "/C=ES/ST=Extremadura/L=Badajoz/O=CASTUO-SYSTEM/CN=postgres.castuo-system.arsys" \
  -addext "subjectAltName = DNS:postgres,DNS:localhost,IP:127.0.0.1"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 365 \
  -extfile <(printf "subjectAltName=DNS:postgres,DNS:localhost,IP:127.0.0.1")

# 3. Keystore OpenEPCIS (Java) — si keytool existe
if command -v keytool &>/dev/null; then
  keytool -genkeypair -alias openepcis -keyalg RSA -keysize 2048 \
    -dname "CN=openepcis.castuo-system.arsys, OU=JEREMIE, O=CASTUO-SYSTEM, L=Badajoz, ST=Extremadura, C=ES" \
    -validity 365 -keystore keystore.p12 -storetype PKCS12 -storepass ctaex17 -keypass ctaex17
fi

chmod 600 ca.key server.key 2>/dev/null || true
chmod 600 keystore.p12 2>/dev/null || true
echo "SSL generado en ssl/"
