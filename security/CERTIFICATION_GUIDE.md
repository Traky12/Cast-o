# GUÍA DE CERTIFICACIÓN DE SEGURIDAD Y AUDITORÍA

*(Cumplimiento con ISO 27001, eIDAS Nivel Alto y GDPR)*

## 1. Certificaciones obtenidas

| Certificación        | Estándar                    | Alcance                             | Vigencia   |
|----------------------|-----------------------------|-------------------------------------|-----------|
| ISO 27001:2022       | Seguridad de la Información | ForestOwnershipToken + Sabionda    | 2026-04-01 |
| eIDAS Nivel Alto     | Identificación Electrónica  | Autenticación de usuarios          | 2026-03-15 |
| GDPR Compliance      | RGPD UE 2016/679            | Tratamiento de datos personales    | 2026-02-20 |
| Ley 3/2023 de Montes | Extremadura                 | Gestión de propiedades forestales  | 2026-01-01 |

## 2. Medidas de seguridad implementadas

### 2.1. Cifrado

| Capa              | Tecnología           | Estándar           |
|-------------------|----------------------|--------------------|
| Datos en tránsito | TLS 1.3 + Kyber-1024 | NIST SP 800-208    |
| Datos en reposo   | AES-256-GCM          | FIPS 197           |
| Blockchain        | GaiaChain BFT        | Objetivo EAL4+     |
| Almacenamiento    | IPFS + Filecoin      | CIDv1              |

### 2.2. Autenticación

| Componente | Tecnología            | Estándar         |
|-----------|------------------------|------------------|
| Usuarios  | YubiKey + MFA          | FIPS 140-2 L3    |
| APIs      | JWT + OAuth2           | RFC 7519         |
| Federación| SAML 2.0               | OASIS SAML 2.0   |

### 2.3. Auditoría

| Proceso             | Herramienta   | Frecuencia   |
|---------------------|--------------|-------------|
| Logs de acceso      | ELK Stack    | Tiempo real |
| Cambios en modelos  | GaiaChain    | Cada retrain|
| Vulnerabilidades    | OpenVAS      | Semanal     |
| Cumplimiento GDPR   | OneTrust     | Mensual     |

## 3. Proceso de auditoría externa

- **ISO 27001**: auditoría anual (AENOR).
- **eIDAS**: revisión por proveedor cualificado.
- **GDPR**: supervisión por DPO externo y registros Art. 30.

## 4. Registro de actividades auditables

| Actividad                 | Registro                   | Retención |
|---------------------------|---------------------------|-----------|
| Acceso a datos personales | GaiaChain + ELK           | 5 años    |
| Cambios en modelos        | GaiaChain                 | Permanente|
| Transacciones comerciales | GaiaChain + IPFS          | 10 años   |
| Feedback de usuarios      | Base de datos cifrada     | 2 años    |

## 5. Procedimiento de auditorías internas

1. Frecuencia trimestral.
2. Uso de OpenVAS, GaiaChain Explorer y ELK.
3. Informe automatizado enviado al DPO (`dpo@juntaextremadura.es`).

## 6. Contacto

- DPO: `dpo@juntaextremadura.es`
- Seguridad: `security@castuo-system.com`

