# Deploy Hetzner — referencia

## Checklist D1 (Cursor → Hetzner)

**[docs/deploy/CHECKLIST-CURSOR-HETZNER-D1.md](../docs/deploy/CHECKLIST-CURSOR-HETZNER-D1.md)**

## TRL-6 integración → TRL-7/9 industrial (cliente)

**[CHECKLIST-TRL7-INDUSTRIAL-LIVE.md](CHECKLIST-TRL7-INDUSTRIAL-LIVE.md)** — etapas verificables para operación en condiciones industriales.

## Archivos en la raíz del repo

- `docker-compose.prod.yml`, `Dockerfile`, `castuo.conf`, `castuo-https.auto.conf`, `init-db/`, `.env.production.example`
- **`deploy.sh`** — despliegue (`--full`, `--api`, `--n8n`, `--nginx`, `--status`, `--rollback`, `--remote`)
- **`hetzner-init.sh`** — bootstrap del VPS (también consumible por `curl` desde `raw.githubusercontent.com`)
- **`deploy/setup-ssl.sh`** — DNS + Certbot + TLS endurecido + cron renew (ver [DNS-SSL-HETZNER-CX22.md](../docs/deploy/DNS-SSL-HETZNER-CX22.md))

## Comandos rápidos

```bash
./deploy.sh --full
./deploy.sh --status
```

Post-deploy (salud api interna, tablas `hydroponics_*`, opcional health pública y Prometheus): **`./deploy/verify_stack.sh`** (ver cabecera del script para variables).

Producción OT + scraping métricas `ot_*`: **`./deploy/verify_production.sh`**.

Otros artefactos en esta carpeta: `traefik.yml`, `dynamic.yml`, `README.eu-oss.md`.

## MQTT TLS (broker dedicado)

- Compose: **`deploy/docker-compose.mqtt.yml`** (o raíz: `docker-compose.mqtt.yml` que lo incluye).
- Checklist mínimo priorizado: **[MQTT-TLS-CHECKLIST-MINIMO.md](MQTT-TLS-CHECKLIST-MINIMO.md)**
- Detalle: `mqtt-tls/README.md`

## Pendrive LUKS (tokens `*_FILE`)

- Windows (empaquetar NTFS, sin LUKS): `..\scripts\windows\prepare_pendrive_final.ps1 -DriveLetter D` (o `Prepare-CastuoPendrive.ps1`; opc. `-FormatNtfs`, `-IncludeOptionalTokens`, `-SkipTokens`, `-RepoRoot`)
- Checklist de ficheros: **[PENDRIVE-CONTENIDO.md](PENDRIVE-CONTENIDO.md)**
- Instrucciones operador: **[INSTRUCCIONES-PENDRIVE.md](INSTRUCCIONES-PENDRIVE.md)** · plantilla env: `config.env.pendrive.example`
- Preparación (una vez): `prepare_pendrive_luks.example.sh`
- Montaje con frase de paso: `mount_secure.example.sh` → `/mnt/castuo_secure/tokens`
- Desmontaje: `umount_secure.example.sh`
- Montaje interactivo clásico: `montar_pendrive.example.sh` (variable `LUKS_PARTITION`)

Detalle operativo: [PRONTUARIO-AGROTECH-TLS.md §8](../docs/deploy/PRONTUARIO-AGROTECH-TLS.md), override Docker en la raíz: `docker-compose.override.tokens.example.yml`.
