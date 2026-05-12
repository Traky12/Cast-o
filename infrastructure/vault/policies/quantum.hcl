path "secret/data/quantum/*" {
  capabilities = ["create", "read", "update", "list"]
}

path "transit/encrypt/quantum" {
  capabilities = ["update"]
}

path "transit/decrypt/quantum" {
  capabilities = ["update"]
}

path "auth/approle/login" {
  capabilities = ["update"]
}
