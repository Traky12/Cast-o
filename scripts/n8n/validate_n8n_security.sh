#!/usr/bin/env bash
# Valida CLI n8n (si está en PATH) y la plantilla del repo.
# Solo Docker: export N8N_ALLOW_MISSING_CLI=1 para no fallar si n8n no está en el host.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "🔍 Validando configuración de n8n..."
if command -v n8n &> /dev/null; then
  echo "✅ n8n está instalado: $(n8n --version)"
else
  echo "❌ n8n no está en PATH."
  echo "   Instalación típica: npm install n8n -g  — o comprueba en Docker: docker exec <contenedor> n8n --version"
  if [[ "${N8N_ALLOW_MISSING_CLI:-}" == "1" ]]; then
    echo "   (N8N_ALLOW_MISSING_CLI=1: se omite la exigencia de CLI en este host.)"
  else
    exit 1
  fi
fi

POLICY="docs/deploy/n8n-security-policy.example.json"
if [[ -f "$POLICY" ]]; then
  echo "✅ Plantilla de seguridad encontrada."
  echo "📝 Recuerda: mapea este JSON a tu configuración real y reemplaza *.invalid."
  if command -v jq &> /dev/null; then
    jq '.workflow.execution.timeout' "$POLICY" || true
  fi
else
  echo "❌ Error: falta la plantilla en docs/deploy/"
  exit 1
fi

echo "OK — revisa Settings > Workflow Security en tu instancia."
