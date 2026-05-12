# Guía de implementación en producción — CASTÚO-SYSTEM™

Requisitos de hardware, pasos de despliegue y verificación para Swiss Vault, destrucción fotónica cuántica y federated learning en entorno de producción.

---

## 1. Requisitos de hardware (referencia)

| Componente | Modelo recomendado | Notas |
|------------|---------------------|--------|
| HSM | Thales Luna 7 | Alta disponibilidad |
| YubiKey | YubiKey 5Ci | Principal + respaldos |
| Hardware fotónico | Quantum Xchange Phio TX (opcional) | 1 por DC cuántico |
| Swiss Vault | Caja fuerte Clase IV (Zúrich) | Custodia física fragmentos |
| Sensor biométrico 3D | Thales Gemalto BioSensor (opcional) | Para Swiss Vault |
| Servidor | Con TPM 2.0 | Ej. Dell PowerEdge R750xs |
| Servidor federado | Con GPU (opcional) | Para entrenamiento de modelos |

---

## 2. Orden de implementación

### 2.1 Dependencias

```bash
sudo apt-get update
sudo apt-get install -y python3-pip pkcs11-tools
pip3 install cryptography
# Opcional: tensorflow, qiskit, id-quantique-sdk
```

### 2.2 Swiss Vault

```bash
export SWISS_VAULT_API_KEY="..."
export SWISS_VAULT_ID="CASTUO-2026"
export SWISS_VAULT_BOX_ID="BOX-9876"
./scripts/security/store_fragment_in_swissvault.sh
```

### 2.3 Destrucción fotónica

```bash
# Simulación (sin hardware)
python3 scripts/security/quantum_photonic_destruction.py simulate madrid_quantum_dc

# Activación con script (requiere auth previa)
./scripts/security/activate_photonic_destruction.sh madrid_quantum_dc
```

### 2.4 Federated learning

```bash
export CASTUO_FEDERATED_USERS="user1,user2,user3"
export CASTUO_FEDERATED_EVENTS_FILE="/path/to/events.json"
export CASTUO_FEDERATED_LABELS_FILE="/path/to/labels.json"
./scripts/security/train_federated_model.sh
```

### 2.5 Cron para actualizaciones federadas

```bash
# Ejemplo: ejecutar cada día a las 04:00
# 0 4 * * * /opt/castuo/scripts/security/train_federated_model.sh
```

---

## 3. Verificación de integración

```bash
# Swiss Vault (almacenamiento de prueba con fragmento por stdin)
echo "000000000000000000000000000000000" | python3 scripts/security/swiss_vault_integration.py store 2
# (requiere SWISS_VAULT_API_KEY y login)

# Destrucción fotónica (simulación)
python3 scripts/security/quantum_photonic_destruction.py simulate madrid_quantum_dc

# Modelo federado (con datos sintéticos)
CASTUO_FEDERATED_USERS=u1,u2,u3 ./scripts/security/train_federated_model.sh

# Registros en GaiaChain
curl -s "https://gaiachain.castuo-system.com/api/v1/audit/federated_learning" \
  -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" | jq
```

---

## 4. Documentación por componente

| Componente | Documento |
|------------|-----------|
| Swiss Vault | [Swiss-Vault-Integration.md](Swiss-Vault-Integration.md) |
| Destrucción fotónica | [Quantum-Photonic-Destruction.md](Quantum-Photonic-Destruction.md) |
| Federated learning | [Federated-Learning-Behavioral-Auth.md](Federated-Learning-Behavioral-Auth.md) |
| Fireblocks | [Fireblocks-Custody.md](Fireblocks-Custody.md) |
| Ledger Vault | [Ledger-Vault-Integration.md](Ledger-Vault-Integration.md) |
| Implementación general | [Full-Implementation-Guide.md](Full-Implementation-Guide.md) |

---

## 5. Variables de entorno críticas

| Variable | Uso |
|----------|-----|
| `SWISS_VAULT_API_KEY`, `SWISS_VAULT_ID`, `SWISS_VAULT_BOX_ID` | Swiss Vault |
| `GAIA_CHAIN_ADMIN_KEY` | GaiaChain (fragmentos, alertas, federated learning) |
| `HSM_USER_PIN` | HSM (opcional; si no, clave PEM) |
| `CASTUO_FEDERATED_USERS`, `CASTUO_FEDERATED_EVENTS_FILE`, `CASTUO_FEDERATED_LABELS_FILE` | Federated learning |
| `CASTUO_PHOTONIC_TRIGGER_DMS` | Activar DMS tras destrucción fotónica |

---

**Referencias**: [Full-Implementation-Guide.md](Full-Implementation-Guide.md) | [Sistema-Seguridad-Extrema.md](Sistema-Seguridad-Extrema.md)
