# Runbook — Backup `cerebros/` + Postgres (stack CASTÚO)

Objetivo: copias **fuera del servidor** de Markdown de auditoría y de la base **postgres-cerebros**, con ventana de mantenimiento acotada.

## 1. Alcance

| Activo | Origen típico | Notas |
|--------|----------------|--------|
| Markdown auditoría | `./cerebros/auditoria` (host) = `/space` SilverBullet + `journal/` vía n8n | Sin secretos en claro en los `.md` salvo que los hayas escrito tú. |
| Markdown soberano | `./cerebros/soberano` | Misma política de confidencialidad. |
| Postgres AGRI-BRAIN | Contenedor `castuo-cerebros-postgres`, DB `agri_brain` (puerto host **5433** por defecto) | Incluye credenciales en `.env.cerebros`. |

## 2. Backup lógico Postgres (recomendado)

En el **host** (con `docker`):

```bash
# Ajusta fecha y ruta de destino
export TS=$(date -u +%Y%m%dT%H%M%SZ)
export DEST=/ruta/segura/backups/castuo-cerebros

mkdir -p "$DEST/$TS"

docker exec castuo-cerebros-postgres pg_dump -U "${CEREBROS_POSTGRES_USER:-agri_brain}" -d "${CEREBROS_POSTGRES_DB:-agri_brain}" -Fc -f /tmp/agri_brain.dump

docker cp castuo-cerebros-postgres:/tmp/agri_brain.dump "$DEST/$TS/agri_brain.dump"
```

Restauración (referencia):

```bash
docker cp ./agri_brain.dump castuo-cerebros-postgres:/tmp/
docker exec -it castuo-cerebros-postgres pg_restore -U agri_brain -d agri_brain --clean --if-exists /tmp/agri_brain.dump
```

## 3. Backup de carpetas Markdown

```bash
export TS=$(date -u +%Y%m%dT%H%M%SZ)
export DEST=/ruta/segura/backups/castuo-cerebros
tar -czvf "$DEST/$TS/cerebros-auditoria-soberano.tgz" -C /ruta/al/repo/Castuo-System cerebros/auditoria cerebros/soberano
```

Excluye `operativo` si solo contiene pruebas vacías. Cifra el `.tgz` con **age** o **gpg** antes de subirlo a almacenamiento compartido.

## 4. RPO / RTO (definir por negocio)

- **RPO:** ¿Cuánta pérdida de diarios o filas SQL es aceptable? (ej. 24 h → backup diario.)
- **RTO:** Tiempo máximo para volver a levantar compose + restaurar dump.

## 5. Comprobaciones post-backup

- `pg_restore --list` o tamaño del dump > 0.
- `tar -tzvf …tgz | head` lista `journal/diario-*.md` si existen.

## 6. Script unificado (repo)

Desde la raíz del repositorio (Linux/macOS/Git Bash), con `docker compose` y el stack levantado cuando toque Postgres:

```bash
chmod +x scripts/backup_castuo_cerebros.sh
./scripts/backup_castuo_cerebros.sh
```

- Escribe en `backups/castuo-cerebros/<timestampUTC>/` (sobrescribible con `CASTUO_BACKUP_ROOT`).
- `CASTUO_BACKUP_PRUNE_DAYS=7` elimina subcarpetas de backup más antiguas que N días (opcional).
- Requiere `.env.cerebros` cargado o variables `CEREBROS_POSTGRES_*` + `PGPASSWORD` coherentes con `docker-compose.cerebros.yml`.

## 7. Relación con n8n

Los workflows viven en el volumen `.n8n` de cada instancia; **no** están en `cerebros/`. Export periódico de workflows desde la UI o backup del volumen Docker `n8n_trillizo_data`, etc.
