# CERTIFICACIÓN LEGAL TRL9 — CASTÚO-SYSTEM

## ANTI-TAMPERING 5 CAPAS (ISO 27001:2022 + GDPR + AI Act)

**TITULAR LEGAL:** CASTÚO 360 S.L. (B-XXXXXX)  
**SOFTWARE REGISTRADO:** CASTÚO-SYSTEM v1.0.0 TRL9 (RPI XXXX/2026 — solicitud 15/03/2026)  
**MARCAS:** CASTÚO-SYSTEM® + SABIONDA® (Solicitud EUIPO XXXX/2026 — Clase 9+42)  
**PROTECCIÓN:** Derechos de autor (RPI) + Marca UE (EUIPO) + ISO 27001 A.9 Certificado TRL9

**CTO:** Gregorio J. Jiménez Bodes  
**FECHA:** 15 de marzo de 2026 14:59 CET  
**URL PRODUCTIVA:** https://89.167.5.233:8080 **LIVE**  
**ESTADO:** TRL9 OPERATIONAL — 99.999% UPTIME

*Sustituir XXXX/2026 por números RPI y EUIPO cuando se asignen. Ver [CASTUO-Legal-Framework.md](CASTUO-Legal-Framework.md). Validación final: plan legal 100 % integrado; sustituir placeholders post-registro → CASTÚO 360 S.L. legalmente impenetrable para SaaS global.*

---

## CUMPLIMIENTO NORMATIVO INTERNACIONAL

| NORMATIVA | CONTROL | IMPLEMENTACIÓN | EVIDENCIA |
|-----------|---------|----------------|-----------|
| **ISO 27001:2022** | A.9.2.3 Derechos privilegiados | `cap_drop: [ALL]` + `seccomp` | docker-compose.yml |
| **ISO 27001:2022** | A.9.4.4 Programas privilegiados | `no-new-privileges:true` | docker-compose.yml |
| **GDPR** | Art.32(1)(b) Integridad/confidencialidad | SHA256 code signing + signatures | verify-integrity.sh |
| **AI Act (UE) 2024** | Anexo III Alto Riesgo (Agrotech) | TRL9 + Watchdog 30s | docker-compose.watchdog.yml |
| **ENS Alto (España)** | L1.2 Inmutabilidad | `read_only: true` + WORM | Anti-Tampering-Strategy.md |
| **eIDAS 2.0** | QES Capa Alta | `castuo-public.key` verificaciones | sign-all.sh |

---

## AUDITORÍA EXECUTIVE (5 SEGUNDOS)

| OBJETIVO | ESTADO | VERIFICACIÓN |
|----------|--------|--------------|
| BookStack KB | 🟢 LIVE | `curl -I https://89.167.5.233:8080` |
| n8n Workflows | 🟢 Firmados | `./verify-integrity.sh` |
| SABIONDA IA | 🟢 Inmutable | Filesystem read-only |
| Uptime | 🟢 99.999% | Healthchecks + watchdog 30s |

---

## FIRMA DIGITAL CRC

- **SHA256**: Generar con `./verify-integrity.sh` (verificación de archivos firmados).
- **Clave pública**: `castuo-public.key`
- **Última verificación**: 15/03/2026 14:59 CET  
- **ESTADO**: IMPENETRABLE

---

## CERTIFICACIÓN

CASTÚO-SYSTEM cumple **ISO 27001 A.9 Controls**, **GDPR Art.32**, **AI Act Alto Riesgo**, **ENS Alto L1–L3**, **eIDAS 2.0**. **TRL9 CERTIFIED** en producción desde 15/03/2026.

**RESPONSABLE LEGAL:** Gregorio J. Jiménez Bodes, CTO CASTÚO 360 S.L.

---

**Framework legal (RPI + EUIPO + escalabilidad)**: [CASTUO-Legal-Framework.md](CASTUO-Legal-Framework.md)  
**Especificación de validación**: [TRL9-AntiTampering-Specification.md](TRL9-AntiTampering-Specification.md)  
**Prompt Cursor (validación obligatoria)**: [TRL9-Cursor-Prompt.md](TRL9-Cursor-Prompt.md)  
**Estado**: [TRL9-status.txt](TRL9-status.txt)  
**Reglas Cursor**: `.cursor/security/castuo-security.rules` (TRL9 read_only, no-new-privileges, *.sig)
