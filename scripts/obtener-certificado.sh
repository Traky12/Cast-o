#!/bin/bash
# CASTUO-SYSTEM — Generar certificado Let's Encrypt con Certbot (sin certs, nginx ya arranca en HTTP)
# Uso: desde la raíz del proyecto:  bash scripts/obtener-certificado.sh
# Requisito: dominio (ej. castuo-system.com) apuntando a la IP del servidor. Let's Encrypt no emite para solo IP.

set -e

DOMAIN="${1:-castuo-system.com}"
EMAIL="${CERTBOT_EMAIL:-gregorio@castuo360.com}"
REPO_DIR="${REPO_DIR:-.}"

echo "=== Certbot: $DOMAIN (email $EMAIL) ==="
cd "$REPO_DIR"

mkdir -p certbot/conf certbot/www

echo "1. Levantando frontend (nginx) para que Certbot pueda validar por HTTP..."
docker-compose up -d frontend
sleep 2

echo "2. Obteniendo certificado (webroot)..."
docker-compose run --rm --entrypoint certbot certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --force-renewal \
  -d "$DOMAIN"

echo "3. Certificados en certbot/conf/live/$DOMAIN/"
ls -la certbot/conf/live/"$DOMAIN"/ 2>/dev/null || true

echo ""
echo "=== Siguiente paso: activar HTTPS ==="
echo "  Opción A - Reemplazar default.conf con la config HTTPS:"
echo "    cp nginx/conf.d/default-https.conf.example nginx/conf.d/default.conf"
echo "  Opción B - O copiar solo el contenido de default-https.conf.example sobre default.conf"
echo ""
echo "  Luego: docker-compose restart frontend"
echo "  Probar: curl -I https://$DOMAIN"
echo ""
