# Prontuario maestro — seguridad y backup en pen drive (2026)

*Procedimiento para **copias de seguridad** y **almacenamiento portátil** cifrado de componentes CASTÚO-System. Prioriza **FOSS** (LUKS, GnuPG, `sqlite3`, `pg_dump`). **No** sustituye Vault, KMS ni política de retención de la DPIA.*

**Relación:** [PLAN-MEJORA-INMEDIATA-CASTUO-2026.md](./PLAN-MEJORA-INMEDIATA-CASTUO-2026.md) · [POLITICA-ROTACION-CLAVES.md](./POLITICA-ROTACION-CLAVES.md) · [PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md) · [PRONTUARIO-BACKUP-SEGURO-PEN-DRIVE.md](./PRONTUARIO-BACKUP-SEGURO-PEN-DRIVE.md) · `backend/database/local_db.py` *(ruta por defecto `resilience.db`)*

---

## 📋 1. Principios

1. **Cifrado** en reposo del medio *(LUKS en el pendrive)* y de los **artefactos** *(GPG simétrico, `age`, o contenedor LUKS interno)*.  
2. **Backup verificado:** prueba de **restauración** periódica + **integridad** *(manifiesto con SHA256 o descifrado de prueba)*.  
3. **Reproducible:** scripts versionados en `docs/deploy/scripts/` o repo interno; sin secretos en el git.  
4. **FOSS** preferente; licencias auditables.  
5. **Integridad:** manifiesto firmado o hashes archivados; ver §5.

**Límites:** el pendrive físico se puede perder — la **frase de paso LUKS** y la de **GPG** deben ser **independientes** y no almacenarse en el mismo llavero sin segunda copia controlada.

---

## 🔧 2. Estructura recomendada en el volumen

Tras montar el dispositivo cifrado *(p. ej. `/mnt/pen_castuo`)*:

```text
/mnt/pen_castuo/
├── backups/
│   ├── sqlite/
│   ├── postgres/
│   ├── configs/
│   └── manifests/          # SHA256 y metadatos por lote
├── docs/                     # Copia offline de prontuarios críticos (opcional)
├── scripts/                  # backup_castuo.sh, restore_*.sh (sin claves)
├── logs/                     # Salida de cron (sin secretos)
└── README_OFFLINE.md         # Instrucciones sin red
```

---

## 🔐 3. Cifrado del pendrive *(capa 1)*

### 3.1. LUKS2 *(Linux)*

```bash
# Sustituir /dev/sdX por el dispositivo correcto (¡triple comprobación!)
sudo cryptsetup luksFormat --type luks2 /dev/sdX
sudo cryptsetup open /dev/sdX pen_castuo
sudo mkfs.ext4 -L CASTUO_BACKUP /dev/mapper/pen_castuo
sudo mkdir -p /mnt/pen_castuo
sudo mount /dev/mapper/pen_castuo /mnt/pen_castuo
```

**`/etc/fstab`:** usar **UUID** del mapper o del LUKS, no `/dev/sdX` volátil. Documentación: `blkid`, `crypttab` para desbloqueo en arranque *(evaluar riesgo en portátiles compartidos)*.

```bash
sudo cryptsetup luksChangeKey /dev/sdX
```

*Windows/macOS:* BitLocker, VeraCrypt o contenedor compatible — mismo principio: **volumen cifrado** antes de copiar backups.

---

## 📦 4. Backup y cifrado de artefactos *(capa 2)*

**Reglas**

- La **clave simétrica GPG** no va en el script versionado: usar **`GPG_PASSPHRASE_FILE`** con permisos `600`, `pass`, Vault, o entrada interactiva en operación manual.  
- **`gpg --verify`** sirve para **firmas** digitales; los ficheros cifrados con **`--symmetric`** **no** se “verifican” así. Integridad: **manifiesto SHA256** (§5) o `gpg --decrypt --output /dev/null` *(prueba de descifrado)*.

### 4.1. SQLite

```bash
#!/usr/bin/env bash
set -euo pipefail
DATE="$(date -u +%Y-%m-%dT%H%M%SZ)"
DB_FILE="${CASTUO_SQLITE_PATH:-/var/lib/castuo/resilience.db}"
BACKUP_DIR="/mnt/pen_castuo/backups/sqlite"
mkdir -p "$BACKUP_DIR"
PLAIN="${BACKUP_DIR}/db_${DATE}.sql.gz"
CIPHER="${PLAIN}.gpg"

sqlite3 "$DB_FILE" ".dump" | gzip -c > "$PLAIN"
# Passphrase desde env temporal o fichero 600 — nunca en git
gpg --batch --yes --symmetric --cipher-algo AES256 \
  --passphrase-file "${GPG_PASSPHRASE_FILE:?definir ruta segura}" \
  --output "$CIPHER" "$PLAIN"
shred -u "$PLAIN" 2>/dev/null || rm -f "$PLAIN"

sha256sum "$CIPHER" >> "/mnt/pen_castuo/backups/manifests/${DATE}.sha256"
```

*Alternativa online consistente:* `sqlite3 "$DB_FILE" ".backup '$PLAIN'"` luego comprimir y cifrar.

### 4.2. PostgreSQL

