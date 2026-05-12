# **🤖 SELF-ASSESSMENT AI ACT – {{ data.system_name }}**
**Nivel de Riesgo Declarado**: {{ data.risk_level }}
**Fecha de Generación**: {{ data.generated_at }}
**Versión**: 1.1
**Responsable**: {{ data.dpo.name }} (DPO)

---
## **📌 1. CONTEXTO**
CASTÚO-SYSTEM™ utiliza **sistemas de IA generativa** para:
1. **Educación forestal**: Vídeos explicativos sobre gestión sostenible.
2. **Simulaciones técnicas**: Demostraciones de poda, tala, etc.
3. **Generación de informes**: Resúmenes automáticos de datos forestales.

**Modelos Utilizados** (todos alojados en UE con licencias compatibles):
{% for use_case in data.use_cases %}
### **{{ use_case.name }}**
| **Modelo**       | **Licencia** | **Hosting**          | **Cumplimiento**          |
|------------------|--------------|----------------------|---------------------------|
{% for model in use_case.ai_models %}
| {{ model.name }} | {{ model.license }} | {{ model.hosting }} | {{ model.compliance|join(", ") }} |
{% endfor %}
**Medidas de Mitigación de Riesgos**:
{% for measure in use_case.risk_mitigation %}
- {{ measure }}
{% endfor %}
---
{% endfor %}

## **📌 2. CUMPLIMIENTO CON EL AI ACT (Reglamento UE 2024/1689)**
### **2.1. Transparencia (Art. 52)**
- **Información al usuario**:
  - Todos los vídeos generados incluyen metadatos de compliance (ej: `compliance.evidence`).
- **Interfaz de usuario**:
  - El MediaGenerator muestra: modelo utilizado, licencia (EUPL-1.2/MIT), enlace a transacción en GaiaChain.

### **2.2. Gestión de Riesgos (Anexo III)**
- **Evaluación documentada** en: `02.03.02_Evaluacion_Riesgos.xlsx`
- **Mitigación**: Validación de prompts contra políticas forestales; revisión humana de muestras aleatorias (10%).

### **2.3. Derechos de los Usuarios (Art. 53)**
- **Derecho a impugnar**: Procedimiento documentado en `02.03_AI_Act_EU/02.03.04_Gestion_Derechos_Impugnacion.md`. Flujo: Usuario reporta → DPO revisa en <48h → Si procede, eliminación y registro en GaiaChain.

## **📌 3. EVIDENCIAS TÉCNICAS**
| **Requisito**               | **Implementación**                                                                 | **Evidencia**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Transparencia (Art. 52)** | Metadatos en cada respuesta API                                                     | `backend/api/services/media_service.py`                                      |
| **Registro (Art. 53)**      | Cada `media_id` se registra en GaiaChain                                          | TX: [0x123...](https://explorer.gaiachain.es/tx/0x123...)                      |
| **Aislamiento (Anexo III)** | Media Engines en red interna (`media_network`)                                      | `docker-compose.eu-oss.yml`                                                  |
| **Auditabilidad**           | Logs en Wazuh con `event_type:media_generation_*`                                  | `backend/api/security/audit.py`                                              |

---
## **📌 4. CONCLUSIÓN**
**Nivel de Riesgo Final**: **Bajo** (sistema de IA para educación con medidas de mitigación documentadas).

**Próximos Pasos**:
1. **2026**: Implementar revisión automática de prompts con modelos de moderación.
2. **2027**: Certificación externa bajo el AI Act (Anexo III).

---
**Firma del DPO**:
_________________________
{{ data.dpo.name }}
Delegada de Protección de Datos
CASTÚO-SYSTEM™
{{ data.generated_at[:10] }}
