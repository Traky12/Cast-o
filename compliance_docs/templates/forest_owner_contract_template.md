# **📜 {{ data.owner_contract.title }}**
**Número de Contrato**: [NÚMERO]
**Fecha**: {{ generated_at[:10] }}
**Lugar**: {{ system.regional_scope.name }}

---
## **📌 PARTE 1: DATOS DE LAS PARTES**

### **1.1. Prestador de Servicios**
- **Razón Social**: {{ data.owner_contract.parties.provider.name }}
- **CIF/NIF**: {{ data.owner_contract.parties.provider.cif }}
- **Domicilio**: {{ data.owner_contract.parties.provider.address }}
- **Representante Legal**: {{ data.owner_contract.parties.provider.representative }}

### **1.2. Propietario Forestal**
- **Nombre/Apellidos**: {{ data.owner_contract.parties.owner.name }}
- **NIF/NIE**: {{ data.owner_contract.parties.owner.nif }}
- **Domicilio**: {{ data.owner_contract.parties.owner.address }}

---
## **📌 PARTE 2: OBJETO DEL CONTRATO**
CASTÚO-SYSTEM™ se compromete a prestar los siguientes servicios al Propietario Forestal:

{% for service in data.owner_contract.services %}
### **Servicio {{ loop.index }}: {{ service.name }}**
**Descripción**: {{ service.description }}

**Base Legal**:
{% for law in service.legal_basis %}
- {{ law }}
{% endfor %}

---
{% endfor %}

## **📌 PARTE 3: OBLIGACIONES DE LAS PARTES**

### **3.1. Obligaciones de CASTÚO-SYSTEM™**
{% for obligation in data.owner_contract.obligations.provider %}
- {{ obligation }}
{% endfor %}

### **3.2. Obligaciones del Propietario Forestal**
{% for obligation in data.owner_contract.obligations.owner %}
- {{ obligation }}
{% endfor %}

---
## **📌 PARTE 4: PROTECCIÓN DE DATOS**

### **4.1. Responsable del Tratamiento**
- **Identidad**: {{ data.owner_contract.data_protection.responsible }}
- **Finalidades**:
{% for purpose in data.owner_contract.data_protection.purposes %}
- {{ purpose }}
{% endfor %}

### **4.2. Derechos del Interesado**
El Propietario Forestal tiene derecho a:
{% for right in data.owner_contract.data_protection.rights %}
- {{ right }}
{% endfor %}

**Plazo de Conservación**: {{ data.owner_contract.data_protection.retention }}

---
## **📌 PARTE 5: CONFIDENCIALIDAD Y PROPIEDAD INTELECTUAL**
1. **Confidencialidad**: Ambas partes mantienen confidencialidad sobre la información intercambiada. Excepción: cumplimiento de obligaciones legales (ej: solicitudes de {{ system.regional_scope.competent_authority }}).
2. **Propiedad Intelectual**: Los vídeos y documentos generados son propiedad del Propietario Forestal. CASTÚO-SYSTEM™ retiene una licencia no exclusiva para uso en demostraciones y formación.

---
## **📌 PARTE 6: DURACIÓN Y RESOLUCIÓN**

### **6.1. Duración**
- **Plazo**: 5 años, renovable automáticamente por períodos anuales.
- **Inicio**: Fecha de firma.

### **6.2. Causas de Resolución**
{% for condition in data.owner_contract.termination.conditions %}
- {{ condition }}
{% endfor %}

### **6.3. Efectos de la Resolución**
- **Devolución de Datos**: En formato digital (JSON/GeoJSON) en un plazo de 30 días.
- **Eliminación de Datos**: {{ data.owner_contract.termination.data_deletion }}

---
## **📌 PARTE 7: LEY APLICABLE Y RESOLUCIÓN DE CONFLICTOS**
- **Ley Aplicable**:
{% for law in data.owner_contract.applicable_law %}
- {{ law }}
{% endfor %}

- **Jurisdicción**: {{ data.owner_contract.jurisdiction }}

---
## **📌 PARTE 8: FIRMAS**

**En {{ system.regional_scope.name }}, a {{ generated_at[:10] }}**

**Por CASTÚO-SYSTEM™**:
_________________________
{{ data.owner_contract.parties.provider.representative }}
Administrador

**Por el Propietario Forestal**:
_________________________
{{ data.owner_contract.parties.owner.name }}
Propietario/a

---
**Anexo I: Glosario**
- **SIGPAC/SIGIF**: Sistema de Información Geográfica de Parcelas Agrícolas/Florestais.
- **GaiaChain**: Blockchain utilizada para registro de eventos de compliance.
- **RGPD/GDPR**: Reglamento General de Protección de Datos (UE 2016/679).

**Anexo II: Políticas**
- Política de Privacidad: https://castuo-system.eu/politica-privacidad
- Términos de Servicio: https://castuo-system.eu/terminos-servicio
