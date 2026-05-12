# Pendrive CASTÚO — Instrucciones de uso

## Importante (NTFS en Windows vs LUKS en Linux)

- Si preparaste el USB en **Windows** con NTFS, los datos en `tokens/` **no van cifrados con LUKS** en ese volumen. Sirve como **paquete de transporte** o copia de trabajo.
- Para **cifrado completo del soporte** (recomendado en servidor), crea el volumen LUKS en **Linux** con `deploy/prepare_pendrive_luks.example.sh` y **copia** allí el contenido de `tokens/` (o genera secretos nuevos allí).

## Montaje en Linux (LUKS ya creado en el pendrive)

1. Conectar el pendrive al servidor.
2. Obtener el nodo estable: `lsblk` y `ls -l /dev/disk/by-id/`.
3. Editar `config.env` donde el escritorio montó el USB (p. ej. `/media/usuario/DISK_LABEL/config.env`) o tras copiarlo al servidor; sustituir `CASTUO_LUKS_DEVICE` por el `by-id` real.
4. Ejecutar el montaje (desde el repo o desde la copia en el pendrive):

```bash
export CASTUO_LUKS_DEVICE=/dev/disk/by-id/usb-...
./deploy/mount_secure.example.sh "$CASTUO_LUKS_DEVICE"
```

Introduce la **frase de paso LUKS** cuando se solicite.

## Verificación de tokens

Con el repo en el servidor:

```bash
export CASTUO_TOKENS_PATH=/mnt/castuo_secure/tokens
python3 scripts/verify_castuo_tokens.py
```

Si solo tienes el script copiado en el USB (misma raíz que `verify_castuo_tokens.py`):

```bash
export CASTUO_TOKENS_PATH=/mnt/castuo_secure/tokens
python3 /ruta/montaje_usb/verify_castuo_tokens.py
```

## Desmontaje

```bash
./deploy/umount_secure.example.sh
```

## Contenido típico del USB

| Elemento | Descripción |
|----------|-------------|
| `tokens/` | Credenciales (un fichero = una línea, sin BOM UTF-8) |
| `config.env` | Plantilla de variables para el operador (editar `by-id`) |
| `mount_secure.example.sh` / `umount_secure.example.sh` | Copia de ayuda; la versión canónica sigue en el repo bajo `deploy/` |
| `PENDRIVE-CONTENIDO.md` | Checklist y mapeo `*_FILE` |
| `INSTRUCCIONES.md` | Copia de este documento en el USB (nombre corto para el operador) |
| `INSTRUCCIONES-PENDRIVE.md` | Versión en repo (mismo contenido orientativo) |

## Permisos (en Linux, con el volumen montado)

```bash
sudo chmod 600 /mnt/castuo_secure/tokens/*
sudo chmod 700 /mnt/castuo_secure/*.sh 2>/dev/null || true
```

## Despliegue Docker

Tras montar y verificar: `docker-compose.override.tokens.example.yml` + `./deploy.sh --local` (ver `docs/deploy/PRONTUARIO-AGROTECH-TLS.md` §8.2).
