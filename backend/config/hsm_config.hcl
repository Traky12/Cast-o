# Configuración para Vault con HSM Thales Luna 9
# Uso: vault server -config=/etc/vault.d/vault.hcl (incluir este seal)
seal "pkcs11" {
  lib            = "/opt/thales/luna/client/lib/libCryptoki2_64.so"
  slot           = "1"
  pin            = "${HSM_PIN}"
  key_label      = "CASTUO_MK"
  generate_key   = false
  hmac_key_label = "CASTUO_HMAC"
}
