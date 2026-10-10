# Cast-o — Distribución de Assurance acotada

Cast-o es la superficie técnica de assurance y validación negativa de CASTÚO-SYSTEM. Ejecuta pruebas acotadas y produce evidencia reproducible; **no es un servicio de certificación**.

## Posición en el ecosistema

`Cast-o` valida alcances declarados. `castuo-evidence` posee los contratos de evidencia portable, `Castuo-system` posee la integración y la gobernanza, y `castuo-evolution` posee la política de promoción. Son autoridades enlazadas, no copias unas de otras.

## Demo offline reproducible

Requisito: Node.js 18 o superior.

```bash
npm install
npm run demo:offline
```

El comando ejecuta un fixture congelado `SIMULATION_ONLY` y escribe:

```text
artifacts/bounded-assurance/offline-demo/evidence-pack.json
```

Salida esperada:

```text
FIELD OPERATION COMPLETED
LOSS OF CONNECTIVITY ........ PASS
LOCAL BUFFER ................ PASS
RECOVERY .................... PASS
SYNC ......................... PASS
EVIDENCE HASH ............... PASS
REPLAY ....................... PASS
CLAIM BOUNDARY ............... SIMULATION_ONLY
PROMOTION .................... BLOCKED
```

El artefacto contiene el ID de operación, eventos, intervalos de conectividad, recuperación, sincronización, hash de integridad, resultado de replay, estado final y efecto de promoción. Es una simulación acotada y no debe presentarse como evidencia de campo, staging o producción.

## Validación

```bash
npm test
npm run validate:package
npm run demo:offline
```

Un PASS local significa `VALIDATED_LOCAL` únicamente para el alcance declarado. El replay independiente, CI remoto, evidencia de campo, operación productiva y certificación son gates separados.

## Límite de gobernanza

El contrato mínimo de fallo es:

```text
solicitud denegada → registrada → explicable → recuperable
```

La promoción permanece fail-closed cuando falta evidencia de provenance, pruebas negativas, replay, seguridad, revisión o rollback.

## Licencia

AGPL-3.0.
