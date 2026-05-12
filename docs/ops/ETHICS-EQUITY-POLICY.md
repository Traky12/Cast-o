# Politica Operativa de Etica y Equidad

Fecha: 2026-04-03
Ambito: API, integraciones IA y contenido educativo

## Objetivo
Garantizar que el sistema opere con criterios de etica, equidad y no discriminacion,
evitando respuestas o flujos que promuevan exclusiones contra grupos protegidos.

## Principios
- No discriminacion por sexo, etnia, origen, religion, discapacidad o condicion social.
- Transparencia y trazabilidad en decisiones automatizadas.
- Seguridad por defecto: integraciones externas deshabilitadas en produccion salvo habilitacion explicita.
- Supervisión humana en operaciones criticas.

## Controles tecnicos activos
- Guard de etica/equidad en texto de entrada para:
  - /api/v1/claude/generate
  - /api/v1/mistral/analyze
  - /api/v1/education/validate
  - /api/v1/education/publish
- Bloqueo con HTTP 422 cuando el texto contiene patrones de exclusion/discriminacion a grupos protegidos.
- Integraciones externas con kill-switch en produccion:
  - ENABLE_TRACES_SUBMIT
  - ENABLE_CLAUDE_INTEGRATION
  - ENABLE_MISTRAL_INTEGRATION

## Requisitos de operacion en produccion
- Definir ENV=production.
- Mantener integraciones externas en OFF por defecto.
- Activar una integracion solo con aprobacion tecnica/compliance y evidencia de necesidad.
- Registrar cambios de flags en auditoria de despliegue.

## Criterio de rechazo
Se bloquea cualquier solicitud que:
- Promueva exclusion de grupos protegidos.
- Solicite odio o violencia contra colectivos.
- Intente automatizar reglas de acceso discriminatorias.

## Revision
- Revision mensual tecnica.
- Revision trimestral legal/compliance.