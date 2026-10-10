# CASTÚO-SYSTEM™ — Project Completion Master Register

**Fecha:** 2026-09-04  
**Repositorio principal:** `Traky12/Cast-o`  
**Estado de publicación:** EVIDENCE-SCOPED / STAGING  
**Producción:** NOT_CLAIMED  
**Objetivo:** disponer de un único registro maestro de madurez, evidencia, seguridad y promoción.

## 1. Regla de verdad del proyecto

Este documento no convierte una capacidad técnica en una afirmación de producción. Cada capacidad debe asociarse a código, prueba, evidencia y fecha de verificación.

Estados permitidos:

- `PASS`: evidencia verificable disponible.
- `PENDING`: trabajo iniciado o preparado, pero falta evidencia suficiente.
- `BLOCKED`: existe un bloqueo técnico/operativo que impide la promoción.
- `NOT_CLAIMED`: no debe presentarse externamente como capacidad comprometida.
- `UNKNOWN`: el repositorio no contiene evidencia suficiente para determinar el estado.

## 2. Superficie observada

El repositorio central contiene, entre otras superficies, API/backend, infraestructura Docker, edge/IoT, integración MQTT/Thingsdata, SABIONDA y agentes, trazabilidad, métricas, seguridad, workflows CI/CD, documentación de arquitectura/evidencias y un front WordPress.

## 3. Gate maestro

| Gate | Dominio | Estado de partida | Condición de cierre |
|---|---|---:|---|
| G0 | Identidad y arquitectura | PASS/PENDING | Roles, repositorios y control plane reconciliados |
| G1 | Seguridad y secretos | BLOCKED | No existen ficheros de secretos versionados; rotación realizada cuando corresponda; alertas críticas evaluadas |
| G2 | Dependencias | BLOCKED | Dependabot/escaneo revisado y riesgo residual documentado |
| G3 | CI/automatización | BLOCKED/PENDING | Runners y checks ejecutan realmente y generan evidencia |
| G4 | Runtime / datos | PENDING | Persistencia, TLS, auth y servicios requeridos demostrados en el entorno objetivo |
| G5 | Evidence / governance | PENDING | Claims enlazados a evidencia y sin sobreafirmaciones |
| G6 | Comercial | NOT_CLAIMED | Pilotos remunerados/clientes/evidencia comercial verificables |
| G7 | Producción | NOT_CLAIMED | Todos los gates anteriores cerrados y release firmado/validado |

## 4. Bloqueadores actuales que NO deben ocultarse

### Seguridad

Existe una incidencia abierta de seguridad (`#12`) que documenta 115 vulnerabilidades detectadas en la rama por defecto: 2 críticas, 32 altas, 60 moderadas y 21 bajas. Esta incidencia debe permanecer abierta hasta su tratamiento y registro de riesgo residual.

Además, la revisión detectó un `.env.thingsdata` versionado. La documentación del propio proyecto indica que las credenciales reales deben manejarse fuera del repositorio. Debe eliminarse del árbol actual, revisar el historial y rotar secretos si el fichero contiene valores sensibles.

### CI

No debe marcarse `GREEN` únicamente porque existan workflows. El estado real debe probar que los jobs han sido ejecutados por un runner válido y que los checks aportan evidencia reproducible.

## 5. Criterio de cierre del proyecto

CASTÚO-SYSTEM solo se considerará “completado para promoción” cuando:

1. El repositorio sea limpio de secretos y artefactos sensibles.
2. Seguridad y dependencias tengan evidencia de revisión y cierre/residual-risk.
3. CI produzca checks reales y reproducibles.
4. Runtime e infraestructura objetivo estén demostrados.
5. La documentación refleje exactamente el estado verificable.
6. Los claims comerciales y de producción estén respaldados por evidencia independiente.

## 6. Política de lenguaje externo

Hasta cerrar G1–G7, utilizar: `staging`, `pilot-ready`, `evidence-scoped`, `TRL en validación` o equivalente respaldado por evidencia. Evitar `production ready`, `TRL9`, `certificado` o equivalentes salvo evidencia específica y actual.
