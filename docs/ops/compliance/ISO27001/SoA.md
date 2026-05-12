# SoA ISO 27001 (Statement of Applicability) - Scaffold

## Alcance (placeholders)
- Sistema: Castuo-System (backend, gemelos, orquestacion, evidencia/traceabilidad)
- Marco: ISO/IEC 27001
- Version interna: ISO27001-SoA-1.0

## Referencias internas (ejemplos)
- Politicas y guias ya existentes (ajustar a tu repos):
  - `docs/ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md`
  - `docs/EVIDENCIA-LEGAL-VERIFICADA.md`
  - `docs/legal/DPIA-CASTUO-SYSTEM.md`

## Politicas y controles (plantilla por secciones)
Control: A.5 Politicas de seguridad
- A.5.1.1 Politicas de seguridad de la informacion
- A.5.1.2 Revision de politicas

Control: A.6 Organizacion de la seguridad
- A.6.1.1 Roles y responsabilidades
- A.6.1.5 Contacto con autoridades

Control: A.7 Seguridad de los activos
- A.7.1.1 Inventario de activos
- A.7.2.1 Clasificacion de la informacion

Control: A.10 Seguridad de las comunicaciones
- A.10.1.1 Controles de red
- A.10.1.2 Acuerdos de intercambio de informacion

Control: A.12 Seguridad en las operaciones
- A.12.3.1 Copias de seguridad (IPFS + GaiaChain, segun template)
- A.12.4.1 Registros y monitoreo (Grafana/Prometheus, evidencia local y witness)

Control: A.13 Control de acceso
- A.13.1.1 Control de acceso a la informacion (RBAC, 2FA)
- A.13.2.1 Gestion de acceso (YubiKey / llaves de hardware, segun alcance)

Control: A.16 Gestion de incidentes
- A.16.1.4 Evaluacion y decision sobre eventos de seguridad
- A.16.1.5 Respuesta a incidentes

## Observaciones
Esta SoA es una plantilla. Debe completarse con:
- Justificacion de inclusion/exclusion para cada control aplicable
- Evidencia concreta (documentos y rutas del repo)
- Responsables (roles) y frecuencia de revision

## Evidencia inmutable en GaiaChain (witness)
Para cada evidencia documental (politicas, minutas, resultados de auditoria interna), recomendamos:
1) Calcular SHA-256 del contenido del documento (o del artefacto de auditoria).
2) Registrar un witness en GaiaChain usando el mecanismo verificado del repo:
   - `scripts/Register-SecurityEvent.ps1`
   - o, si aplica, el endpoint remoto del repo `POST /api/v1/witness` con payload minimal `{hash, coop_id, ipfs_cid}`.

Ejemplo (PowerShell, preferido por contrato verificado del repo):
```powershell
.\scripts\Register-SecurityEvent.ps1 `
  -EventType "iso27001_isms_document" `
  -EventData @{ document_path="docs/ops/compliance/ISO27001/ISMS-Policy.md"; sha256="TODO_CALCULAR" } `
  -CoopId 1 `
  -Severity "info" `
  -LogEventInBackend
```

## Plantilla ejecutable: Auditoria interna (checklist)
Estructura propuesta para una auditoria interna (placeholders):
- `audit_id`: AUDIT-ISO27001-[YYYYMMDD]-[NN]
- `scope`: [alcance]
- `criteria`: [criterios ISO27001]
- `method`: [entrevistas, revision de evidencias, pruebas]
- `findings`: lista de hallazgos (cada uno con `severity`, `requirement`, `evidence_ref`)
- `status`: `open|closed`

Registro de evidencia:
1) Guardar el resultado como un archivo versionado (ej: `docs/audits/[audit_id].json` o `.md`).
2) Notarizar el hash del resultado final con `scripts/Register-SecurityEvent.ps1`.

