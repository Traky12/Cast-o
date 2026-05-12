# Guía de implementación completa — Producción

**CASTÚO-SYSTEM™** — Pasos para desplegar Fireblocks, QKD, modelo Transformer, HSM (Thales Luna 7), YubiKey 5Ci y verificación con GaiaChain.

---

## 1. Requisitos de hardware (referencia)

| Componente | Modelo recomendado | Notas |
|------------|--------------------|--------|
| HSM | Thales Luna 7 | 2 unidades para HA |
| YubiKey | YubiKey 5Ci | 1 principal + 2 respaldo |
| QKD | ID Quantique Cerberis XG | 1 por DC crítico |
| Servidor | Con TPM 2.0 | Dell PowerEdge R750xs u equivalente |
| Almacenamiento | SanDisk Extreme Pro 128GB | Backups encriptados |
| Fireblocks | Cuenta MPC-CMP | Custodia de fragmentos |

---

## 2. Orden de implementación

### 2.1 Dependencias base

```bash
sudo apt-get update
sudo apt-get install -y python3-pip libpam-yubico yubico-pam pkcs11-tools
pip3 install cryptography  # y opcional: fireblocks-sdk, tensorflow, qiskit
```

### 2.2 HSM Thales Luna 7

```bash
# Inicialización (SO-PIN y User PIN por prompt, no en script)
sudo scripts/security/init-hsm.sh
pkcs11-tool --login --pin $HSM_USER_PIN --list-objects
```

### 2.3 YubiKey 5Ci

```bash
ykman config usb --enable OTP+FIDO2+PIV
ykman piv generate-key --algorithm ECCP384 9a auth
sudo scripts/security/setup-yubikey.sh
```

### 2.4 Fireblocks

```bash
export FIREBLOCKS_API_KEY="..."
export FIREBLOCKS_VAULT_ACCOUNT_ID="0"
./scripts/security/store_fragment_in_fireblocks.sh
```

### 2.5 QKD (si está disponible)

```bash
export QKD_SERVER_ADDRESS="https://qkd.castuo-system.com"
export QKD_API_KEY="..."
python3 scripts/security/quantum_destruction_qkd.py activate caceres_quantum_dc
```

### 2.6 Modelo de comportamiento (Transformer)

```bash
# Entrenar con historial (archivo JSON con eventos y opcional "label")
python3 scripts/security/behavioral_auth_transformer.py train --user authorized_admin --events events.json
# Monitoreo por stdin (eventos JSON, uno por línea)
python3 scripts/security/behavioral_auth_transformer.py monitor --user authorized_admin
```

### 2.7 Backups automáticos

```bash
sudo crontab -e
# Añadir: 0 3 * * * /opt/castuo/scripts/backup/automated-backup.sh
```

---

## 3. Verificación de integración

```bash
# Autenticación YubiKey + biometría
scripts/security/biometric_auth.py

# Fireblocks (almacenamiento de prueba)
python3 scripts/security/fireblocks_integration.py store 2  # con fragmento por stdin

# Destrucción cuántica (simulada)
python3 scripts/security/quantum_destruction_simulator.py simulate caceres_quantum_dc

# Destrucción cuántica con QKD (si QKD_SERVER_ADDRESS está definido)
python3 scripts/security/quantum_destruction_qkd.py activate caceres_quantum_dc

# Behavioral Transformer
python3 scripts/security/behavioral_auth_transformer.py monitor --user test
```

---

## 4. Documentación por componente

| Componente | Documento |
|------------|-----------|
| Fireblocks | [Fireblocks-Custody.md](Fireblocks-Custody.md) |
| Swiss Vault | [Swiss-Vault-Integration.md](Swiss-Vault-Integration.md) |
| QKD | [Quantum-Destruction-QKD.md](Quantum-Destruction-QKD.md) |
| Behavioral Transformer | [Behavioral-Auth-Transformer.md](Behavioral-Auth-Transformer.md) |
| Ledger Vault | [Ledger-Vault-Integration.md](Ledger-Vault-Integration.md) |
| Destrucción cuántica (simulador) | [Quantum-Destruction-Protocols.md](Quantum-Destruction-Protocols.md) |
| Destrucción fotónica | [Quantum-Photonic-Destruction.md](Quantum-Photonic-Destruction.md) |
| Federated learning | [Federated-Learning-Behavioral-Auth.md](Federated-Learning-Behavioral-Auth.md) |
| Producción (Swiss/fotónica/FL) | [Production-Implementation-Guide.md](Production-Implementation-Guide.md) |
| Integración general | [Full-Integration-Guide.md](Full-Integration-Guide.md) |

---

## 5. Variables de entorno críticas

| Variable | Uso |
|----------|-----|
| `FIREBLOCKS_API_KEY`, `FIREBLOCKS_VAULT_ACCOUNT_ID` | Fireblocks |
| `QKD_SERVER_ADDRESS`, `QKD_API_KEY` | QKD |
| `LEDGER_VAULT_API_KEY` | Ledger Vault |
| `GAIA_CHAIN_ADMIN_KEY` | GaiaChain (alertas, fragmentos) |
| `HSM_USER_PIN` | HSM (opcional; si no, clave PEM) |
| `YUBICO_CLIENT_ID`, `YUBICO_API_KEY` | YubiKey OTP |
| `GAIA_CHAIN_DIR` | Ruta a `master_key.pem` |

No incluir contraseñas ni PINs en scripts; usar prompts o secretos en entorno.

---

**Referencias**: [Sistema-Seguridad-Extrema.md](Sistema-Seguridad-Extrema.md) | [Full-Integration-Guide.md](Full-Integration-Guide.md)
