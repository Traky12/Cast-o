# WebCheck Integration (Self-Hosted, Air-Gap Safe)

Este documento describe cómo ejecutar **WebCheck** de forma **soberana** dentro del búnker, sin depender de endpoints externos.

## 1. Requisitos
- Docker instalado
- Puerto libre `3000` en el host

## 2. Ejecución local (self-hosted)
1. Levantar el contenedor:

```bash
docker compose -f docker-compose.webcheck.yml up -d
```

2. Ejecutar el auditor (self-hosted + air-gap aware):

```bash
WEBCHECK_TARGET="127.0.0.1" \
BUNKER_AIRGAP="false" \
./scripts/seguridad/webcheck_audit.sh
```

3. Reporte generado:
- `webcheck_report.json`

## 3. Modo air-gap
Si `BUNKER_AIRGAP=true`, el script **no ejecuta** auditorías y sale con éxito (`exit 0`).

## 4. Integración CI/CD (GitLab)
Para que la auditoría se ejecute en GitLab, añadir un job que llame a `scripts/seguridad/webcheck_audit.sh`
y ejecute el escaneo contra un `WEBCHECK_TARGET` definido. Recomendado: evitar ejecuciones cuando el búnker
está en air-gap.

