# RUNBOOK GO-LIVE PR19

Fecha base: 2026-04-02
Alcance: PR #19 (`feat: validar_lote completo + K8s Hetzner + seguridad + CI/CD`)
Objetivo: activar produccion en Hetzner con trazabilidad tecnica y criterio Go/No-Go auditable.

## 1. Roles y responsabilidades

- Release Lead: coordina ventanas, decide Go/No-Go.
- DevOps: ejecuta workflows y validacion de cluster.
- Backend Owner: valida endpoints y contratos API.
- Seguridad/Cumplimiento: valida secretos, permisos y evidencias.

## 2. Precondiciones (T-60 a T-30)

### 2.0 Bloqueantes Go/No-Go

Debe quedar todo en verde antes de declarar `GO`:

| Bloqueante | Estado esperado | Accion requerida |
|---|---|---|
| Secrets en GitHub | Configurados | Cargar 6 secretos criticos |
| Permisos GitHub Actions | Read and write | Ajustar en Settings > Actions |
| Workflows criticos | Ejecutados al menos 1 vez | Lanzar y validar runs reales |
| Cambios locales no consolidados | Controlados | Consolidar alcance antes de merge |
| DNS/TLS | Activo | Confirmar `castuo-system.cloud`, `api.castuo-system.cloud`, `n8n.castuo-system.cloud`, `www.castuo-system.cloud` |
| GaiaChain real | Credenciales presentes | Configurar `GAIACHAIN_PRIVATE_KEY` |

### 2.1 GitHub Actions

Verificar en repository settings:

- Actions permissions: Read and write.
- Secrets presentes:
  - `HETZNER_KUBECONFIG`
  - `JWT_SECRET_KEY`
  - `GAIACHAIN_PRIVATE_KEY`
  - `DB_PASSWORD`
  - `REGISTRY_USER`
  - `REGISTRY_PASSWORD`

Comandos de apoyo:

```bash
gh secret list
gh pr view 19 --json state,mergeStateStatus,reviewDecision,headRefName,baseRefName
```

Evidencia:

- Captura de pantalla de settings/secrets (sin mostrar valores).

### 2.2 Estado de rama y PR

Comandos:

```bash
git fetch origin
git status
git rev-parse --abbrev-ref HEAD
gh pr view 19 --json state,mergeStateStatus,reviewDecision,headRefName,baseRefName
```

Criterio:

- Rama correcta: `feat/excelencia-operativa`.
- PR abierto y mergeable.
- Sin conflictos.

Evidencia:

- Salida de comandos guardada en `logs/go-live-pr19/00-pr-status.txt`.

### 2.3 Validacion local minima

Comandos:

```bash
pytest -q tests/test_api.py -k "validar_lote or metrics or predict"
```

Criterio:

- Exito 100% en subset critico.

Evidencia:

- Guardar salida en `logs/go-live-pr19/01-local-tests.txt`.

## 3. Ventana de ejecucion (T-30 a T+20)

### 3.1 Disparo de workflows

Ejecutar en este orden:

```bash
gh workflow run deploy-staging.yml --ref feat/excelencia-operativa
gh workflow run e2e-smoke-traces.yml --ref feat/excelencia-operativa
gh workflow run deploy-to-hetzner.yml --ref feat/excelencia-operativa
```

Monitorizacion:

```bash
gh run list --limit 20
gh run watch
```

Criterio:

- `deploy-staging.yml`: success
- `e2e-smoke-traces.yml`: success
- `deploy-to-hetzner.yml`: success

Evidencia:

- IDs y URLs de runs en `logs/go-live-pr19/02-workflow-runs.txt`.

### 3.2 Verificacion de cluster

Comandos:

```bash
kubectl get pods -n castuo-system
kubectl get svc -n castuo-system
kubectl get ingress -n castuo-system
kubectl get hpa -n castuo-system
kubectl rollout status deployment/castuo-api -n castuo-system --timeout=180s
```

Criterio:

- Pods `Running`/`Ready`.
- Ingress activo con host esperado.
- HPA aplicado.
- Rollout completado.

Evidencia:

- Salida en `logs/go-live-pr19/03-k8s-status.txt`.

### 3.2.1 DNS + Ingress (flujo operativo en 5 pasos)

Paso 1. Conectar `kubectl` al cluster Hetzner real:

```bash
# Ejemplo: sustituir castuo-prod por el nombre real del cluster
hcloud kubeconfig create castuo-prod --output kubeconfig.yaml
export KUBECONFIG=$(pwd)/kubeconfig.yaml
kubectl cluster-info
kubectl get nodes -n castuo-system
```

Paso 2. Obtener direccion del Ingress:

```bash
kubectl get ingress -n castuo-system -o wide
```

Registrar la `ADDRESS` (IP o hostname del LB) para el paso DNS.

Paso 3. Configurar DNS en el proveedor (TTL recomendado: 300):

- `castuo-system.cloud` -> `A/AAAA` a la IP del Ingress.
- `api.castuo-system.cloud` -> `A/AAAA` a la IP del Ingress.
- `n8n.castuo-system.cloud` -> `A/AAAA` a la IP del Ingress.
- `www.castuo-system.cloud` -> `A/AAAA` a la IP del Ingress.

Paso 4. Aplicar/validar Ingress con los 4 hosts:

```bash
kubectl apply -f k8s/ingress.yaml
kubectl describe ingress -n castuo-system castuo-ingress
```

Nota tecnica importante:

