# Runbook de reproducción y firma independiente de S-001A

Este procedimiento debe ejecutarse por una persona distinta del autor del paquete y en un entorno controlado por esa persona. La firma del manifest prueba integridad y autenticidad del paquete; la attestation del revisor prueba que la reproducción fue realizada por una autoridad independiente. Ninguna de las dos, por separado, cambia automáticamente el gate.

## 0. Precondiciones

El revisor debe recibir por canales separados:

| Artefacto | Origen requerido |
|---|---|
| Repositorio y commit congelado | GitHub / owner del paquete |
| Certificado público de raíz | Trust authority, fuera de GitHub |
| Fingerprint esperado de la raíz | Trust authority, canal fuera de banda |
| Certificado público del signer | Trust authority |
| Firma detached del manifest | Signing authority |
| Manifest canónico | Owner del paquete |
| SBOM y hashes auxiliares | Owner del paquete |
| Identidad y clave del revisor | Organización del revisor, HSM o almacén protegido |

No se deben solicitar ni copiar claves privadas del owner o de la autoridad firmante.

## 1. Obtener el commit congelado

```bash
set -euo pipefail
umask 077

WORK="$HOME/castuo-review-s001a-$(date -u +%Y%m%dT%H%M%SZ)"
git clone https://github.com/Traky12/Castuo-system.git "$WORK/repo"
cd "$WORK/repo"
git fetch --tags origin

git checkout --detach 2106b27
git rev-parse HEAD
```

El revisor debe confirmar que el commit coincide con el commit comunicado por el owner. Si no coincide, detenerse con `BLOCK`.

## 2. Comprobar que no hay cambios locales

```bash
git status --porcelain

test -z "$(git status --porcelain)" || {
  echo "BLOCK: working tree is not clean"
  exit 1
}
```

## 3. Validar sintaxis, manifest y scripts

```bash
python3 -m json.tool \
  governance/evidence/E3-001-S001A/package-closure-manifest-2026-08-20.json \
  > /dev/null

python3 -m json.tool \
  governance/evidence/E3-001-S001A/security-gate-decision.json \
  > /dev/null

python3 -m json.tool \
  governance/evidence/E3-001-S001A/gate-state.json \
  > /dev/null

python3 -m compileall -q scripts/assurance
find scripts/assurance -type d -name __pycache__ -prune -exec rm -rf {} +
```

## 4. Reproducir S-001A

```bash
python3 governance/evidence/E3-001-S001A/scripts/replay_s001a.py \
  --fixture governance/evidence/E3-001-S001A/fixtures/S-001A-frozen-fixture.json \
  --output "$WORK/local-replay.json" \
  | tee "$WORK/replay.stdout"

python3 scripts/assurance/foreign_verify_s001a.py \
  governance/evidence/E3-001-S001A/fixtures/S-001A-frozen-fixture.json \
  governance/evidence/E3-001-S001A/replay-result.json \
  | tee "$WORK/foreign-verification.stdout"
```

El resultado esperado es `PASS_LOCAL_NO_CLAIM` para el replay y `PASS_FOREIGN_SEMANTIC_REPLAY` para la verificación semántica. El scope debe permanecer `S-001A`.

## 5. Ejecutar pruebas negativas

```bash
python3 scripts/assurance/run_negative_security_cases.py \
  | tee "$WORK/negative-security-tests.stdout"
```

Cada caso debe observar `BLOCK`: manifest alterado, estado desconocido, expansión de scope y fallo de replay. Cualquier `ALLOW`, `PROMOTE` o caso no ejecutado es un bloqueo.

## 6. Verificar la raíz y la firma del manifest

El revisor debe copiar los siguientes artefactos desde la autoridad correspondiente a un directorio protegido que no se versionará:

```text
$WORK/trust/root-ca.cert.pem
$WORK/trust/root-ca.cert.sha256
$WORK/trust/staging-signer.cert.pem
$WORK/trust/evidence-manifest.sig
```

No se debe generar una raíz temporal para esta verificación. La raíz aprobada debe llegar por el canal de trust authority.

```bash
ROOT_CERT="$WORK/trust/root-ca.cert.pem"
SIGNER_CERT="$WORK/trust/staging-signer.cert.pem"
SIGNATURE="$WORK/trust/evidence-manifest.sig"
MANIFEST="governance/evidence/E3-001-S001A/package-closure-manifest-2026-08-20.json"
EXPECTED_ROOT_FP=$(tr -d '[:space:]' < "$WORK/trust/root-ca.cert.sha256")

openssl x509 -in "$ROOT_CERT" -outform DER \
  | sha256sum | awk '{print toupper($1)}'

scripts/assurance/verify_signed_manifest.sh \
  --manifest "$MANIFEST" \
  --signature "$SIGNATURE" \
  --signer-cert "$SIGNER_CERT" \
  --root-cert "$ROOT_CERT" \
  --expected-root-fingerprint "$EXPECTED_ROOT_FP"
```

