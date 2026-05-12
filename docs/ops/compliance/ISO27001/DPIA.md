# DPIA / Evaluacion de Impacto (Plantilla ISO/GDPR)

## Objetivo
Documentar la evaluacion de impacto para tratamientos con posible riesgo alto para derechos y libertades.

## Referencias de tu repositorio (ejemplos)
- `docs/legal/DPIA-CASTUO-SYSTEM.md`
- `docs/legal/TRL10/README_WINDOWS.md` (si aplica a evidencias y alcance)

## Datos y tratamiento (placeholders)
- Responsable del tratamiento: [ROLE/ENTITY]
- Descripcion del tratamiento: [RESUMEN]
- Finalidades: [PURPOSES]
- Base legal: [LEGAL_BASIS]
- Categorias de interesados: [PATIENTS_USERS_EMPLOYEES]
- Categorias de datos: [PERSONAL_DATA_SENSITIVE]

## Necesidad y proporcionalidad
- Justificacion: [TEXT]
- Medidas para minimizar datos: [TEXT]

## Analisis de riesgos
Metodologia:
- [METHOD]

Riesgos principales (ejemplos):
- Exposicion de datos sensibles por logs
- Acceso no autorizado a evidencias
- Modificacion no detectable de certificados o hashes

## Medidas mitigadoras (placeholders)
- Cifrado y secretos fuera del repo (VeraCrypt / claves en entorno)
- Integridad por hashes y testigos (GaiaChain witness)
- Minimizar datos en traces y auditorias
- Continuidad operativa con SQLite de resiliencia

## Decision final (placeholders)
Estado:
- [APROBADO_CONCONDICIONES / REQUIERE_MEJORAS / NO_APROBADO]

Fecha y aprobacion:
- [DATE] / [APPROVER]