```bash
#!/usr/bin/env bash
set -euo pipefail
DATE="$(date -u +%Y-%m-%dT%H%M%SZ)"
PG_HOST="${PGHOST:-localhost}"
PG_DB="${PGDATABASE:-castuo}"
PG_USER="${PGUSER:-postgres}"
BACKUP_DIR="/mnt/pen_castuo/backups/postgres"
mkdir -p "$BACKUP_DIR"
PLAIN="${BACKUP_DIR}/${PG_DB}_${DATE}.dump"
CIPHER="${PLAIN}.gpg"

pg_dump -h "$PG_HOST" -U "$PG_USER" -F c -b -v -f "$PLAIN" "$PG_DB"
gpg --batch --yes --symmetric --cipher-algo AES256 \
  --passphrase-file "${GPG_PASSPHRASE_FILE:?}" \
  --output "$CIPHER" "$PLAIN"
shred -u "$PLAIN" 2>/dev/null || rm -f "$PLAIN"
sha256sum "$CIPHER" >> "/mnt/pen_castuo/backups/manifests/${DATE}.sha256"
```

### 4.3. Configuraciones *(sin secretos en claro innecesarios)*

```bash
#!/usr/bin/env bash
set -euo pipefail
DATE="$(date -u +%Y-%m-%dT%H%M%SZ)"
# Ajustar: solo árboles que no contengan .env con secretos en claro
CONFIG_PATHS="${CASTUO_CONFIG_TARBALL_PATHS:-/etc/castuo}"
BACKUP_DIR="/mnt/pen_castuo/backups/configs"
mkdir -p "$BACKUP_DIR"
PLAIN="${BACKUP_DIR}/configs_${DATE}.tar.gz"
CIPHER="${PLAIN}.gpg"

tar -czf "$PLAIN" $CONFIG_PATHS
gpg --batch --yes --symmetric --cipher-algo AES256 \
  --passphrase-file "${GPG_PASSPHRASE_FILE:?}" \
  --output "$CIPHER" "$PLAIN"
rm -f "$PLAIN"
sha256sum "$CIPHER" >> "/mnt/pen_castuo/backups/manifests/${DATE}.sha256"
```

---

## 🔄 5. Restauración

### 5.1. SQLite

```bash
BACKUP_FILE="/mnt/pen_castuo/backups/sqlite/db_2026-03-23T120000Z.sql.gz.gpg"
DB_FILE="/var/lib/castuo/resilience.db"
TMP="/tmp/castuo_restore_$$"

gpg --batch --passphrase-file "${GPG_PASSPHRASE_FILE:?}" \
  --output "${TMP}.sql.gz" --decrypt "$BACKUP_FILE"
gunzip -c "${TMP}.sql.gz" | sqlite3 "$DB_FILE"
rm -f "${TMP}.sql.gz"
```

### 5.2. PostgreSQL

```bash
BACKUP_FILE="/mnt/pen_castuo/backups/postgres/castuo_2026-03-23T120000Z.dump.gpg"
gpg --batch --passphrase-file "${GPG_PASSPHRASE_FILE:?}" \
  --output /tmp/castuo_restore.dump --decrypt "$BACKUP_FILE"
pg_restore -h localhost -U postgres -d castuo -v /tmp/castuo_restore.dump
rm -f /tmp/castuo_restore.dump
```

---

## ✅ 6. Verificación de integridad

```bash
# Comprobar hashes del manifiesto del día
cd /mnt/pen_castuo/backups
sha256sum -c manifests/2026-03-23T120000Z.sha256
```

*Prueba de descifrado (sin dejar claro en disco):*

```bash
gpg --batch --passphrase-file "${GPG_PASSPHRASE_FILE:?}" \
  --decrypt --output /dev/null algún_fichero.gpg
```

**No** usar `gpg --verify` sobre `.gpg` simétricos como única prueba.

---

## ⏱ 7. Automatización

```cron
# Crontab root — rutas absolutas; % escapado en cron
0 2 * * * GPG_PASSPHRASE_FILE=/root/.config/castuo/backup.gpg.pass /mnt/pen_castuo/scripts/backup_all.sh >> /mnt/pen_castuo/logs/backup-$(date -u +\%Y-\%m-\%d).log 2>&1
```

*El pendrive debe estar **montado** a las 02:00 o usar script que falle con log claro. Para servidores, preferir **backup a objeto** + este flujo como **copia air-gap** mensual.*

---

## 🎯 8. Conclusión y prioridades

### 8.1. Top 3 inmediatas

1. **Montar estructura + un backup de prueba** y restauración en laboratorio *(1 día)*.  
2. **Manifiesto SHA256** por lote + revisión trimestral de restauración.  
3. **LUKS** en el medio antes de datos sensibles *(1 día)*.

### 8.2. Próximos pasos

- Índice corto: [PRONTUARIO-BACKUP-SEGURO-PEN-DRIVE.md](./PRONTUARIO-BACKUP-SEGURO-PEN-DRIVE.md).  
- Formación del equipo y política de **retención** (copias, destrucción segura del pendrive obsoleto).  
- Alinear con [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) si hay datos personales en los volcados.

---

*Dos llaves en el mismo bolsillo: el pendrive cifrado y la contraseña en Post-it es el adversario que ya ganó.*

🚜 *Pa'lante, campeón.* 🌱
