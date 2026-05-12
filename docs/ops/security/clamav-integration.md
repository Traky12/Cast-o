# Integracion con ClamAV (CI/CD) - Scaffold repo

## Objetivo
Agregar una capa adicional de deteccion de malware en el pipeline de CI/CD para reducir la probabilidad de que codigo malicioso entre en el repositorio.

## Requisitos
- ClamAV instalado en el runner de GitLab (o en la imagen del job).
- Base de firmas actualizada (`freshclam`).

## Enfoque (placeholders, sin modificar operativos)
- No modifica ningun `.gitlab-ci.yml` existente.
- Incluye una plantilla de job en el contenido para que tu equipo la adopte donde corresponda.

## Recomendaciones de soberania
- El escaneo debe ejecutarse en infraestructura controlada por tu organizacion.
- Mantener logs de auditoria (y si aplica, hacer witness/hash en GaiaChain mediante `POST /api/v1/witness` usando el contrato minimal del repo).

## Plantilla de job CI/CD (.gitlab-ci.yml)
Ejemplo de referencia:

```yaml
scan_malware:
  stage: security
  tags:
    - bunker-local
  script:
    - sudo freshclam
    - bash scripts/ops/security/clamav-scan.sh
  artifacts:
    paths:
      - clamav_scan.log
  allow_failure: false
```

## Script plantilla
El repo incluye el scaffolding:
- `scripts/ops/security/clamav-scan.sh`

## Verificacion manual
- Ejecutar el script localmente en el runner.
- Confirmar que `clamav_scan.log` existe.
- Confirmar que el script falla (exit 1) si detecta infectados.

