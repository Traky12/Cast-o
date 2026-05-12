#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +"%Y%m%d-%H%M%S")"
OUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/artifacts/security-hybrid/$STAMP}"

mkdir -p "$OUT_DIR"

PASS=0
WARN=0
FAIL=0

pass() {
  PASS=$((PASS + 1))
  echo "PASS: $1"
}

warn() {
  WARN=$((WARN + 1))
  echo "WARN: $1"
}

fail() {
  FAIL=$((FAIL + 1))
  echo "FAIL: $1"
}

echo "[INFO] Evidencias en $OUT_DIR"

if command -v pfctl >/dev/null 2>&1; then
  if pfctl -sr >"$OUT_DIR/opnsense_rules.txt" 2>/dev/null; then
    pass "Reglas PF/OPNsense exportadas"
  else
    warn "No se pudieron exportar reglas PF"
  fi
else
  echo "pfctl no disponible en este host" >"$OUT_DIR/opnsense_rules.txt"
  warn "pfctl no disponible; check OPNsense omitido"
fi

if command -v kubectl >/dev/null 2>&1; then
  if kubectl get networkpolicies -n castuo-system -o yaml >"$OUT_DIR/network_policies.yaml" 2>/dev/null; then
    pass "Network policies obtenidas desde cluster"
  else
    warn "No se pudieron leer policies del cluster (sin contexto o namespace)"
  fi
else
  echo "kubectl no disponible" >"$OUT_DIR/network_policies.yaml"
  warn "kubectl no disponible; verificacion K8s omitida"
fi

if command -v docker >/dev/null 2>&1; then
  if (
    cd "$ROOT_DIR"
    docker compose -f infrastructure/security/docker-compose.security.yml ps
  ) >"$OUT_DIR/security_stack_ps.txt" 2>/dev/null; then
    pass "Stack de seguridad accesible por docker compose"
  else
    warn "Stack de seguridad no iniciado o no accesible"
  fi

  if docker logs castuo-modsecurity --tail 100 >"$OUT_DIR/modsecurity_logs.txt" 2>/dev/null; then
    pass "Logs de ModSecurity capturados"
  else
    warn "No se pudieron capturar logs de ModSecurity"
    : >"$OUT_DIR/modsecurity_logs.txt"
  fi

  if docker logs castuo-suricata --tail 100 >"$OUT_DIR/suricata_alerts.txt" 2>/dev/null; then
    pass "Logs de Suricata capturados"
  else
    warn "No se pudieron capturar logs de Suricata"
    : >"$OUT_DIR/suricata_alerts.txt"
  fi
else
  : >"$OUT_DIR/security_stack_ps.txt"
  : >"$OUT_DIR/modsecurity_logs.txt"
  : >"$OUT_DIR/suricata_alerts.txt"
  fail "docker no disponible; no es posible validar stack de seguridad"
fi

if curl -fsS http://localhost:9200/_cluster/health >"$OUT_DIR/elastic_health.json" 2>/dev/null; then
  pass "Elasticsearch responde"
else
  warn "Elasticsearch no responde"
  echo '{}' >"$OUT_DIR/elastic_health.json"
fi

if curl -fsS http://localhost:5601/api/status >"$OUT_DIR/kibana_health.json" 2>/dev/null; then
  pass "Kibana responde"
else
  warn "Kibana no responde"
  echo '{}' >"$OUT_DIR/kibana_health.json"
fi

GO_NO_GO="GO"
if [[ "$FAIL" -gt 0 ]]; then
  GO_NO_GO="NO_GO"
fi

{
  echo "PASS: $PASS"
  echo "WARN: $WARN"
  echo "FAIL: $FAIL"
  echo "GO_NO_GO: $GO_NO_GO"
  echo "EVIDENCE_DIR: $OUT_DIR"
} | tee "$OUT_DIR/00_summary.txt"

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