El único resultado aceptable es `PASS: trust root, signer chain and manifest signature verified`. La autoridad de confianza debe comprobar además vigencia, revocación, propósito del certificado y que el fingerprint fue aprobado fuera de banda.

## 7. Ejecutar rollback en entorno propio autorizado

El revisor no debe declarar rollback operacional basándose sólo en el simulador local del owner. Si dispone de una ventana de staging aprobada, debe crear su propio registro de autorización:

```bash
cat > "$WORK/staging-authorization.json" <<'EOF'
{
  "authorized": true,
  "environment": "staging",
  "scope": "S-001A",
  "remote_side_effects": false,
  "owner": "REPLACE_WITH_OPERATIONS_OWNER",
  "window_id": "REPLACE_WITH_APPROVED_CHANGE_WINDOW"
}
EOF
```

Después debe ejecutar el simulador o runbook operacional aprobado, conservar logs, hashes pre/post, estado restaurado, evidencia preservada, tiempos de detección/recuperación y retest. Para un simulacro puramente local:

```bash
python3 scripts/assurance/simulate_authorized_rollback.py \
  --sandbox "$WORK/staging-sandbox" \
  --authorization-file "$WORK/staging-authorization.json" \
  --environment staging \
  --fault corrupt-evidence \
  --output "$WORK/authorized-staging-rollback.json"
```

El resultado esperado es `PASS_STAGING_NO_PRODUCTION_CLAIM`. Esto demuestra el procedimiento del simulador, pero sólo el owner operacional puede decidir si constituye evidencia suficiente de rollback representativo.

## 8. Crear el registro de revisión independiente

El revisor debe completar una copia del registro sin cambiar el fixture ni el script:

```bash
cp governance/evidence/E3-001-S001A/independent-review/review-record.yaml \
  "$WORK/review-record.yaml"
```

Debe rellenar identidad, organización, conflicto de interés, fecha, commit, comandos, hashes, resultados, desviaciones, limitaciones y recomendación. Un registro mínimo aprobado debe incluir:

```yaml
reviewer:
  reviewer_id: REPLACE_WITH_REAL_REVIEWER_ID
  organization: REPLACE_WITH_ORGANIZATION
  independence: CONFIRMED
  conflict_check: CLEAR
execution:
  package_commit: 2106b27
  observed_decision: APPROVED_WITHIN_DECLARED_SCOPE
  observed_status: PASS_LOCAL_NO_CLAIM
  evidence_hashes_verified: true
  negative_tests_reproduced: true
  rollback_reproduced: true
review:
  review_date: REPLACE_WITH_UTC_DATE
  limitations_acknowledged: true
  recommendation: APPROVED_WITHIN_DECLARED_SCOPE
promotion_impact:
  one_r: true
  one_a: false
  gate_status: REVIEW_READY_NOT_PROMOTED
  claim: LOCAL_RESULT_NO_CLAIM
```

No se debe marcar `one_r: true` hasta completar realmente la reproducción.

## 9. Firmar la attestation del revisor

La clave privada debe estar en el HSM o almacén protegido del revisor. No se debe crear una clave desechable para simular independencia.

```bash
openssl dgst -sha256 \
  -sign "$REVIEWER_PRIVATE_KEY" \
  -out "$WORK/review-record.yaml.sig" \
  "$WORK/review-record.yaml"

openssl x509 -in "$REVIEWER_CERT" -pubkey -noout \
  > "$WORK/reviewer-public-key.pem"

openssl dgst -sha256 \
  -verify "$WORK/reviewer-public-key.pem" \
  -signature "$WORK/review-record.yaml.sig" \
  "$WORK/review-record.yaml"
```

La organización debe conservar el certificado o identidad pública del revisor, el fingerprint, el método de revocación y la relación entre el revisor y la decisión. La firma se adjunta como attestation, no como sustituto de la decisión del gate.

## 10. Entregar el paquete al gate authority

```bash
sha256sum \
  "$WORK/review-record.yaml" \
  "$WORK/review-record.yaml.sig" \
  "$WORK/foreign-verification.stdout" \
  "$WORK/negative-security-tests.stdout" \
  "$WORK/authorized-staging-rollback.json" \
  > "$WORK/reviewer-artifact-hashes.sha256"
```

El gate authority debe comprobar que el commit, manifest, firma, reviewer attestation y rollback pertenecen al mismo scope y versión. Sólo después puede actualizar los estados binarios. El revisor no debe cambiar directamente `gate-state.json` para forzar `PROMOTE`.

## Criterio final

El estado puede cambiar a `PROMOTE` sólo si la organización confirma simultáneamente:

```text
capability
∧ evidence
∧ replay
∧ security
∧ sovereignty
∧ resilience
∧ independent_review
∧ rollback_verified
```

Una firma local válida, un reviewer record sin attestation, un rollback simulado o un check de CI en verde por sí solos no satisfacen el predicado.
