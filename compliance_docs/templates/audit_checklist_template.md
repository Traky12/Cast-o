# **🔍 {{ checklist.name }} ({{ region|capitalize }})**
**Fecha**: {{ generated_at[:10] }}
**Versión**: 1.0
**Responsable**: {{ system.dpo.name }}

---
## **📌 INSTRUCCIONES**
1. **Frecuencia**: {{ "Mensual" if "Mensual" in checklist.name else "Trimestral" }}.
2. **Metodología**: Revisar cada ítem y marcar ✅ si cumple o ❌ si no cumple. Registrar evidencias en la columna correspondiente.
3. **Registro**: Guardar este documento en `compliance_docs/generated/`. Notificar al DPO cualquier incumplimiento en <24h.

---
## **📌 ITEMS A AUDITAR**

| **ID**   | **Descripción**                                                                 | **Cumple (✅/❌)** | **Evidencia**                                                                 | **Normativa Aplicable**                     |
|----------|----------------------------------------------------------------------------------|-------------------|-------------------------------------------------------------------------------|---------------------------------------------|
{% for item in checklist['items'] %}
| {{ item.id }} | {{ item.description }}                                                          |                    | {{ item.evidence|join(", ") }}                                                | {{ item.compliance|join(", ") }}             |
{% endfor %}

---
## **📌 PROCEDIMIENTO DE REVISIÓN**
1. **Recopilación de Evidencias**:
   - Ejecutar scripts de auditoría (ej: `python backend/scripts/audit_consents.py --since 30d`).
   - Consultar logs en Wazuh: dashboard de auditoría.

2. **Registro de Resultados**: Actualizar esta plantilla con los resultados. Firmar y guardar en `compliance_docs/generated/`.

3. **Acciones Correctivas**: Para ítems ❌: abrir incidencia, asignar responsable y plazo (máx. 7 días para críticos). Registrar la acción en la próxima auditoría.

---
## **📌 RESPONSABLES**
| **Rol**               | **Nombre**               | **Email**                     |
|-----------------------|--------------------------|-------------------------------|
| Delegado de Protección de Datos | {{ system.dpo.name }}   | {{ system.dpo.email }}        |
| Responsable Técnico   | Carlos Martínez          | cto@castuo-system.eu         |
| Auditor Interno       | Ana López                | audit@castuo-system.eu       |

---
**Firma del Auditor**:
_________________________
[Nombre del Auditor]
{{ generated_at[:10] }}
