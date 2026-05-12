# SanDisk 128GB — Almacenamiento seguro CASTÚO-SYSTEM™

Almacenamiento offline de datos críticos (GaiaChain, Cursor, IoT, legal, personas, biometría, fragmentos de emergencia) con doble capa de cifrado.

---

## 1. Preparación del SanDisk

### 1.1 LUKS2

```bash
# Identificar dispositivo (ej. /dev/sdX)
lsblk
# Crear partición LUKS2
sudo cryptsetup luksFormat --type luks2 --pbkdf argon2id --iter-time 5000 /dev/sdX
sudo cryptsetup open /dev/sdX castuo_secure
sudo mkfs.ext4 /dev/mapper/castuo_secure
sudo mount /dev/mapper/castuo_secure /mnt/sandisk
```

### 1.2 VeraCrypt (opcional, dentro de LUKS)

```bash
veracrypt --create /mnt/sandisk/castuo_veracrypt.hc --volume-type=normal --encryption=AES --hash=SHA-512 --filesystem=ext4 --size=120G
veracrypt /mnt/sandisk/castuo_veracrypt.hc /mnt/sandisk/CASTUO_SECURE
```

---

## 2. Montaje seguro

- **Script**: `scripts/security/mount-sandisk.sh /dev/sdX`
- Solicita contraseña LUKS por prompt (no almacenada).
- Variables: `CASTUO_LUKS_MAPPER`, `CASTUO_SANDISK_MOUNT`, `CASTUO_SANDISK_ROOT`.

---

## 3. Exportación de datos

| Script | Contenido |
|--------|-----------|
| `scripts/export/export_cursor_to_sandisk.sh` | Binarios y configs Cursor (verificación de firma) |
| `scripts/export/export_gaiachain_to_sandisk.sh` | Backups y snapshot GaiaChain |
| `scripts/export/export_iot_to_sandisk.sh` | Firmware IoT y certificados TPM |
| `scripts/export/export_legal_to_sandisk.sh` | Legal, CTAEX, compliance, auditorías |

Ejecutar después de montar el SanDisk. Destino por defecto: `$CASTUO_SANDISK_ROOT` o `/mnt/sandisk/CASTUO_SECURE`.

---

## 4. Estructura en SanDisk

```
CASTUO_SECURE/
├── gaiachain/     # Backups, snapshots
├── cursor/        # Binarios, configs (firmados)
├── iot/           # Firmware, certs TPM
├── legal/         # Contratos, compliance
├── people/        # Registro personas (CTAEX, paginado)
├── biometric/     # Datos biométricos (encriptados)
├── emergency/     # Fragmentos Shamir (copias locales)
├── system/        # Roles, perfiles, auditorías
└── index.json     # Índice firmado (GPG) para integridad
```

---

## 5. Índice firmado

```bash
# Generar índice (ejemplo)
jq -n '{"version":"1.0","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","entries":[]}' > /mnt/sandisk/CASTUO_SECURE/index.json
gpg --sign --local-user "CASTUO-SYSTEM <security@castuo-system.com>" --output /mnt/sandisk/CASTUO_SECURE/index.json.sig /mnt/sandisk/CASTUO_SECURE/index.json
```

---

## 6. Backup automático

- **Script**: `scripts/backup/automated-backup.sh`
- **Cron**: `0 3 * * * /opt/castuo/scripts/backup/automated-backup.sh`
- Sincroniza con GaiaChain (encrypted-backup.sh) y, si el SanDisk está montado, exporta GaiaChain al SanDisk.

---

## 7. Desmontaje

```bash
umount /mnt/sandisk/CASTUO_SECURE   # si se montó VeraCrypt
umount /mnt/sandisk
cryptsetup close castuo_secure
```

No dejar la contraseña LUKS en historial ni en disco.
