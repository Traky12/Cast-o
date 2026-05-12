#!/bin/bash
# CASTUO-SYSTEM v5.0 — Deploy completo (HTTP → HTTPS)
# Uso: desde la raíz del proyecto
#   bash scripts/deploy-v5-https.sh
#   DOMAIN=midominio.com bash scripts/deploy-v5-https.sh  # opcional

set -e

DOMAIN="${DOMAIN:-castuo-system.com}"
REPO_DIR="${REPO_DIR:-.}"

echo "=== Deploy v5.0 → HTTPS ($DOMAIN) ==="
cd "$REPO_DIR"

echo "1. git pull + build + up..."
git pull
docker-compose up -d --build

echo "2. Certificado Let's Encrypt..."
bash scripts/obtener-certificado.sh "$DOMAIN"

echo "3. Activar HTTPS en nginx..."
cp nginx/conf.d/default-https.conf.example nginx/conf.d/default.conf
docker-compose restart frontend

echo "4. Verificación..."
sleep 2
curl -I "https://89.167.5.233" 2>/dev/null || curl -I "https://$DOMAIN" 2>/dev/null || echo "Comprueba manualmente: https://$DOMAIN"

echo ""
echo "=== Deploy v5.0 HTTPS listo ==="
