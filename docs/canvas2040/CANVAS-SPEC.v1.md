# CANVAS-SPEC.v1.md

Formato comun para documentacion auditable, cifrada y auto-ejecutable (CASTUO-SYSTEM 2040).

Este "spec" es la fuente de verdad para que los equipos creen "Canvas Cards" consistentes, reutilicen el cifrador existente y vinculen evidencias (Gemelos Digitales y GaiaChain) sin duplicar logica ni romper despliegues.

## 1) Estructura Base de un Canvas (YAML)

Ejemplo: `docs/canvas2040/modules/universal-core.canvas.yaml`

```yaml
---
module: "universal-core"          # Nombre unico del modulo (ej: "quantum-agrovoltaic")
version: "1.0.0"                  # Version del canvas (semver)
jurisdictions:                   # Jurisdicciones aplicables (heredadas del mapeo de docs/GEMELO_DIGITAL_ULTRA_SEGURO.md)
  - "EU"                          # Union Europea (GDPR, AI Act)
  - "ES"                          # Espana (RD 903/2025, Ley de IA 2026)
  - "GLOBAL"                      # Normativas globales (ISO 27001, NIST)
description: |                    # Descripcion clara y verificable del modulo
  Modulo central de CASTUO-SYSTEM 2040, con integracion de:
  - Gemelos digitales (seguridad, legal, cumplimiento).
  - GaiaChain 3.0 para trazabilidad atomica.
  - Cumplimiento auto-adaptativo.
security_controls:
  encryption: "USE: backend/scripts/encrypt_document.py" # Debe reutilizar el cifrador existente
  access: "Shamir-7/11 (custodia multi-continental)"
  audit: "Gemelos Digitales + GaiaChain (opcional si GAIA_CHAIN_API_URL esta definida)"
data_classification:
  - "PII"                          # Datos personales (GDPR)
  - "AGRONOMIC"                    # Datos de cultivos (Ph. Eur. 3028)
  - "FINANCIAL"                    # Transacciones BioCoin (AEMPS, FDA)
compliance_mapping:
  EU:
    - "GDPR: Art. 17 (Derecho al olvido)"
    - "AI Act 2024: Sec. 3.2 (Transparencia)"
  ES:
    - "RD 903/2025: Sec. 4.1 (Trazabilidad)"
  GLOBAL:
    - "ISO 27001: A.9.4 (Control de acceso)"
evidence_checks:                 # Comandos para generar evidencias (se ejecutan via EXECUTION-MANIFEST)
  - command: "gemelo-digital audit --module {{module}} --type legal --output reports/legal_{{module}}_{{timestamp}}.json"
    description: "Auditoria legal con Gemelo Digital."
    output: "reports/legal_{{module}}_{{timestamp}}.json"
  - command: "python backend/scripts/encrypt_document.py --input reports/ --output encrypted/"
    description: "Cifrar evidencias generadas con el cifrador existente."
    output: "encrypted/{{module}}_{{timestamp}}.enc"
runbook_commands:                # Comandos operativos (optional). Deben ser compatibles con CI/CD.
  - "kubectl apply -f k8s/{{module}}.yaml"
dependencies:                     # Optional: servicios/microservicios requeridos para ejecutar evidencias
  - "gaiachain"
  - "digital-twins"
---
```

## 2) Campos obligatorios vs opcionales

Obligatorios:
- `module`
- `version`
- `jurisdictions`
- `description`
- `security_controls`
- `data_classification`
- `compliance_mapping`
- `evidence_checks`

Opcionales:
- `runbook_commands`
- `dependencies`

## 3) Vinculacion con lo existente (no duplicar)

- Jurisdicciones y mapeo de cumplimiento: basarse en `docs/GEMELO_DIGITAL_ULTRA_SEGURO.md`.
- Cifrado de evidencias: reutilizar `backend/scripts/encrypt_document.py`.
- Gemelos digitales: evidencias se generan/validan invocando los endpoints o comandos ya presentes en el flujo actual (GemeloSeguridad/GemeloLegal).
- GaiaChain 3.0: usar evidencias solo si aplica; las llamadas de red deben respetar air-gap (regla en EXECUTION-MANIFEST).

## 4) Regla de Air-gap (seguridad soberana)

Cuando el entorno este en modo air-gap, los canvas deben:
- evitar llamadas a APIs externas (incluyendo GaiaChain remota si no esta local),
- ejecutar solo comprobaciones locales (tests, validaciones offline),
- registrar el estado "skipped" en evidencias cifradas si el EXECUTION-MANIFEST asi lo indica.

