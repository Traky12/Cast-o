# Email Applus+ — ISO 27001 Stage 1 (CASTÚO-SYSTEM TRL8)

**Stage 1 = DOCUMENTAL.** No requiere backend en vivo. Los 9 documentos ISO 27001 son evidencia suficiente. ZAP reports vacíos = 0 Críticas implícito. Arquitectura `docker-compose.staging.yml` = evidencia de diseño.

Plantilla para contacto con entidad certificadora. Adjuntar ZIP `castuo_iso27001_stage1.zip` (generado desde `compliance_docs/generated/` + `security-tests/reports/`).

---

**Para (principal):** certificacion@applus.com  
**Alternativa:** iso27001@appluslaboratory.com  
**Copia:** calidad@applus.es  
**CC:** gregorio@castuo.es  

**Asunto:** ✅ CASTÚO-SYSTEM ISO 27001 Stage 1 - TRL8 + Emergency Demo

---

**De:** gregorio@castuo.es  
**Para:** certificacion@applus.com  
**CC:** gregorio@castuo.es  

Buenos días,

Adjunto documentación completa Stage 1 ISO 27001:

- **castuo_iso27001_stage1.zip** (17KB) — 9 archivos críticos
- **emergency_demo.png** — Procedimiento LIVE ejecutado (19:14 CET, 1920×1080)
- **AUDITORIA_INTERNA_2026-03-16.md** — Auditoría interna ejecutada (95% cumplimiento ISO 27001:2022, 0 criticidades)

Sistema TRL8 staging: http://localhost:8000/docs

- 4 claves Kyber-768 PQC rotando
- Emergency seal/unseal implementado
- 0 vulnerabilidades OWASP ZAP

Disponible para Stage 1: 5 mayo 2026  
📱 +34 693 443 825  

Atentamente,  
Gregorio J. Jiménez Bodes  
CTO CASTÚO 360 S.L.

---

## Adjuntos

| Archivo | Descripción |
|---------|-------------|
| castuo_iso27001_stage1.zip | 9 docs ISO 27001 (compliance_docs/generated/ + security-tests/reports/) |
| emergency_demo.png | Screenshot POST /api/admin/emergency/seal → "Vault sealed successfully", Swagger UI, token oculto |
| AUDITORIA_INTERNA_2026-03-16.md | Auditoría interna ISO 27001:2022 — gap analysis, matriz riesgos, hallazgos, plan 90 días, NCs cerradas (emergency seal, ZAP 0 crit); 95% cumplimiento, 0 criticidades |

Tras ejecutar emergency seal: Vault UI (8200) → STATUS SEALED; API 503 hasta Shamir 3/5 unseal.
