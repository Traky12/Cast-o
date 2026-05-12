# Vault staging: almacenamiento en archivo, sellado Shamir (sin HSM).
# Uso: vault server -config=/etc/vault.d/vault_staging.hcl

ui = true

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

storage "file" {
  path = "/var/lib/vault/data"
}

# Sin bloque seal => seal Shamir por defecto (operator init / unseal con 5/3 shares).
