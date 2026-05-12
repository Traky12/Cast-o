# Capa clave maestra del administrador general

Todo el material sensible del sistema queda **tras una única capa** cifrada con la **clave maestra del administrador general**. Sin esta clave no se accede a secretos; con ella se puede descifrar cualquier payload protegido por esta capa.

---

## Principio

- **Una clave** (administrador general) protege el acceso a secretos y bundles cifrados.
- **Orígenes de la clave:** variable de entorno `ADMIN_MASTER_KEY`, secret Docker `admin_master_key`, o archivo local `security/.admin_master_key` (no versionar).
- **Algoritmo:** derivación HKDF-SHA256 → clave AES-256; cifrado AES-256-GCM. Salida en base64 (nonce || ciphertext || tag).

---

## Uso

### 1. Configurar la clave (solo una opción)

**Opción A — Variable de entorno (CI/servidor):**
```bash
export ADMIN_MASTER_KEY="contraseña-o-token-muy-largo-y-seguro"
```

**Opción B — Docker secret (producción):**
```bash
echo -n "contraseña-master-segura" | docker secret create admin_master_key -
# En docker-compose: secrets: admin_master_key; env: ADMIN_MASTER_KEY_FILE=/run/secrets/admin_master_key
# O montar como archivo y leer en app desde /run/secrets/admin_master_key
```

**Opción C — Archivo local (solo desarrollo, no commitear):**
```bash
echo -n "tu-clave-master" > security/.admin_master_key
chmod 600 security/.admin_master_key
```
El archivo `security/.admin_master_key` está en `.gitignore`; **nunca** debe subirse al repositorio.

---

### 2. Cifrar / descifrar desde CLI

**Cifrar stdin → base64 por stdout:**
```bash
echo -n "dato sensible" | python3 security/encrypt_with_admin_master.py encrypt
```

**Cifrar archivo:**
```bash
python3 security/encrypt_with_admin_master.py encrypt -i backend/billing.db -o backend/billing.db.enc
```

**Descifrar archivo:**
```bash
python3 security/encrypt_with_admin_master.py decrypt -i backend/billing.db.enc -o backend/billing.db
```

---

### 3. Uso desde Python

```python
from security.admin_master_layer import encrypt, decrypt

# Cifrar (bytes → base64 bytes)
ciphertext_b64 = encrypt(b"secreto o contenido binario")

# Descifrar (base64 bytes o str → bytes)
plaintext = decrypt(ciphertext_b64)
```

---

## Integración con el resto de capas

- **Capa 0 (esta):** Clave maestra administrador → desbloquea bundles y secretos cifrados con ella.
- **Capas 1–10:** Vault, Docker secrets, SOPS, Git-crypt, K8s, HKDF NFT, Audit, HSM, verificación diaria, GDPR. Los secretos que se quieran proteger “todo en uno” pueden cifrarse con esta capa (por ejemplo un backup de `.env`, claves SOPS, o un bundle de secrets) y guardarse en repo o almacenamiento; solo el administrador con la clave maestra podrá descifrarlos.

---

## Verificación

El script `security/master-encrypt-verify.sh` comprueba si la capa está configurada (variable `ADMIN_MASTER_KEY` o secret `admin_master_key` o archivo `security/.admin_master_key`). No comprueba el valor de la clave por seguridad.

---

*[ENCRYPTION_9_CAPAS_V1.7.1](ENCRYPTION_9_CAPAS_V1.7.1.md) · [BLINDAJE_ADMINISTRADOR_V170](BLINDAJE_ADMINISTRADOR_V170.md)*
