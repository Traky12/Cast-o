# TRL — tabla maestra orientativa (CASTÚO-SYSTEM)

Documento de **seguimiento**: no sustituye evidencia, auditoría ni checklist industrial.

| Módulo / cinta | PRONT / guía | TRL declarado en repo (honesto) | Evidencia siguiente paso |
|----------------|--------------|-----------------------------------|---------------------------|
| RGI / NF plantilla | `PRONT-CASTUO-RGI-v2-2026.md` | Experimental / lab | Dataset real, métricas reconstrucción, edge medido |
| API lab hidroponía | `PRONTUARIO-AGROTECH-TLS.md` § | Integración TRL-6 staging | Piloto industrial, observabilidad |
| Pendrive LUKS / IAM | `deploy/PENDRIVE-CONTENIDO.md` | Operativo (ops) | Rotación de claves, runbook incidentes |
| Industrial vivo | `deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md` | Objetivo cliente | Completar checklist en despliegue real |
| SIGPAC / validación parcelas | `PRONT-CASTUO-SIGPAC-v1-2026.md`, `pei-001-sigpac/README.md`, `backend/integrations/sigpac_validator.py` | Scripts + PEI en repo; TRL operativo según piloto | Evidencia: informes PEI-001, datos reales anónimos, CI verde |
| n8n automatización | `PRONT-CASTUO-N8N-v1-2026.md`, `PRONTUARIO-AUTOMATIZACION-N8N-2026.md` | Exports + CLI validación; ejecución según despliegue | Logs n8n, webhooks en staging, `harden_n8n_flow.py` en pipeline |
| Robotics lab / edge | `PRONT-CASTUO-ROBOTICS-v1-2026.md`, `backend/integrations/robotics/README.md` | Lab + mock documentados | Piloto hardware controlado + `DPIA-Robotics-2026.md` según alcance |
| IA lab (federado SIGPAC / decisión n8n / visión edge) | `federated_trainer.py`, `ai_decision.py`, `ai_vision.py` + PRONTs § lab | **Experimental** (no TRL-9 por código solo) | Nodos reales, acuerdos RGPD, métricas + ONNX/medición edge si aplica |
| LoRA FAQ (Mistral u otra base HF) | `scripts/ai/mistral_lora/README.md`, `finetune_lora.py` | **Lab** (GPU típica; no RPi entrenamiento 7B) | Dataset propio, evaluación, licencia modelo, DPIA si datos personales |
| RGPD (scripts + plantillas) | `scripts/compliance/GDPR/README.md` | Ejecutable + docs | Legal/DPO, `audit_gdpr.py`, consentimientos reales |

**Regla:** subir TRL implica **artefactos verificables** (logs, tests, informes, piloto), no versión de dependencia.

*Añade filas al crear `PRONT-CASTUO-*` nuevos.*
