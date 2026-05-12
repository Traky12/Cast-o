# **🛡️ DECLARACIÓN DE APLICABILIDAD ISO 27001:2022**
**Organización**: CASTÚO-SYSTEM™
**Fecha**: {{ data.generated_at }}
**Versión**: 2.1
**Responsable**: {{ data.dpo.name }} (DPO)

---
## **📌 1. ALCANCE DEL SGSI**
El **Sistema de Gestión de Seguridad de la Información (SGSI)** de CASTÚO-SYSTEM™ cubre:
- **Backend Forestal**: API en FastAPI (Python).
- **Frontend**: React con ConsentManager y MediaGenerator.
- **Infraestructura**: Hosting en OVH (Francia) y Hetzner (Alemania).
- **Datos**: Información de parcelas forestales, consentimientos y media generada.

**Exclusiones**: Infraestructura física de proveedores cloud (OVH/Hetzner); dispositivos personales de usuarios.

---
## **📌 2. DECLARACIÓN DE APLICABILIDAD**
{% for code, control in data.controls.items() %}
### **{{ code }}: {{ control.name }}**

| **Requisito**      | **Implementación** | **Evidencia** |
|--------------------|---------------------|---------------|
| Implementación     | {% for item in control.implementation %}- {{ item }}{% endfor %} | {% for item in control.evidence %}- {{ item }}{% endfor %} |

---
{% endfor %}

## **📌 3. JUSTIFICACIÓN DE CONTROLES EXCLUIDOS**
| **Control**       | **Razón de Exclusión**                                                                 |
|-------------------|----------------------------------------------------------------------------------------|
| A.6.1.5           | No aplicable (no hay información en papel).                                            |
| A.11.2.9          | Delegado al proveedor de cloud (OVH/Hetzner).                                           |
| A.16.1.7          | No aplicable (no hay desarrollo físico de hardware).                                    |

---
## **📌 4. ESTADO DE IMPLEMENTACIÓN**
| **Dominio**          | **% Implementado** | **Próximos Pasos**                                  |
|----------------------|--------------------|------------------------------------------------------|
| **Políticas**        | 100%               | Revisión anual (marzo 2027).                        |
| **Organización**     | 90%                | Formación en seguridad para nuevos empleados.       |
| **Control de Acceso**| 100%               | Mantener configuración actual (Keycloak + Vault).    |
| **Criptografía**     | 95%                | Migración a HSM físico en 2027.                     |
| **Seguridad Operativa** | 90%             | Automatizar backups de MinIO.                       |
| **Comunicaciones**   | 100%               | TLS 1.2+ en Traefik.                                |
| **Gestión de Incidentes** | 85%           | Implementar playbooks automatizados.               |

---
## **📌 5. PLAN DE TRATAMIENTO DE RIESGOS**
| **Riesgo**                          | **Tratamiento**                                                                 | **Responsable**   | **Plazo**       |
|--------------------------------------|----------------------------------------------------------------------------------|-------------------|------------------|
| Compromiso de claves en Vault        | Migración a HSM físico + rotación automática.                                   | Seguridad         | Q1 2027          |
| Falta de integración con SIGPAC     | Desarrollar API de validación.                                                  | Backend Team      | Q3 2026          |
| Escalado de Media Engines            | Monitorizar uso de GPU en OVH/Hetzner.                                          | DevOps            | Continuo         |
| Cambios en AI Act                   | Revisión trimestral de compliance.                                               | DPO               | Trimestral      |

---
## **📌 6. DECLARACIÓN DE CONFORMIDAD**
**Fecha de Certificación**: [Pendiente auditoría externa 2026]
**Alcance**: Gestión de consentimientos (GDPR + Ley 3/2023); Generación de media educativa (AI Act); Protección de datos personales (ISO 27001 A.18.1.4).

**Firma del DPO**:
_________________________
{{ data.dpo.name }}
Delegada de Protección de Datos
CASTÚO-SYSTEM™
{{ data.generated_at[:10] }}
