# Política de Seguridad de la Información (PSI) — ISO 27001

**Versión**: 1.0  
**Fecha**: [DD/MM/2026]  
**Alineada con**: ISO 27001, ENS (Esquema Nacional de Seguridad) Alto  
**Aprobación**: Consejo Asesor

---

## 1. Objetivo

Garantizar la **confidencialidad, integridad y disponibilidad** de la información de CASTÚO Agrovoltaic Tech SL, CTAEX, clientes y distribuidores.

---

## 2. Alcance

- Todos los sistemas de **CASTÚO Agrovoltaic Tech SL** (APIs, bases de datos, blockchain, IoT).
- Datos de **CTAEX, clientes y distribuidores UE**.
- Entornos: producción, staging, desarrollo (según clasificación).

---

## 3. Roles y responsabilidades

| Rol | Responsable | Función |
|-----|-------------|---------|
| **CISO** | CTO | Dirección de seguridad, aprobación de controles |
| **DPO** | Delegado Protección de Datos | RGPD, registro tratamientos, AEPD |
| **Equipo de Seguridad** | DevOps / Backend | Implementación técnica (cifrado, RBAC, logs) |

---

## 4. Controles obligatorios (resumen)

| Control ISO 27001 | Implementación | Responsable |
|-------------------|----------------|-------------|
| **A.5.1** Políticas de seguridad | PSI documentada y revisada anualmente | Seguridad |
| **A.9.1** Control de accesos | RBAC (Admin, Técnico, Auditor, Usuario) | DevOps |
| **A.12.1** Seguridad física | Servidores Hetzner, acceso restringido | DevOps |
| **A.14.1** Cifrado | AES-256 en reposo, TLS 1.3 en tránsito | DevOps |
| **A.12.4** Logs | ELK Stack, retención 5 años | DevOps |
| **A.16** Gestión de incidentes | Plan de Contingencia 2.0, notificación <72h AEPD si procede | Legal |

---

## 5. Cifrado

- **Datos en reposo**: AES-256 (BD, backups). HSM para claves críticas (recomendado).
- **Datos en tránsito**: TLS 1.3. Auditoría con OpenSSL.

---

## 6. Autenticación y accesos

- **MFA (TOTP)** para todos los usuarios (Authy / Google Authenticator). Ver `Guía-MFA.md`.
- **RBAC**: Admin, Técnico, Auditor, Usuario. Revisión con Open Policy Agent (OPA).

---

## 7. Logs de auditoría

- Registrar **quién, qué, cuándo** en todas las acciones sensibles.
- **ELK Stack** (Elasticsearch, Logstash, Kibana). Retención: **5 años**.

---

## 8. Pentesting

- Pruebas de penetración **semestrales** (S21sec, ElevenPaths).
- Corrección de vulnerabilidades críticas en **< 7 días**.

---

## 9. Revisión

- Revisión anual de la PSI por el Consejo Asesor.
- Actualización del Registro de Activos (ver `Asset-Register.md`).
