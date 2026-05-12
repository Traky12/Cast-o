# Política Vault para CASTÚO-SYSTEM™ v2.0 (claves post-cuánticas y secretos)
# Aplicar: vault policy write castuo-admin backend/policies/castuo-admin.hcl

path "castuo/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "castuo/metadata/*" {
  capabilities = ["list"]
}

# Permisos para habilitar el motor kv-v2 en castuo (manage_vault_keys.py --init)
path "sys/mounts/castuo" {
  capabilities = ["create", "read", "update", "delete"]
}
