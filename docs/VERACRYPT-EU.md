# VERACRYPT EU (repo)

## Objetivo

Endurecer la soberania de datos mediante cifrado de disco completo o contenedores cifrados, alineado con buenas practicas GDPR (minimizar exposicion) y NIS2 (resiliencia frente a accesos no autorizados).

## Principios de implementacion en este repo

1. No hardcodear contraseas en scripts.
2. Usar password file o variables de entorno gestionadas fuera del repo.
3. Registrar trazabilidad (hash + evento) con el mismo mecanismo del repo: `backend/routers/blockchain_gaia.py` via `POST /api/v1/witness`.

## Scripts disponibles

- `scripts/security/install_veracrypt_eu.sh`
- `scripts/security/create_veracrypt_container_eu.sh`
- `scripts/security/mount_veracrypt_container_eu.sh`
- `scripts/security/umount_veracrypt_container_eu.sh`
- `scripts/security/veracrypt_eu_audit.py`
- `scripts/security/notarize_veracrypt_event.sh`

## Nota de verificacion

La verificacion completa (montaje/desmontaje) depende del SO y de permisos del entorno. El script `veracrypt_eu_audit.py` intenta hacerlo solo si se habilita explicitamente el modo de prueba.

