# ANEXO V — PROTOCOLO DE SEGURIDAD Y CUMPLIMIENTO NORMATIVO
**Acuerdo de Colaboración Estratégica CTAEX S.L. – CASTÚO-SYSTEM**

**Versión:** 1.0  
**Fecha:** [DD/MM/AAAA]  
**Referencia:** Acuerdo marco CTAEX – CASTÚO-SYSTEM.

---

## 1. Normativas aplicables

| Normativa | Ámbito | Responsable de cumplimiento |
|-----------|--------|-----------------------------|
| **GDPR (UE 2016/679)** | Protección de datos personales (ej.: datos de agricultores, empleados). | EL PROVEEDOR (DPO) |
| **ISO 27001** | Seguridad de la información (acceso, cifrado, auditorías). | Ambos (Equipo de Seguridad) |
| **RD 903/2025** | Regulación de cannabis medicinal en España. | EL CLIENTE (Legal) |
| **Ley 38/2003** | Subvenciones públicas (Fondo de I+D). | Ambos (Finanzas) |
| **AI Act UE 2024/1689** | Ética en IA (transparencia, equidad). | EL PROVEEDOR (Equipo de IA) |

---

## 2. Medidas de seguridad

### 2.1. Acceso y autenticación

| Medida | Detalle |
|--------|---------|
| **Autenticación multifactor (MFA)** | Todos los usuarios deben usar **MFA (TOTP)** para acceder al Sistema. |
| **IP Whitelisting** | Solo IPs autorizadas (ej.: 89.167.5.0/24 para CTAEX). |
| **Roles y permisos** | **RBAC** (Role-Based Access Control) con niveles: Admin, Técnico, Auditor, Usuario. |
| **Logs de acceso** | Registros de todos los accesos (conservación: 5 años). |

### 2.2. Cifrado y protección de datos

| Medida | Detalle |
|--------|---------|
| **TLS 1.3** | Todos los datos en tránsito se cifrarán con TLS 1.3. |
| **AES-256** | Datos en reposo (ej.: base de datos) se cifrarán con AES-256. |
| **Masking de datos** | Datos personales (ej.: NIFs) se enmascararán automáticamente (GDPR Art. 25). |
| **Backups** | Copias de seguridad diarias en **Backblaze B2** (retención: 90 días). |

### 2.3. Auditorías

| Tipo | Frecuencia | Responsable |
|------|------------|-------------|
| **Auditoría interna** | Trimestral | EL PROVEEDOR (Seguridad) |
| **Auditoría externa** | Anual | Tercero independiente (ej.: AENOR) |
| **Pruebas de penetración** | Semestral | Equipo de Seguridad |

---

## 3. Cumplimiento normativo específico

### 3.1. GDPR (UE 2016/679)

| Requisito | Implementación |
|-----------|----------------|
| **Consentimiento** | Todos los usuarios deben aceptar una **política de privacidad** al registrarse. |
| **Derecho al olvido** | Los datos personales podrán ser eliminados bajo solicitud (endpoint: `DELETE /users/{id}/data`). |
| **DPO** | **EL PROVEEDOR** designará un **Delegado de Protección de Datos (DPO)**. |
| **Registros de actividad** | Se mantendrán registros de todas las operaciones con datos personales (6 años). |

### 3.2. ISO 27001

| Requisito | Implementación |
|-----------|----------------|
| **Política de seguridad** | Documento interno con medidas de seguridad (acceso, cifrado, backups). |
| **Gestión de riesgos** | Análisis anual de riesgos (ej.: fallos de seguridad, pérdida de datos). |
| **Control de accesos** | Solo personal autorizado (Anexo IV) podrá acceder a datos sensibles. |
| **Auditorías internas** | Revisión trimestral de cumplimiento. |

### 3.3. RD 903/2025 (Cannabis medicinal)

| Requisito | Implementación |
|-----------|----------------|
| **Licencias AEMPS** | Validación automática de licencias antes de registrar lotes. |
| **Límites de THC/CBD** | `CHECK (thc_percentage <= 0.3)` en la base de datos. |
| **Trazabilidad** | Registro en **GaiaChain** de todos los lotes (desde semilla hasta venta). |
| **Informes AEMPS** | Generación automática de informes para auditorías (endpoint: `/cannabis/batches/{id}/aemps-report`). |

---

## 4. Protocolos de incidente

### 4.1. Brecha de seguridad

| Paso | Acción | Responsable |
|------|--------|-------------|
| **Detección** | Identificar la brecha (ej.: acceso no autorizado, pérdida de datos). | Equipo de Seguridad |
| **Contención** | Aislar los sistemas afectados. | DevOps |
| **Notificación** | Notificar a **EL CLIENTE** en **<24 h** y a la **AEPD** en **<72 h** (si afecta a datos personales). | DPO |
| **Investigación** | Determinar la causa raíz. | Equipo de Seguridad |
| **Mitigación** | Aplicar parches o cambios para evitar futuros incidentes. | DevOps |
| **Informe final** | Documentar el incidente y acciones tomadas (para auditorías). | DPO |

### 4.2. Incumplimiento normativo

| Normativa | Acción | Responsable |
|-----------|--------|-------------|
| **GDPR** | Notificar a la **AEPD** en **72 h** si hay una brecha de datos personales. | DPO |
| **ISO 27001** | Realizar una **auditoría interna** para identificar fallos. | Equipo de Seguridad |
| **RD 903/2025** | **Suspender certificaciones** hasta resolver el incumplimiento. | EL CLIENTE (Legal) |

---

## 5. Aceptación

Las partes aceptan este Anexo como **parte integrante** del Acuerdo Principal.
