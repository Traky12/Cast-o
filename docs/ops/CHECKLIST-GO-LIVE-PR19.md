# CHECKLIST GO-LIVE PR19

> **Estado documental histórico — no constituye evidencia vigente de TRL 9, certificación, validación externa, producción ni conformidad.**
>
> Este documento refleja una hipótesis, sesión de trabajo, propuesta o estado interno histórico. El estado técnico actual de CASTÚO y sus limitaciones se rige por el README vigente, el registro de capacidades, los resultados de tests y los evidence packs verificables.
>
> Cualquier afirmación de madurez, operatividad, certificación, validación o preparación productiva debe considerarse pendiente de evidencia específica y revisión independiente.
>
> `document_status: historical` · `technical_maturity_claim: not_current` · `trl_claim: not_verified` · `certification_claim: not_verified` · `external_validation: not_verified` · `production_status: not_claimed` · `superseded_by: README.md` · `review_required: true` — índice: [`docs/HISTORICAL-CLAIMS-INDEX.md`](../HISTORICAL-CLAIMS-INDEX.md)


## 1. Preflight

```bash
gh secret list
gh pr view 19 --json state,mergeStateStatus,reviewDecision,headRefName,baseRefName
git status
pytest -q tests/test_api.py -k "validar_lote or metrics or predict"
```

## 2. Lanzar workflows

```bash
gh workflow run deploy-staging.yml --ref feat/excelencia-operativa
gh workflow run e2e-smoke-traces.yml --ref feat/excelencia-operativa
gh workflow run deploy-to-hetzner.yml --ref feat/excelencia-operativa
gh run list --limit 10
gh run watch
```

## 3. Verificar cluster

```bash
kubectl get pods -n castuo-system
kubectl get svc -n castuo-system
kubectl get ingress -n castuo-system
kubectl get hpa -n castuo-system
kubectl rollout status deployment/castuo-api -n castuo-system --timeout=180s
```

## 4. Verificar endpoints

```bash
curl -i https://api.castuo-system.cloud/health
curl -i https://api.castuo-system.cloud/metrics
```

## 5. Login real

```bash
export JWT_TOKEN=$(curl -s -X POST https://api.castuo-system.cloud/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"go-live-check","tenant_id":"default","role":"tecnico"}' | jq -r '.token')
```

## 6. validar_lote real

```bash
curl -s -X POST https://api.castuo-system.cloud/api/v1/skills/validar_lote \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "lote_id": "GO-LIVE-PR19",
    "metadatos": {"humedad": 61.2, "thc": 0.15, "ubicacion": "test"},
    "firma_digital": "'"${JWT_TOKEN}"'"
  }' | jq
```

## 7. TRACES smoke

```bash
curl -s -X POST https://api.castuo-system.cloud/api/v1/traces/certificado \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/traces-sample.json | jq
```

## 8. Go / No-Go

GO si:

- workflows en success
- cluster Ready
- /health y /metrics en 200
- validar_lote OK
- TRACES OK

NO-GO si falla cualquiera de los anteriores.