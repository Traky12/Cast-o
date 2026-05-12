# Migracion a GitLab Self-Hosted (Soberania Total)

## Objetivo
Eliminar dependencia de GitLab.com (EE.UU.) y garantizar control absoluto sobre codigo y datos en infraestructura soberana (Hetzner / OVHcloud).

## Requisitos
- Servidor: Ubuntu 22.04 LTS (o equivalente).
- Recursos recomendados: 4 vCPUs, 16GB RAM, 200GB SSD.
- Dominio: `gitlab.castuo-system.eu` (ajustar a tu dominio).
- Acceso admin por SSH.
- Variables de entorno para backups: IPFS y GaiaChain (claves fuera del repo).

## Estructura de artefactos en el repo
- `scripts/ops/gitlab-selfhosted/setup_gitlab.sh`: plantilla de instalacion/puesta en marcha.
- `docs/ops/gitlab-selfhosted/backup_to_ipfs.sh`: script de backup (instalable en `/usr/local/bin/`).

## Paso 1) Preparar el servidor
Template (revisa antes de ejecutar):

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl openssh-server ca-certificates tzdata perl
```

## Paso 2) Instalar GitLab (self-hosted)
Ejecuta la plantilla de scaffolding:

```bash
chmod +x scripts/ops/gitlab-selfhosted/setup_gitlab.sh
scripts/ops/gitlab-selfhosted/setup_gitlab.sh
```

Notas:
- `EXTERNAL_URL` y `ssh port` se deben ajustar al entorno real.
- Este documento evita valores sensibles. Define las variables fuera del repo.

## Paso 3) Backup diario a IPFS y notarizacion opcional en GaiaChain
El script de backup usa:
- `gitlab-backup create`
- `ipfs add` para obtener el `CID`
- `POST /api/v1/witness` en GaiaChain (opcional si `GAIA_CHAIN_API_KEY` esta presente)

Instalacion (ejemplo):

```bash
sudo cp "docs/ops/gitlab-selfhosted/backup_to_ipfs.sh" /usr/local/bin/backup_to_ipfs.sh
sudo chmod +x /usr/local/bin/backup_to_ipfs.sh
```

Cron (ejemplo):

```cron
0 3 * * * /usr/local/bin/backup_to_ipfs.sh >> /var/log/gitlab/backup_cron.log 2>&1
```

## Variables de entorno (placeholders)
Define estas variables para `backup_to_ipfs.sh`:
- `IPFS_API_ADDR` (ej: `127.0.0.1:5001`) o cambia el script para tu IPFS.
- `GAIA_CHAIN_API_URL` (ej: `https://gaiachain.castuo-system.eu`)
- `GAIA_CHAIN_API_KEY` (string; mantener fuera del repo)
- `GAIA_COOP_ID` (int; default `1`)

## Paso 4) Verificacion
- Confirmar que existen backups en el directorio esperado de GitLab.
- Confirmar que `ipfs add` retorna un CID.
- Si `GAIA_CHAIN_API_KEY` esta configurado, confirmar respuesta 2xx en el `curl` de witness.