- En este repo el Ingress enruta a `Service` internos (`castuo-api-service`, `castuo-n8n-service`).
- El puerto en Ingress debe ser el `port` del Service (80), no el `targetPort` del Pod (8000/5678).

Frontend raiz dedicado (opcional):

```bash
kubectl apply -f k8s/frontend-service.yaml
```

Si se despliega frontend dedicado, actualizar `k8s/ingress.yaml` en hosts `castuo-system.cloud` y `www.castuo-system.cloud` para usar `castuo-frontend-service:80`.

Paso 5. Validar DNS, HTTP/HTTPS y TLS:

```bash
# DNS
nslookup api.castuo-system.cloud
dig castuo-system.cloud +short

# Redirect HTTP -> HTTPS y salud
curl -I http://api.castuo-system.cloud/health
curl -I https://api.castuo-system.cloud/health

# Certificados
kubectl describe certificate -n castuo-system castuo-tls
kubectl get challenge -A

# Evidencia de certificado externo
openssl s_client -connect api.castuo-system.cloud:443 -servername api.castuo-system.cloud | openssl x509 -noout -dates
```

Criterio de exito:

- DNS resuelve todos los dominios al mismo Ingress.
- HTTP responde `301` a HTTPS.
- HTTPS responde `200` en `/health`.
- Certificado en estado `Ready`.

### 3.3 Verificacion funcional API

Comandos:

```bash
curl -i https://api.castuo-system.cloud/health
curl -i https://api.castuo-system.cloud/metrics
```

Criterio:

- HTTP 200 en ambos.

Evidencia:

- Salida en `logs/go-live-pr19/04-health-metrics.txt`.

### 3.4 Verificacion de endpoints criticos

#### A) TRACES smoke

```bash
curl -s -X POST https://api.castuo-system.cloud/api/v1/traces/certificado \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/traces-sample.json | jq
```

Criterio:

- Campo `estado` contiene `Compliant`.
- Aviso legal presente.

#### B) validar_lote

1) Opcion recomendada: login contra la API real.

Ruta real de autenticacion actual: `POST /api/v1/auth/login`

Contrato real actual:

```json
{
  "user_id": "go-live-check",
  "tenant_id": "default",
  "role": "tecnico"
}
```

Comando:

```bash
export JWT_TOKEN=$(curl -s -X POST https://api.castuo-system.cloud/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"go-live-check","tenant_id":"default","role":"tecnico"}' | jq -r '.token')
```

2) Opcion alternativa: generar JWT temporal offline si conoces `JWT_SECRET_KEY`.

```bash
python3 - <<'PY'
import jwt
from datetime import datetime, timedelta, timezone
payload = {
    "sub": "go-live-check",
    "roles": ["tecnico"],
    "exp": int((datetime.now(timezone.utc) + timedelta(minutes=20)).timestamp())
}
print(jwt.encode(payload, "${JWT_SECRET_KEY}", algorithm="HS256"))
PY
```

3) Ejecutar endpoint real.

Ruta real actual: `POST /api/v1/skills/validar_lote`

Contrato minimo real actual:

```json
{
  "lote_id": "GO-LIVE-PR19",
  "metadatos": {
    "humedad": 61.2,
    "thc": 0.15,
    "ubicacion": "test"
  },
  "firma_digital": "<TOKEN>"
}
```

```bash
curl -s -X POST https://api.castuo-system.cloud/api/v1/skills/validar_lote \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "lote_id": "GO-LIVE-PR19",
    "metadatos": {"humedad": 61.2, "thc": 0.15, "ubicacion": "test"},
    "firma_digital": "<TOKEN>"
  }' | jq
```

Criterio:

- `status` = `OK`
- Respuesta incluye `tx_hash`, `qr_path`, `certificado_path`

Nota operativa:

- El sistema actual devuelve rutas de fichero (`qr_path`, `certificado_path`), no URLs publicas de storage.

Evidencia:

- Salida en `logs/go-live-pr19/05-endpoints.txt`.

## 4. Criterio Go/No-Go (T+20)

### GO

- Workflows criticos en `success`.
- Cluster estable y rollout completado.
- `/health` y `/metrics` en 200.
- Smoke TRACES OK.
- validar_lote OK.

### NO-GO

- Cualquier workflow critico `failed`.
- Rollout incompleto o pods no estables.
- Fallo de endpoints de salud/funcionales.

## 5. Plan de rollback (si No-Go)

1. Revertir a imagen estable previa:

```bash
kubectl -n castuo-system rollout undo deployment/castuo-api
kubectl -n castuo-system rollout status deployment/castuo-api --timeout=180s
```

2. Verificar salud tras rollback:

```bash
curl -i https://api.castuo-system.cloud/health
```

3. Registrar incidente:

- `logs/go-live-pr19/rollback.txt`
- Crear issue postmortem con causa raiz y acciones preventivas.

## 6. Cierre de activacion (T+30)

Comandos:

```bash
gh pr comment 19 --body "Go-live PR19 ejecutado. Ver evidencias en logs/go-live-pr19/*.txt"
```

Checklist final:

- [ ] Evidencias archivadas
- [ ] Estado final comunicado al equipo
- [ ] Riesgos residuales documentados
- [ ] Monitoreo reforzado 60 min

## 7. Riesgos residuales conocidos

- Dependencia de GaiaChain y conectividad externa para transaccion real.
- Riesgo de drift de imagen si el workflow aplica deployment con tag fijo tras set-image.
- Cambios pendientes en rama deben consolidarse antes de merge definitivo a `main`.
