# Registro de Activos — ISO 27001

**Versión**: 1.0  
**Fecha**: [DD/MM/2026]

---

## Activos de información y sistemas

| Activo | Tipo | Ubicación | Responsable | Criticidad |
|--------|------|-----------|-------------|------------|
| Servidor PostgreSQL | Base de datos | Hetzner (DE) | DevOps | Alta |
| GaiaChain Nodes | Blockchain | [Proveedor] | Blockchain Team | Crítica |
| API Backend (FastAPI) | Aplicación | Hetzner / Docker | DevOps | Alta |
| Redis (cola, sesiones) | Cache/Cola | Hetzner | DevOps | Media |
| Frontend Next.js | Aplicación | CDN / Hetzner | DevOps | Media |
| Sensores IoT (Libelium) | Hardware | CTAEX / campo | IoT Team | Alta |
| LIMS CTAEX (integración) | Externo | CTAEX | Backend Team | Alta |
| Backups (Backblaze B2) | Backup | B2 | DevOps | Crítica |

---

## Clasificación de la información

| Tipo de dato | Clasificación | Cifrado | Retención |
|--------------|---------------|---------|-----------|
| Datos personales (usuarios) | Confidencial | AES-256, TLS 1.3 | Según RGPD |
| Lotes y certificaciones | Operativa | AES-256, TLS 1.3 | 5 años mínimo |
| Logs de auditoría | Confidencial | AES-256 | 5 años |
| Claves API / secretos | Crítica | HSM / vault | Rotación anual |

---

## Revisión

- Actualización trimestral del registro.
- Revisión de responsables y criticidad en cada cambio de arquitectura.
