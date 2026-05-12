# Cumplimiento RGPD — materiales ejecutables (CASTÚO-SYSTEM)

No es asesoría legal. Adaptar a tu responsable, DPO y políticas.

## 1. Anonimización / pseudonimización

```bash
pip install -r scripts/compliance/GDPR/requirements.txt
python scripts/compliance/GDPR/data_anonymization.py --input data/raw_queries.json --output data/anonymized_queries.json
python scripts/compliance/GDPR/data_anonymization.py --input data/raw.json --output data/out.json --salt "mi_salt_interna"
python scripts/compliance/GDPR/data_anonymization.py --input data/raw.json --output data/out.json --synthetic-names
```

## 2. Auditoría básica (post-proceso)

```bash
python scripts/compliance/GDPR/audit_gdpr.py --dataset data/anonymized_queries.json
```

## 3. Plantillas

| Archivo | Uso |
|---------|-----|
| `consent_template.html` | Integrar en frontend; registrar versión y timestamp en backend. |
| `treatment_register.md` | Registro Art. 30 (mantener vivo). |
| `dpia_template.md` | EIPD antes de despliegues de riesgo elevado. |

## 4. Tests

```bash
pytest scripts/compliance/GDPR/tests/test_anonymization.py -v
```

## 5. LoRA / IA

`scripts/ai/mistral_lora/README.md` — entrenar solo con base legal clara y datos minimizados.

## 6. Copia en `docs/`

Resumen orientativo: `docs/compliance/GDPR/README.md`.
