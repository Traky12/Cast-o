#!/usr/bin/env bash
# Certbot webroot + fragmento TLS endurecido (Nginx en Docker). Requiere DNS apuntando al VPS.
set -euo pipefail

CASTUO_REPO_ROOT="${CASTUO_REPO_ROOT:-/opt/castuo-system}"
CASTUO_DOMAIN="${CASTUO_DOMAIN:?export CASTUO_DOMAIN=}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:?export CERTBOT_EMAIL=}"

cd "$CASTUO_REPO_ROOT"
if [[ ! -f .env.production ]]; then
  echo "Falta .env.production en $CASTUO_REPO_ROOT" >&2
  exit 1
fi

if [[ -z "${CASTUO_N8N_DOMAIN:-}" ]]; then
  CASTUO_N8N_DOMAIN="$(grep -E '^N8N_HOST=' .env.production | head -1 | sed 's/^N8N_HOST=//; s/\r$//; s/^\"//; s/\"$//; s/^'"'"'//; s/'"'"'$//')"
fi
CASTUO_N8N_DOMAIN="${CASTUO_N8N_DOMAIN:?export CASTUO_N8N_DOMAIN o N8N_HOST en .env.production}"

COMPOSE=(docker compose -f "$CASTUO_REPO_ROOT/docker-compose.prod.yml" --env-file "$CASTUO_REPO_ROOT/.env.production")

_public_ip() {
  curl -4 -fsS --max-time 5 https://ifconfig.me/ip 2>/dev/null || curl -4 -fsS --max-time 5 https://api.ipify.org 2>/dev/null || true
}

_check_dns() {
  local name="$1" want="${2:-}"
  local got
  if ! command -v dig >/dev/null 2>&1; then
    apt-get update -y && apt-get install -y --no-install-recommends dnsutils
  fi
  got="$(dig +short "$name" A | tail -1)"
  if [[ -z "$got" ]]; then
    echo "ERROR: sin registro A para $name" >&2
    exit 1
  fi
  if [[ -n "$want" && "$got" != "$want" ]]; then
    echo "ERROR: $name → $got (esperado $want). DNS/TTL/propagación." >&2
    exit 1
  fi
  echo "OK DNS $name → $got"
}

WANT_IP="${EXPECTED_IP:-}"
if [[ -z "$WANT_IP" ]]; then
  WANT_IP="$(_public_ip)"
fi
if [[ -z "$WANT_IP" ]]; then
  echo "Define EXPECTED_IP=... si no hay salida a Internet desde el servidor." >&2
  exit 1
fi

echo "==> DNS → $WANT_IP"
_check_dns "$CASTUO_DOMAIN" "$WANT_IP"
_check_dns "$CASTUO_N8N_DOMAIN" "$WANT_IP"

if [[ ! -f castuo.conf.pre-ssl.bak ]]; then
  cp -a castuo.conf castuo.conf.pre-ssl.bak
fi

echo "==> Docker up"
"${COMPOSE[@]}" up -d

echo "==> Certbot certonly"
"${COMPOSE[@]}" --profile certbot run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$CASTUO_DOMAIN" -d "$CASTUO_N8N_DOMAIN" \
  --email "$CERTBOT_EMAIL" \
  --agree-tos --non-interactive

CERT_LINEAGE="/etc/letsencrypt/live/$CASTUO_DOMAIN"
HTTPS_CONF="$CASTUO_REPO_ROOT/castuo-https.auto.conf"

cat >"$HTTPS_CONF" <<NGX
# Generado por deploy/setup-ssl.sh — regenerar con el mismo script si cambias dominios.
limit_req_zone \$binary_remote_addr zone=castuo_limit:10m rate=10r/s;

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $CASTUO_DOMAIN;

    ssl_certificate     $CERT_LINEAGE/fullchain.pem;
    ssl_certificate_key $CERT_LINEAGE/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; base-uri 'self';" always;

    location / {
        limit_req zone=castuo_limit burst=20 nodelay;
        proxy_pass http://castuo_api;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 120s;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $CASTUO_N8N_DOMAIN;

    ssl_certificate     $CERT_LINEAGE/fullchain.pem;
    ssl_certificate_key $CERT_LINEAGE/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;

    location / {
        limit_req zone=castuo_limit burst=30 nodelay;
        proxy_pass http://castuo_n8n;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }
}
NGX

echo "==> Recarga Nginx (monta castuo-https.auto.conf)"
"${COMPOSE[@]}" up -d --force-recreate nginx

CRON_TAG="castuo-certbot-renew"
CRON_LINE="12 3,15 * * * cd $CASTUO_REPO_ROOT && docker compose -f docker-compose.prod.yml --env-file .env.production --profile certbot run --rm certbot renew --webroot -w /var/www/certbot --quiet && docker compose -f docker-compose.prod.yml exec -T nginx nginx -s reload"
if crontab -l 2>/dev/null | grep -Fq "$CRON_TAG"; then
  echo "(cron $CRON_TAG ya presente)"
else
  ( crontab -l 2>/dev/null; echo "# $CRON_TAG"; echo "$CRON_LINE" ) | crontab -
  echo "OK cron instalado ($CRON_TAG)"
fi

echo "==> Prueba: curl -fsS https://$CASTUO_DOMAIN/health"
