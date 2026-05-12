"""
Registro de coherencia sistema + seguridad/cifrado para el rol administrador general.
API estable: get_admin_general_playbook() devuelve deepcopy (no mutar el template en runtime).
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Final, List, Mapping

ADMIN_GENERAL_ROLE: Final[str] = "admin_general"
PLAYBOOK_VERSION: Final[str] = "2.5.5-20260316"

# Detalle técnico por capa (auditorías, paneles avanzados).
ENCRYPTION_STACK: Final[List[Dict[str, str]]] = [
    {
        "capa": "admin_master",
        "modulo": "security.admin_master_layer",
        "nota": "AES-256-GCM + HKDF; ADMIN_MASTER_KEY / Docker secret / security/.admin_master_key",
    },
    {
        "capa": "pqc_hibrido",
        "modulo": "backend.security.pq_crypto",
        "nota": "Kyber-1024 + Dilithium-5 si pqcrypto; fallback AES-GCM documentado",
    },
    {
        "capa": "robotics_lab_señales",
        "modulo": "backend.integrations.robotics.signal_manager",
        "nota": "ROBOT_SIGNAL_SYMMETRIC_KEY; AES-GCM en muestras PCM lab",
    },
    {
        "capa": "tls_despliegue",
        "modulo": "reverse_proxy / uvicorn",
        "nota": "TLS 1.3 en producción; Bearer CASTUO_ROBOTICS_LAB_BEARER_TOKEN en lab HTTP",
    },
    {
        "capa": "iam_bearer_archivo",
        "modulo": "backend.auth_roles.read_secret",
        "nota": "Tokens por rol vía ENV o *_FILE (Docker secret / volumen USB montado)",
        "pendrive_path": "/mnt/castuo_secure/tokens/",
    },
]

GOVERNANCE_DOCUMENTATION: Final[List[Dict[str, str]]] = [
    {"titulo": "Marco legal y soberanía UE 2026 (advertencia DPO, RGPD, Copernicus)", "ruta": "docs/legal/MARCO-LEGAL-SOBERANIA-UE-2026.md"},
    {"titulo": "Stack FOSS soberanía UE (compose postgres + guía activación)", "ruta": "docs/deploy/EU-FOSS-SOVEREIGNTY-STACK.md"},
    {"titulo": "n8n automatización CASTÚO (5 flujos críticos, lab, Grafana)", "ruta": "docs/deploy/PRONTUARIO-AUTOMATIZACION-N8N-2026.md"},
    {"titulo": "Conexiones completas automatización 2026 (n8n, workflows, lab)", "ruta": "docs/deploy/PRONTUARIO-CONEXIONES-COMPLETAS-AUTOMATIZACION-2026.md"},
    {"titulo": "Holografía y registro de información 2026", "ruta": "docs/deploy/PRONTUARIO-HOLOGRAFIA-REGISTRO-2026.md"},
    {"titulo": "Prontuario legal robotics", "ruta": "docs/legal/PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md"},
    {"titulo": "DPIA Robotics + §6 cadena lab", "ruta": "docs/legal/DPIA-Robotics-2026.md"},
    {"titulo": "Plan excelencia refuerzo", "ruta": "docs/legal/PLAN-EXCELENCIA-V2.5-REFUERZO.md"},
    {"titulo": "Coherencia admin general", "ruta": "docs/legal/SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md"},
    {"titulo": "Cifrado y roles v2.5", "ruta": "docs/legal/PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md"},
    {"titulo": "Capas cifrado v1.7.1", "ruta": "docs/security/ENCRYPTION_9_CAPAS_V1.7.1.md"},
    {"titulo": "Integración cifrada soberana 2026 (TLS, reposo, rotación)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md"},
    {"titulo": "Evaluación técnica CASTÚO 2026 (estado repo, evidencia, gaps)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-EVALUACION-TECNICA-CASTUO-2026.md"},
    {"titulo": "Plan maestro fases 20s 2026 (criterios aceptación, cronograma)", "ruta": "docs/deploy/PRONTUARIO-PLAN-FASES-ESTABILIZACION-20S-2026.md"},
    {"titulo": "Plan mejora inmediata 2026 (LLMNR, backup, HA, integraciones)", "ruta": "docs/deploy/PLAN-MEJORA-INMEDIATA-CASTUO-2026.md"},
    {"titulo": "Backup seguro en pen drive 2026 (LUKS, GPG, SQLite/PG)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-SEGURIDAD-BACKUP-PEN-DRIVE-2026.md"},
    {"titulo": "Mejora técnica y escalado 2026 (HAProxy, ACME, alertas, UE)", "ruta": "docs/deploy/PLAN-MEJORA-TECNICA-ESCALADO-CASTUO-2026.md"},
    {"titulo": "Escalado clientes + Sabionda + expansión UE 2026", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-ESCALADO-CLIENTES-SABIONDA-UE-2026.md"},
    {"titulo": "Sistema reforzado, seguro y evolutivo 2026 (blueprint)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-SISTEMA-REFORZADO-SEGURO-EVOLUTIVO-2026.md"},
    {"titulo": "Evolución completa CASTÚO 2026 (implementaciones por fases)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-EVOLUCION-COMPLETA-CASTUO-2026.md"},
    {"titulo": "Automatización y evolución 2026 (CI, seguridad, métricas, escalado)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-AUTOMATIZACION-EVOLUCION-SISTEMA-2026.md"},
    {"titulo": "Integración satelital y reforzamiento estructural 2026", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-INTEGRACION-SATELITAL-REFORZAMIENTO-2026.md"},
    {"titulo": "Análisis crítico y conexiones del sistema 2026 (Cursor, integración, soberanía UE)", "ruta": "docs/deploy/PRONTUARIO-ANALISIS-CRITICO-CONEXIONES-SISTEMA-2026.md"},
    {"titulo": "Soberanía datos UE (satellite_preprocess, CASTUO_EU_DATA_SOVEREIGNTY)", "ruta": "backend/energy_audit/eu_data_sovereignty.py"},
    {"titulo": "TraceChain PEI-002", "ruta": "docs/legal/TraceChain-Compliance-2026.md"},
    {"titulo": "PEI-002 stub README", "ruta": "pei-002-tracechain/README.md"},
    {"titulo": "Robotics lab README", "ruta": "backend/integrations/robotics/README.md"},
    {"titulo": "Deploy Hetzner ejemplo env", "ruta": "docs/deploy/robotics-lab-hetzner.env.example"},
    {"titulo": "Checklist Cursor → Hetzner D1 (CX22, TLS, comandos)", "ruta": "docs/deploy/CHECKLIST-CURSOR-HETZNER-D1.md"},
    {"titulo": "Agrotech ética y trazabilidad (TRL-6)", "ruta": "agrotech/ETHICS_TRACEABILITY.md"},
    {"titulo": "Agrotech + TLS Production (TRL-6)", "ruta": "docs/deploy/PRONTUARIO-AGROTECH-TLS.md"},
    {"titulo": "Checklist TRL-7 industrial / sistema vivo (cliente)", "ruta": "deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md"},
    {"titulo": "DNS + SSL Hetzner CX22 (guía, setup-ssl, verify PowerShell)", "ruta": "docs/deploy/DNS-SSL-HETZNER-CX22.md"},
    {"titulo": "Deploy producción Hetzner CX22 (compose, nginx, n8n, postgres)", "ruta": "deploy/README.md"},
    {"titulo": "Convención paths Vault KV", "ruta": "backend/security/VAULT_KV_PATHS.md"},
    {"titulo": "Prontuario refuerzo secrets / Vault A·B·C", "ruta": "docs/legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md"},
    {"titulo": "Checklist TRL6 edge Hetzner + pruebas", "ruta": "docs/deploy/CHECKLIST-TRL6-HETZNER-STAGING.md"},
    {"titulo": "Seguridad red + Multilinker (LLMNR/mDNS, playbook checks)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md"},
    {"titulo": "Refuerzo integral 2026 (seguridad + soberanía + evolución)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-REFUERZO-INTEGRAL-2026.md"},
    {"titulo": "Refuerzo y seguridad avanzada 2026 (hardening, runbook)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-REFUERZO-SEGURIDAD-AVANZADA-2026.md"},
    {"titulo": "Infraestructura soberana TRL6→TRL7 2026 (UE, migración)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-INFRAESTRUCTURA-SOBERANA-TRL6-TRL7-2026.md"},
    {"titulo": "Evolución segura y ética del sistema 2026 (FOSS UE, LLMNR, principios)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md"},
    {"titulo": "Auditoría técnica y ética CASTÚO 2026 (debilidades, roadmap)", "ruta": "docs/deploy/PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md"},
    {"titulo": "Auditoría + evolución resiliente 2026 (evidencia git, métricas medibles)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-AUDITORIA-EVOLUCION-RESILIENTE-2026.md"},
    {"titulo": "Plantilla solicitud firma DPO §6 robotics", "ruta": "docs/legal/DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md"},
    {"titulo": "Roadmap código TRL6→TRL7", "ruta": "docs/deploy/ROADMAP-TRL6-TRL7-CODE.md"},
    {"titulo": "Roadmap mejoras P1–P5 (perf, obs, seguridad)", "ruta": "docs/deploy/ROADMAP-MEJORAS-P1-P5-2026.md"},
    {"titulo": "Neuromórfica / memristores (orientación vs código sim)", "ruta": "docs/integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md"},
    {"titulo": "Ecología digital agrícola 2026 (biológico-digital, metáforas honestas)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-ECOLOGIA-DIGITAL-AGRICOLA-2026.md"},
    {"titulo": "Integración biológica-digital 2026 (equivalencias y límites éticos)", "ruta": "docs/deploy/PRONTUARIO-MAESTRO-INTEGRACION-BIOLOGICA-DIGITAL-2026.md"},
    {"titulo": "Checklist integraciones y mejoras P1–P3", "ruta": "docs/deploy/CHECKLIST-INTEGRACIONES-MEJORAS-2026.md"},
    {"titulo": "Script validación TRL6 (PowerShell)", "ruta": "scripts/windows/Invoke-TRL6-Validation.ps1"},
    {"titulo": "Export evidencia TRL6 (JUnit + manifest)", "ruta": "scripts/windows/Export-TRL6-Evidence.ps1"},
    {"titulo": "Plantilla informe evidencia TRL6 (legal)", "ruta": "docs/legal/INFORME-EVIDENCIA-TRL6-PLANTILLA.md"},
    {"titulo": "Cliente Vault opcional (hvac)", "ruta": "backend/security/vault.py"},
    {"titulo": "Matriz TRL campo (orientativa)", "ruta": "docs/legal/PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md"},
]

# Chequeos declarativos para ops en host edge / LAN mixta (no se ejecutan solos en CI).
CRITICAL_HARDENING_CHECKS: Final[Mapping[str, Mapping[str, Any]]] = {
    "llmnr_multicast_off": {
        "scope": "Linux con systemd-resolved (p. ej. VPS Ubuntu / Hetzner)",
        "cmd": "grep -E '^LLMNR=|^MulticastDNS=' /etc/systemd/resolved.conf || true",
        "expected": ["LLMNR=no", "MulticastDNS=no"],
        "verify": "Ambas directivas bajo [Resolve]; resolvectl status",
        "remediation": "Editar /etc/systemd/resolved.conf (ver PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md §2.2)",
        "territorio": "Cierra descubrimiento por multicast que alimenta poisoning hacia sesiones en la misma capa 2.",
    },
    "avoid_nuke_systemd_resolved": {
        "scope": "Ubuntu/Debian típico",
        "verify": "DNS resuelve tras cambios; stub-resolv.conf coherente",
        "remediation": "No deshabilitar systemd-resolved entero sin plan DNS alterno (rompe muchos despliegues).",
        "territorio": "Sin resolver estable, el edge deja de ver el río (APIs, Vault, cadena).",
    },
    "nbt_ns_windows": {
        "scope": "Estaciones Windows en broadcast con operadores",
        "verify": "NetbiosOptions=2 en interfaces Tcpip* o GPO DNS Client",
        "remediation": "Deshabilitar NetBIOS sobre TCP/IP; GPO Turn off multicast name resolution si AD",
        "territorio": "El mismo aire RF/LAN no debe entregar nombres falsos a quien custodia tokens CASTUO_*.",
    },
    "udp_5355_evidence": {
        "scope": "Post-despliegue",
        "verify": "tcpdump -ni any udp port 5355 -c 20 en ventana de prueba",
        "remediation": "Si tráfico inesperado: revisar impresoras/mDNS o reglas firewall acordadas",
        "territorio": "La evidencia corta evita compliance solo en papel.",
    },
}

CRITICAL_ENV_VARS: Final[List[str]] = [
    "ADMIN_MASTER_KEY",
    "ADMIN_MASTER_KEY_FILE",
    "GAIA_CHAIN_RPC",
    "GAIA_CHAIN_AUDIT_CONTRACT",
    "GAIA_CHAIN_AUDIT_ABI",
    "GAIA_CHAIN_PRIVATE_KEY",
    "GAIA_CHAIN_PRIVATE_KEY_FILE",
    "CASTUO_ROBOTICS_LAB_BEARER_TOKEN",
    "CASTUO_ROBOTICS_LAB_BEARER_TOKEN_FILE",
    "CASTUO_ROBOTICS_LAB_CHAIN_REGISTER",
    "CASTUO_ROBOTICS_LAB_CHAIN_TOKEN_ID",
    "CASTUO_ROBOTICS_LAB_CHAIN_INCLUDE_PARCEL_ID",
    "ROBOT_SIGNAL_SYMMETRIC_KEY",
    "CASTUO_ADMIN_GENERAL_BEARER",
    "CASTUO_ADMIN_GENERAL_BEARER_FILE",
    "VAULT_ADDR",
    "VAULT_TOKEN",
    "VAULT_TOKEN_FILE",
]

# Template canónico (jerarquía resumida TRL-5 / operaciones).
ADMIN_GENERAL_PLAYBOOK: Dict[str, Any] = {
    "role": ADMIN_GENERAL_ROLE,
    "version": PLAYBOOK_VERSION,
    "encryption_stack": [
        "admin_master_layer",
        "pq_crypto.dilithium_sign",
        "signal_manager.aes256_gcm",
        "TLS_Bearer_robotics_lab",
    ],
    "governance_doc_paths": [d["ruta"] for d in GOVERNANCE_DOCUMENTATION],
    "critical_env_var_names": list(CRITICAL_ENV_VARS),
}


def get_admin_general_playbook() -> Dict[str, Any]:
    """Deepcopy del playbook + metadatos extendidos (sin secretos)."""
    out = copy.deepcopy(ADMIN_GENERAL_PLAYBOOK)
    out["encryption_stack_detail"] = copy.deepcopy(list(ENCRYPTION_STACK))
    out["governance_docs_meta"] = copy.deepcopy(list(GOVERNANCE_DOCUMENTATION))
    out["jerarquia_crypto"] = (
        "Prod: Opción A *_FILE (Docker secrets) o B VAULT_ADDR+VAULT_TOKEN_FILE (vault.py); no Opción C .env plano | "
        "Nivel 0: ADMIN_MASTER_KEY / *_FILE → admin_master_layer | "
        "Nivel 1: CASTUO_ADMIN_GENERAL_BEARER / *_FILE → admin_general | "
        "Nivel 2: CASTUO_ROBOTICS_LAB_BEARER_TOKEN / *_FILE → lab HTTP | "
        "Nivel 3: GAIA_CHAIN_PRIVATE_KEY / *_FILE → on-chain (opt-in)"
    )
    out["critical_hardening_checks"] = copy.deepcopy(dict(CRITICAL_HARDENING_CHECKS))
    return out
