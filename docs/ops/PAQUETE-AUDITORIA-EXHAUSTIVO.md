# Paquete de Auditoria Exhaustivo

## Objetivo
Generar un bundle verificable y repetible con estado tecnico, legal y operativo del sistema.

## Comando unico

```bash
make audit-package-exhaustive
```

## Salida
Se crea un directorio en:

- artifacts/audit-package-YYYYMMDD-HHMMSS/

Contenido principal:
- system-info.txt
- PORTADA-EJECUTIVA.md
- AUDIT-REPORT.md
- summary.json
- manifest.txt
- logs/*.log
- evidence/ (copia de artefactos clave)
- integrity.sha256
- audit-package-*.zip
- audit-package-*.sha256

## Criterio de estado
- GO: todos los checks criticos en PASS.
- NO-GO: al menos un check critico en FAIL.

## Checks ejecutados
- make test-github-operativity
- make test-github-certification
- REQUIRE_GITHUB_HARDENING=0 bash scripts/setup-prod-hardening.sh
- make ctaex-compliance-check
- make legal-compliance-check
- pytest -q tests/test_dsar_router.py
- pytest -q tests/test_api.py -k iot_telemetry_
- bash scripts/audit-evidence-security-scan.sh <evidence_dir>

Total: 8 checks criticos

## Portada ejecutiva
El paquete genera automaticamente una portada en:

- PORTADA-EJECUTIVA.md

Incluye:
- Estado GO/NO-GO
- Resultado de checks (ejemplo: 7/7)
- Tabla de verificadores externos (CDTI, CTAEX, AENOR)
- Referencias de bundle (ZIP + checksum)
- Valoracion economica estimativa interna (con disclaimer)

## Uso recomendado
1. Ejecutar antes de auditorias CTAEX o revisiones de cumplimiento.
2. Adjuntar AUDIT-REPORT.md y summary.json en entregables.
3. Verificar `integrity.sha256` y checksum del ZIP antes de compartir.
4. Conservar bundles historicos para trazabilidad de evidencia.
