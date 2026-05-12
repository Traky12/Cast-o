# ─────────────────────────────────────────────────────────────────────────────
# Vault Policy: quantum — CASTÚO-SYSTEM™ (QSEC-001 / QSEC-002)
# ─────────────────────────────────────────────────────────────────────────────
# Concede acceso de lectura a los secretos de cifrado cuántico/híbrido
# y al motor transit para operaciones criptográficas.
#
# Aplicar con:
#   vault policy write castuo-quantum infrastructure/vault/policies/quantum.hcl
#
# Asignar al AppRole del servicio API / LangGraph:
#   vault write auth/approle/role/castuo-api \
#       policies="castuo-quantum,castuo-iot" \
#       secret_id_ttl=24h token_ttl=1h
#
# Ref: PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §2 (Vault KV v2)
# ─────────────────────────────────────────────────────────────────────────────

# ── KV v2: secretos de cifrado ───────────────────────────────────────────────

# Secreto JWT para middleware quantum_auth
path "secret/data/castuo/quantum/jwt_secret" {
  capabilities = ["read"]
}

# Clave privada X25519 / P-384 del backend (generada fuera del código)
path "secret/data/castuo/quantum/backend_private_key" {
  capabilities = ["read"]
}

# Clave pública de dispositivos IoT (lectura para cifrado)
path "secret/data/castuo/iot/+/public_key" {
  capabilities = ["read"]
}

# ── KV v2: metadatos (listar versiones, sin leer contenido) ──────────────────
path "secret/metadata/castuo/quantum/*" {
  capabilities = ["list", "read"]
}

path "secret/metadata/castuo/iot/*" {
  capabilities = ["list"]
}

# ── KV v2: quantum secrets (acceso general) ──────────────────────────────────
path "secret/data/quantum/*" {
  capabilities = ["create", "read", "update", "list"]
}

# ── Transit engine: cifrado/descifrado (sin acceso a clave en claro) ─────────
# Permite usar Kyber-1024 / X25519 vía Vault Transit cuando estén disponibles.

path "transit/encrypt/castuo-quantum" {
  capabilities = ["update"]
}

path "transit/decrypt/castuo-quantum" {
  capabilities = ["update"]
}

path "transit/datakey/plaintext/castuo-quantum" {
  capabilities = ["update"]
}

path "transit/keys/castuo-quantum" {
  capabilities = ["read"]
}

path "transit/encrypt/quantum" {
  capabilities = ["update"]
}

path "transit/decrypt/quantum" {
  capabilities = ["update"]
}

# ── AppRole auth ─────────────────────────────────────────────────────────────
path "auth/approle/login" {
  capabilities = ["update"]
}

# ── Renovación de token propio ───────────────────────────────────────────────
path "auth/token/renew-self" {
  capabilities = ["update"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}
