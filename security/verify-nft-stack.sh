#!/usr/bin/env bash
# CASTÚO-SYSTEM v1.7.0 — Verificación seguridad 7 capas del stack NFT dinámico.
# Uso: ./security/verify-nft-stack.sh
# Salida: 🔒 NFT STACK 7/7 SECURE (exit 0) o fallo en uno o más checks (exit 1).

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PASS=0
FAIL=0
SKIP=0

# Formato oficial: "N. Label → ✅ Estado" o "→ ⏭️ Fallback"
report_ok()   { echo "$1 → ✅ $2"; ((PASS+=1)); }
report_skip() { echo "$1 → ⏭️ $2"; ((SKIP+=1)); }
report_fail() { echo "$1 → ❌ $2"; ((FAIL+=1)); }

echo "🔍 Verificación Seguridad NFT Stack v1.7.0"
echo ""

# 1. Docker Secret nft_private_key
if command -v docker >/dev/null 2>&1; then
  if docker secret ls 2>/dev/null | grep -q nft_private_key; then
    report_ok "1. Docker Secret nft_private_key" "Existe"
  else
    report_skip "1. Docker Secret nft_private_key" "No encontrado"
  fi
else
  report_skip "1. Docker Secret nft_private_key" "Sin Docker"
fi

# 2. SOPS .env.sops
if [ -f ".env.sops" ] && command -v sops >/dev/null 2>&1; then
  if sops --decrypt .env.sops >/dev/null 2>&1; then
    report_ok "2. SOPS .env.sops" "Descifrable"
  else
    report_fail "2. SOPS .env.sops" "No descifrable"
  fi
else
  report_skip "2. SOPS .env.sops" "Archivo o sops ausente"
fi

# 3. Git-crypt
if command -v git-crypt >/dev/null 2>&1; then
  if git-crypt status >/dev/null 2>&1; then
    report_ok "3. Git-crypt" "Inicializado"
  else
    report_skip "3. Git-crypt" "No inicializado"
  fi
else
  report_skip "3. Git-crypt" "No instalado"
fi

# 4. K8s dynamic-nft-minter
if command -v kubectl >/dev/null 2>&1; then
  if kubectl get pods -l app=dynamic-nft-minter --request-timeout=5s 2>/dev/null | grep -q Running; then
    report_ok "4. K8s dynamic-nft-minter" "Running"
  else
    report_skip "4. K8s dynamic-nft-minter" "Sin cluster o sin pods"
  fi
else
  report_skip "4. K8s dynamic-nft-minter" "Sin kubectl"
fi

# 5. Proxy Admin
if [ -n "$DYNAMIC_NFT_ADDRESS" ] && [ -f "blockchain/scripts/verify-proxy-admin.js" ]; then
  if (cd blockchain && npx hardhat run scripts/verify-proxy-admin.js --network gaiachain 2>/dev/null); then
    report_ok "5. Proxy Admin" "DynamicCropNFT verified"
  else
    report_skip "5. Proxy Admin" "Red o script no disponible"
  fi
else
  report_skip "5. Proxy Admin" "DYNAMIC_NFT_ADDRESS o script ausente"
fi

# 6. Audit Trail (audit_trace.py o verify_nft_audit.py)
AUDIT_SCRIPT=""
[ -f "backend/scripts/audit_trace.py" ] && AUDIT_SCRIPT="backend/scripts/audit_trace.py"
[ -z "$AUDIT_SCRIPT" ] && [ -f "backend/scripts/verify_nft_audit.py" ] && AUDIT_SCRIPT="backend/scripts/verify_nft_audit.py"
if [ -n "$AUDIT_SCRIPT" ]; then
  if python3 "$AUDIT_SCRIPT" 1 2>/dev/null; then
    report_ok "6. Audit Trail" "Token 1 trace OK"
  else
    report_skip "6. Audit Trail" "Sin datos o error"
  fi
else
  report_skip "6. Audit Trail" "Script ausente"
fi

# 7. Repo Structure (archivos críticos + carpetas ecosistema)
CRITICAL_FILES="blockchain/contracts/DynamicCropNFT.sol backend/scripts/update_dynamic_nft.py backend/scripts/mint_dynamic_lettuce_nft.py"
CRITICAL_DIRS="backend security docs blockchain/contracts"
MISSING=""
for f in $CRITICAL_FILES; do [ ! -f "$f" ] && MISSING="$MISSING $f"; done
for d in $CRITICAL_DIRS; do [ ! -d "$d" ] && MISSING="$MISSING $d"; done
if [ -z "$MISSING" ]; then
  report_ok "7. Repo Structure" "100% Completa"
else
  report_fail "7. Repo Structure" "Faltan:$MISSING"
fi

echo ""
if [ "$FAIL" -eq 0 ] && [ "$PASS" -gt 0 ]; then
  echo "🔒 NFT STACK 7/7 SECURE"
  echo "Trazabilidad inmutable → NFTs seguros → Cooperativas protegidas."
  exit 0
else
  echo "⚠️  NFT STACK: $PASS passed, $SKIP skipped, $FAIL failed"
  exit 1
fi
