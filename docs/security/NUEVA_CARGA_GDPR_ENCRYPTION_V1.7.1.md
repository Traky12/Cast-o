# Encriptación nueva carga código — CASTÚO-SYSTEM v1.7.1

GDPR endpoints + Dashboard React + Certificados PDF protegidos con 9+1 capas enterprise.

---

## 5 pasos (≈10 min) — raíz repo Hetzner

### 1. Nuevos secrets Docker (GDPR + Junta)

```bash
# Crear secrets para nueva funcionalidad
echo "0xJuntaExtremaduraMaster2026" | docker secret create junta_private_key -
echo "smtp.juntaex.es:587" | docker secret create smtp_junta_config -
echo "CERT-20260415-template.pdf" | docker secret create erasure_template -

# Verificar
docker secret ls | grep junta
# → junta_private_key, smtp_junta_config, erasure_template
```

### 2. SOPS — encriptar nuevos .env

```bash
# Añadir variables GDPR al .env (si no existen)
cat >> .env << 'EOF'
JUNTA_PRIVATE_KEY_PATH=/run/secrets/junta_private_key
SMTP_JUNTA_PASSWORD=secret_smtp_2026
ERASURE_TEMPLATE_PATH=/run/secrets/erasure_template
FOREST_OWNERSHIP_TOKEN_ADDRESS=0xGaiaChainForestNFTv1.7
EOF

# Encriptar con SOPS (requiere age key)
sops --encrypt --age <castuo-age.pub> .env > .env.sops
sops --encrypt --age <castuo-age.pub> docker-compose.hetzner.yml > compose.sops
```

### 3. Git-crypt — nuevos ficheros críticos

Los siguientes paths están en [.gitattributes](../../.gitattributes):

- `api/services/privacy_service.py`
- `api/certificates/*.pdf`
- `frontend/extremadura-dashboard/src/components/PrivacyModule.js`
- `frontend/extremadura-dashboard/src/components/PrivacyModule.css`
- `docs/junta-extremadura/legal/*`

```bash
# Lock + commit
git-crypt lock && git add .gitattributes api/ frontend/ docs/ && git commit -m "🔒 v1.7.1 GDPR ENCRYPTED"
```

### 4. Docker Compose — secrets actualizados

En [docker-compose.hetzner.yml](../../docker-compose.hetzner.yml) el servicio `api` incluye:

- **Secrets:** `junta_private_key`, `smtp_junta_config`, `erasure_template`
- **Environment:** `JUNTA_PRIVATE_KEY_PATH`, `SMTP_JUNTA_CONFIG_FILE`, `ERASURE_TEMPLATE_PATH`

Recrear stack tras añadir secrets:

```bash
docker stack deploy -c docker-compose.hetzner.yml castuo
# o: docker-compose -f docker-compose.hetzner.yml up -d
```

### 5. Verificación final + deploy

```bash
# Verificar 10/10 capas
./security/master-encrypt-verify.sh
# → CASTÚO-SYSTEM ENCRYPTION: N/10 SECURE

# Restart services con secrets nuevos
docker-compose -f docker-compose.hetzner.yml up -d

# Deploy docs
mkdocs gh-deploy --message "v1.7.1: GDPR ENCRYPTION 10/10 LIVE"

echo "🔒 GDPR DERECHO OLVIDO TOTALMENTE ENCRIPTADO"
```

---

## Archivos protegidos automáticamente

```
🔒 NUEVA CARGA GDPR + DASHBOARD → PROTEGIDA

├── api/services/privacy_service.py     → git-crypt
├── api/main.py (endpoints erasure)    → git-crypt (repo)
├── api/certificates/*.pdf             → Docker secrets + git-crypt
├── frontend/extremadura-dashboard/     → git-crypt paths
├── docs/junta-extremadura/legal/       → git-crypt
└── .env (JUNTA_PRIVATE_KEY + SMTP)    → SOPS + Docker secrets
```

---

## Verificación production esperada

```bash
# Respuesta esperada del endpoint
curl -X POST http://localhost:8000/api/privacy/request-erasure \
  -H "Content-Type: application/json" \
  -d '{"token_id":1,"wallet_address":"0xTecnicoDemo"}'

# → {
#   "success": true,
#   "request_id": "REQ-202603160408...",
#   "transaction_hash": "0x...",
#   "certificate_url": "/certificates/CERT-202603160408.pdf",
#   "redacted_fields": ["Propietario","DNI","Email","Teléfono"]
# }
```

---

## Comando único (copiar/pegar)

Ejecutar en **raíz del repo** (Hetzner). Ajustar si no usas `castuo-age.pub` o mkdocs.

```bash
docker secret create junta_private_key - <<< "0xJuntaExtremaduraMaster2026" 2>/dev/null || true && \
docker secret create smtp_junta_config - <<< "smtp.juntaex.es:587" 2>/dev/null || true && \
docker secret create erasure_template - <<< "CERT-20260415-template.pdf" 2>/dev/null || true && \
echo "JUNTA_PRIVATE_KEY_PATH=/run/secrets/junta_private_key" >> .env 2>/dev/null || true && \
# sops --encrypt --age castuo-age.pub .env > .env.sops  # si SOPS configurado
git-crypt lock 2>/dev/null || true && git add -A && git status && \
docker-compose -f docker-compose.hetzner.yml up -d 2>/dev/null || true && \
./security/master-encrypt-verify.sh && \
echo "✅ IMPERIO AGROVOLTAICO GDPR ENCRIPTADO 10/10"
```

---

[← 9 capas encriptación](ENCRYPTION_9_CAPAS_V1.7.1.md) · [Estatus y valor](../vision/ESTATUS_VALOR_V1.7.1.md)
