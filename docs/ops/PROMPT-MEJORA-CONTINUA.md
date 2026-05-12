# Prompt Maestro de Mejora Continua (CASTUO-SYSTEM)

## Objetivo
Ejecutar un ciclo integral de mejora continua sin romper regresiones, cubriendo: calidad de codigo, tipado estatico, tests, workflows, seguridad y consistencia de datos.

## Prompt listo para usar
Copia y pega este bloque en tu agente:

Actua como arquitecto tecnico y SRE de CASTUO-SYSTEM. Ejecuta el ciclo completo de mejora continua en etapas, sin romper compatibilidad:

1) Diagnostico
- Lista cambios no confirmados.
- Ejecuta tests y reporta fallos por severidad.
- Valida workflows de GitHub Actions (sintaxis y seguridad de expresiones).
- Revisa errores de tipado estatico.

2) Correccion
- Arregla primero errores bloqueantes de runtime/tests.
- Arregla despues workflows inseguros o fragiles.
- Limpia avisos de tipado estatico en modulos tocados, sin cambiar comportamiento funcional.
- No introducir secretos hardcodeados ni credenciales de ejemplo reutilizables.

3) Validacion
- Reejecuta test suite completa.
- Revalida workflows.
- Revalida errores estaticos en archivos modificados.
- Entrega evidencias concretas (estado final de tests, workflows y tipado).

4) Cierre
- Resume cambios por archivo y riesgo residual.
- Propone siguientes 3 mejoras priorizadas por impacto/tiempo.
- Sugiere mensaje de commit estilo conventional commits (feat/fix/refactor).

Reglas:
- Mantener APIs publicas y contratos existentes salvo que haya bug critico.
- Preservar seguridad: JWT/OAuth2, cifrado, principio de minimo privilegio, sin secretos en repo.
- Cambios pequenos y verificables por etapa.

## Checklist operacional rapido
- Tests: /workspaces/Castuo-system/.venv/bin/python -m pytest -q
- Workflows: actionlint
- Tipado estatico: get_errors en archivos modificados
- Seguridad minima: sin claves en codigo, sin interpolar inputs no confiables en scripts CI

## Criterio de exito
- Tests en verde
- Workflows sin hallazgos criticos
- Errores estaticos bloqueantes resueltos en archivos tocados
- Evidencia de cambios y plan siguiente priorizado
