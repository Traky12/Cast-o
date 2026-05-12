# Contenido del pendrive CASTÚO

En **producción** el volumen debería ir **cifrado con LUKS** en Linux (`deploy/prepare_pendrive_luks.example.sh`). Los secretos en `tokens/` son **un fichero = una sola línea**, sin BOM UTF-8 (evitar `Out-File` por defecto en Windows para tokens).

## Preparación rápida en Windows (paquete NTFS)

Sirve para **empaquetar** scripts, checklist y plantillas. **NTFS no sustituye LUKS.**

Desde la raíz del repo (PowerShell **elevado** solo si usas `-FormatNtfs`):

```powershell
cd "C:\ruta\Castuo-System"
.\scripts\windows\prepare_pendrive_final.ps1 -DriveLetter D
# equivalente canónico:
.\scripts\windows\Prepare-CastuoPendrive.ps1 -DriveLetter D
```

Formatear el volumen (opcional, **borra datos**):

```powershell
.\scripts\windows\prepare_pendrive_final.ps1 -DriveLetter D -FormatNtfs
```

Tokens opcionales (`vault.token`, `n8n.key`, `iot.key` con marcadores `REPLACE_*`):

```powershell
.\scripts\windows\prepare_pendrive_final.ps1 -DriveLetter D -IncludeOptionalTokens
```

Verificación rápida:

```powershell
Get-ChildItem -Path "D:\" -Recurse
```

El script genera los tres tokens mínimos en **UTF-8 sin BOM**, copia scripts (`mount` / `umount` / `prepare_pendrive_luks`), `verify_castuo_tokens.py`, `PENDRIVE-CONTENIDO.md`, `INSTRUCCIONES-PENDRIVE.md`, `INSTRUCCIONES.md`, `config.env` y `config.env.pendrive.example`, y al final indica si los tres tokens obligatorios **no llevan BOM**.

Verificación de estructura y bytes (los tres primeros bytes no deben ser `EF BB BF`):

```powershell
Get-ChildItem -Path "D:\" -Recurse
$check = {
  param($p)
  $b = [System.IO.File]::ReadAllBytes($p)
  $bom = $b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF
  if ($bom) { "BOM en $p" } else { "OK sin BOM: $p" }
}
& $check "D:\tokens\admin_general.token"
& $check "D:\tokens\farmer.key"
& $check "D:\tokens\technician.key"
```

## Identificar el USB en Linux

En Windows puede ser **D:**; en el servidor Linux usa:

```bash
lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS
ls -l /dev/disk/by-id/
```

Actualiza `config.env` con el `by-id` real (no uses un nombre inventario tipo `usb-CASTUO_SECURE`).

## Archivos obligatorios (`tokens/`)

| Fichero | Variable `*_FILE` típica |
|---------|---------------------------|
| `admin_general.token` | `CASTUO_ADMIN_GENERAL_BEARER_FILE` |
| `farmer.key` | `FARMER_API_KEY_FILE` |
| `technician.key` | `MQTT_TECHNICIAN_PASSWORD_FILE` |

## Archivos opcionales (`tokens/`)

Puedes usar los nombres que prefieras siempre que `.env` / compose apunten al mismo path.

| Fichero sugerido | Uso / variable típica |
|------------------|------------------------|
| `vault.token` | `VAULT_TOKEN_FILE` (contenido = token Vault) |
| `robotics_lab.token` | `CASTUO_ROBOTICS_LAB_BEARER_TOKEN_FILE` |
| `n8n.key` | Secreto para flujos (si lo lees vía `*_FILE` personalizado; n8n suele usar su propia config) |
| `iot.key` | `IOT_API_KEY` o clave dispositivo si la expones como fichero |

Más referencias: `backend/models/system_admin_playbook.py` (`CRITICAL_ENV_VARS`).

## Raíz del USB (tras `Prepare-CastuoPendrive.ps1`)

```text
D:\
├── tokens\
│   ├── admin_general.token
│   ├── farmer.key
│   ├── technician.key
│   └── (opcionales con -IncludeOptionalTokens: vault.token, n8n.key, iot.key)
├── config.env
├── config.env.pendrive.example
├── mount_secure.example.sh
├── umount_secure.example.sh
├── prepare_pendrive_luks.example.sh
├── verify_castuo_tokens.py
├── docker-compose.rgi.example.yml   (si existe en el repo; referencia edge RGI)
├── PRONT-*.md                       (guías cortas docs/deploy; prefijo PRONT-, no PRONTUARIO-)
├── TRL-MASTER.md                    (tabla TRL orientativa; si existe en repo)
├── scripts\ai\generative\   (RGI/NF plantilla)
├── scripts\ai\sigpac\      (geotiff_stats + requirements; si existe en repo)
├── scripts\ai\n8n\        (workflow_manager CLI; si existe en repo)
├── scripts\ai\robotics\    (robot_controller lab + tests; si existe en repo)
├── models\rg\               (pesos .pt / .onnx si los generaste localmente)
├── PENDRIVE-CONTENIDO.md   (ojo: nombre exacto; no PENDRUIVE-CONTENIDO)
├── INSTRUCCIONES-PENDRIVE.md
└── INSTRUCCIONES.md
```

## Configuración en Linux (tras transferir)

```bash
ls -l /dev/disk/by-id/
# Editar config.env donde esté montado el USB (ej. /media/usuario/…/config.env) o copiar al servidor
# Montaje LUKS (volumen ya cifrado):
chmod +x ./mount_secure.example.sh
./mount_secure.example.sh /dev/disk/by-id/usb-...
export CASTUO_TOKENS_PATH=/mnt/castuo_secure/tokens
python3 /ruta/al/repo/scripts/verify_castuo_tokens.py
# o, si copiaste el .py en el USB montado en /media/usb:
# python3 /media/usb/verify_castuo_tokens.py
```

Despliegue Docker (desde la raíz del repo en el servidor):

```bash
cp docker-compose.override.tokens.example.yml docker-compose.override.yml
# Editar .env.production: rutas *_FILE bajo /app/tokens/ (ver .env.production.example)
```

## Permisos recomendados (Linux, volumen montado)

```bash
sudo chmod 600 /mnt/castuo_secure/tokens/*
sudo chmod 700 /mnt/castuo_secure/*.sh 2>/dev/null || true
```

## Generación segura (Linux, LUKS montado)

```bash
openssl rand -hex 32 | sudo tee /mnt/castuo_secure/tokens/admin_general.token >/dev/null
openssl rand -hex 24 | sudo tee /mnt/castuo_secure/tokens/farmer.key >/dev/null
openssl rand -hex 24 | sudo tee /mnt/castuo_secure/tokens/technician.key >/dev/null
sudo chmod 600 /mnt/castuo_secure/tokens/*
```

## Scripts del repo (canónicos)

- Preparación LUKS (Linux): `deploy/prepare_pendrive_luks.example.sh`
- Montaje con frase de paso: `deploy/mount_secure.example.sh`
- Desmontaje: `deploy/umount_secure.example.sh`
- Verificación: `scripts/verify_castuo_tokens.py` + `CASTUO_TOKENS_PATH`

Instrucciones operativas: `deploy/INSTRUCCIONES-PENDRIVE.md` · Prontuario: `docs/deploy/PRONTUARIO-AGROTECH-TLS.md` §8.
