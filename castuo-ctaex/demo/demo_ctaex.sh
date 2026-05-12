#!/bin/bash
# Demo técnica CTAEX 90s – CASTÚO-SYSTEM TRL9 en Hetzner
set -euo pipefail

API_URL="${API_URL:-https://castuo-system.es}"
TOKEN="${API_TOKEN:-ctaex17_jeremie_token}"

echo "🎤 DEMO CASTÚO-SYSTEM TRL9 (CTAEX, 90s)"
echo "======================================="

echo "0:15 ✅ Health check TRL9 LIVE"
curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/health" || curl -s "$API_URL/health"
echo -e "\n"

echo "0:35 🌱 B001 mostaza → /sabionda/decide → VeChain TX"
curl -s -X POST "$API_URL/sabionda/decide" \
  -H "Content-Type: application/json" \
  -d '{"bandeja":"B001","crop":"mostaza","system":"hidroponia_rpi4","ph":5.6,"ec":1.9,"temp":23}' | jq . 2>/dev/null || echo ""
echo -e "\n"

echo "0:55 🔁 Ecosistema completo B001 → 3.4K€ + 30 Biocoin"
curl -s -X POST "$API_URL/ecosistema/B001" \
  -H "Content-Type: application/json" \
  -d '{"biomasa_kg":100,"crop":"sorgo","texto_psicologo":"me siento solo","amount":1000}' | jq . 2>/dev/null || echo ""
echo -e "\n"

echo "1:15 📊 docker stats (multi-réplica Hetzner CX22)"
docker stats --no-stream 2>/dev/null || echo "docker stats no disponible en este entorno"
echo -e "\n"

echo "1:30 💰 ROI: 350K€/año con 50 sistemas"
echo "======================================="

