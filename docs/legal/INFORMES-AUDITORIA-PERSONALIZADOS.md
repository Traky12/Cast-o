# Informes de auditoría personalizados (plantillas, sin métricas inventadas)

**Impacto territorial:** el informe solo tiene valor si los `events` y `water_usage` reflejan **mediciones y expediente reales**; la plantilla no sustituye trámites AEMPS ni CTAEX.

## Artefactos

| Pieza | Ruta |
|-------|------|
| Plantilla JSON (Jinja2) | `templates/reports/aemps_audit.jinja2` |
| Generador | `backend/reports/audit_generator.py` |

## Uso

```python
from backend.reports.audit_generator import AuditReportGenerator

gen = AuditReportGenerator()
gen.generate_aemps_report(
    {
        "batch_id": "...",
        "parcel_id": "...",
        "crop_type": "...",
        "events": [...],
        "water_usage": {"total_liters": 0, "savings_percent": 0},
        "compliance_status": "pending_review",
        "compliance_issues": [],
    },
    "exports/aemps_audit_batch.json",
    token_id=1,
)
```

## GaiaChain (opcional)

Tras escribir el JSON se puede registrar en cadena pasando **`token_id=`** (`int` o `str` numérico, **≥ 1**, `tokenId` del contrato) o definiendo **`CASTUO_AUDIT_REPORT_TOKEN_ID`**. Valores inválidos se rechazan con log `error` y no se llama a la cadena. Se usa `register_event_in_chain` con **un dict** (`action`: `aemps_audit_report_generated`). Fallos de RPC/clave quedan en log `error`; el fichero generado sigue siendo la evidencia primaria.

El informe incluye **`normative_notice`** en la raíz del JSON: las referencias normativas son **documentales**, no certificación.

**Relación:** [PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md) · [SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md](./SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md)
