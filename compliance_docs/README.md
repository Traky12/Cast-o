# Documentación de Cumplimiento – CASTÚO-SYSTEM™

Generación automatizada de documentación normativa (GDPR, Ley 3/2023 / equivalente regional, AI Act, ISO 27001, SIGPAC/SIGIF, contratos con propietarios forestales y checklists de auditoría).

## Estructura

```
compliance_docs/
├── templates/          # Plantillas Jinja2 (Markdown)
│   ├── gdpr_register_template.md
│   ├── ai_act_assessment_template.md
│   ├── ley3_compliance_template.md
│   ├── iso27001_declaration_template.md
│   ├── compliance_report_template.md
│   ├── sigpac_procedure_template.md
│   ├── forest_owner_contract_template.md
│   └── audit_checklist_template.md
├── scripts/
│   └── generate_compliance_docs.py
├── generated/          # Salida generada (no versionar datos sensibles)
└── README.md
```

## Requisitos

- Python 3.8+
- Jinja2: `pip install jinja2`

## Uso

### Generar toda la documentación (región por defecto: Extremadura)

```bash
cd compliance_docs
python scripts/generate_compliance_docs.py
```

### Especificar región y/o ID de media

```bash
# Extremadura (por defecto) con media_id por defecto
python scripts/generate_compliance_docs.py

# Extremadura con informe para un vídeo concreto
python scripts/generate_compliance_docs.py extremadura sd-eu-20260316-12345-67890

# Andalucía
python scripts/generate_compliance_docs.py andalucia sd-eu-20260316-12345-67890

# Portugal
python scripts/generate_compliance_docs.py portugal sd-eu-20260316-12345-67890
```

### Parámetros

1. **region** (opcional): `extremadura` | `andalucia` | `portugal`. Por defecto: `extremadura`.
2. **media_id** (opcional): Identificador del media para el informe de cumplimiento. Por defecto: `sd-eu-20260315-12345-67890`.

## Documentos generados

| Archivo | Descripción |
|---------|-------------|
| `02.01.01_Registro_Actividades_Tratamiento.md` | Registro de actividades de tratamiento (GDPR Art. 30) |
| `02.02.03_Gestion_Consentimientos_*_*.md` | Cumplimiento Ley 3/2023 (o Ley 2/2021 Andalucía / Decreto-Lei 96/2019 Portugal) |
| `02.03.03_AI_Act_Self-Assessment.md` | Self-assessment AI Act |
| `02.04.01_Declaracion_Aplicabilidad_ISO27001.md` | Declaración de aplicabilidad ISO 27001 |
| `02.05.01_Procedimiento_SIGPAC_*.md` | Procedimiento de validación con SIGPAC/SIGIF |
| `04.03.01_Contrato_Propietario_Forestal_*.md` | Contrato tipo con propietario forestal (ES/PT) |
| `06.01.01_Checklist_Auditoria_Monthly_*.md` | Checklist de auditoría mensual |
| `06.01.01_Checklist_Auditoria_Quarterly_*.md` | Checklist de auditoría trimestral |
| `compliance_report_<media_id>.md` | Informe de cumplimiento por media |

## Integración con el resto del proyecto

- **Complementariedad**: `backend/scripts/generate_compliance_report.py` genera informes técnicos por `media_id` (auditores técnicos). Este generador produce documentación normativa para AEPD, Junta de Extremadura/Andalucía, ICNF, certificadoras ISO 27001.
- **Evidencias compartidas**: Mismos logs (Wazuh), transacciones GaiaChain y metadatos de compliance.

## Entrega a auditores

- **Junta de Extremadura**: `02.02.03_*_Ley_3_2023_Extremadura.md`, `02.05.01_Procedimiento_SIGPAC_Extremadura.md`.
- **AEPD**: `02.01.01_Registro_Actividades_Tratamiento.md`.
- **Certificadora ISO 27001**: `02.04.01_Declaracion_Aplicabilidad_ISO27001.md`.
- **Propietarios forestales**: `04.03.01_Contrato_Propietario_Forestal_*.md`.

## Variables de entorno

- `ENVIRONMENT`: `production` (por defecto) o `development`; se refleja en los documentos generados.
