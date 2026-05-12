#!/usr/bin/env python3
"""
Inventario de evidencias en el clon (protocolo legal v2.4, UE + Extremadura / OSS).

No constituye auditoria legal ni certificacion ISO/RGPD/eIDAS; solo presencia de ficheros.

No importa el paquete backend (PYTHONPATH / CI estables).

GaiaChain en codigo real:
  - register_event_in_chain(event_data) en backend/api/services/gaiachain_service.py
    requiere tokenId (int), action (str), status (str), details/compliance opcionales.
  - POST /api/audit/register-event en backend/api/routes/audit.py (JWT Keycloak, rol dpo/admin).
  - GaiaChainAuditClient en backend/utils/gaia_chain.py -> get_consent_status (otra capa).

Uso:
    python scripts/audit/audit_repo_evidence_check.py
    python scripts/audit/audit_repo_evidence_check.py --json
    python scripts/audit/audit_repo_evidence_check.py --post-register-api

    No hay flags --caae, --pac, --market ni --iot: el inventario corre completo siempre.
        Requiere CASTUO_AUDIT_API_URL y CASTUO_AUDIT_API_TOKEN (Bearer).
        Opcional: CASTUO_AUDIT_TOKEN_ID (default 1).

Salida:
    0 — rutas requeridas presentes
    1 — falta alguna ruta
    2 — error de ejecucion
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Lista alineada a PROTOCOLO + marcos CAAE/PAC/mercado + IoT docs/iot (rev. 2026-03-21)
REQUIRED_EVIDENCE: dict[str, list[tuple[str, str]]] = {
    "legal": [
        ("DPIA", "docs/legal/DPIA-CASTUO-SYSTEM.md"),
        ("Prontuario legal 90 dias", "docs/legal/PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md"),
        ("Protocolo auditoria interna", "docs/legal/PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md"),
        ("Manifiesto CASTUO 1.0", "docs/MANIFESTO-CASTUO-SYSTEM-1-0.md"),
        ("Plantilla FacturaE (XML)", "templates/legal/facturae.xml"),
        ("Informes auditoria personalizados (doc)", "docs/legal/INFORMES-AUDITORIA-PERSONALIZADOS.md"),
        ("Prontuario maestro auditoria interna", "docs/legal/PRONTUARIO-MAESTRO-AUDITORIA-INTERNA.md"),
        ("Umbrales climaticos Extremadura (doc)", "docs/legal/UMBRALES-CLIMATICOS-EXTREMADURA.md"),
        (
            "Roadmap integraciones SIGPAC GaiaChain AEMET",
            "docs/legal/ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md",
        ),
        (
            "Plan integracion reforzado Castuo 6",
            "docs/legal/PLAN-INTEGRACION-REFORZADO-CASTUO-6.md",
        ),
        (
            "Diseno integral ecosistema Castuo 6",
            "docs/legal/DISENO-INTEGRAL-ECOSISTEMA-CASTUO-6.md",
        ),
        (
            "Prontuario maestro encriptacion roles v2.5",
            "docs/legal/PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md",
        ),
        (
            "Analisis critico excelencia v2.5",
            "docs/legal/ANALISIS-CRITICO-EXCELENCIA-V2.5.md",
        ),
        (
            "Prontuario maestro consulta critica Castuo",
            "docs/legal/PRONTUARIO-MAESTRO-CONSULTA-CRITICA-CASTUO-SYSTEM.md",
        ),
        (
            "Plan excelencia integral Castuo System",
            "docs/legal/PLAN-EXCELENCIA-INTEGRAL-CASTUO-SYSTEM.md",
        ),
        (
            "Prontuario debilidades potencial soberania EU",
            "docs/legal/PRONTUARIO-MAESTRO-DEBILIDADES-POTENCIAL-SOBERANIA-EU.md",
        ),
        ("Contrato CTAEX TRL10", "docs/legal/TRL10/contrato_ctaex_final_20260320.md"),
        (
            "Registro actividades tratamiento (generado)",
            "compliance_docs/generated/02.01.01_Registro_Actividades_Tratamiento.md",
        ),
    ],
    "extremadura_territorio": [
        ("Marco SIGPAC-AEMPS (honestidad repo)", "docs/legal/SIGPAC-AEMPS-MARCO-REPOSITORIO.md"),
        (
            "Marco SIGPAC avanzado + clima Extremadura (honestidad repo)",
            "docs/legal/SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md",
        ),
        ("Marco CAAE-PAC-mercado (honestidad repo)", "docs/legal/CAAE-PAC-MERCADO-MARCO-REPOSITORIO.md"),
        ("Anexo III confidencialidad (Extremadura)", "docs/legal/ANEXO-III-CONFIDENCIALIDAD-Y-PROTECCION-DATOS.md"),
        (
            "Procedimiento SIGPAC (generado)",
            "compliance_docs/generated/02.05.01_Procedimiento_SIGPAC_Extremadura.md",
        ),
        (
            "Gestion consentimientos Ley 3/2023 (generado)",
            "compliance_docs/generated/02.02.03_Gestion_Consentimientos_Ley_3_2023_Extremadura.md",
        ),
        ("Criterios PAC2040", "docs/funding/PAC2040-Criterios.md"),
        ("Traceability CIS calculator", "backend/traceability/cis_calculator.py"),
        ("Traceability cork models", "backend/traceability/cork_models.py"),
        ("EPCIS event model (addon)", "custom-addons/castu_system/models/epcis_event.py"),
        (
            "Grafana dashboard produccion integral",
            "castu-monitoring/grafana/dashboards/castuo_production_integral.json",
        ),
        (
            "Grafana dashboard AEMPS cannabis trials",
            "castu-monitoring/grafana/dashboards/aemps-cannabis-trials.json",
        ),
        ("Config umbrales clima Extremadura (YAML)", "config/extremadura_climate.yaml"),
    ],
    "iot_repo": [
        ("Marco IoT (honestidad repo)", "docs/iot/IOT-MARCO-REPOSITORIO.md"),
        ("MQTT handler (paquete iot/)", "iot/mqtt_handler.py"),
        ("Docker Compose MQTT", "iot/docker-compose.mqtt.yml"),
        ("Router FastAPI IoT", "backend/routers/iot.py"),
        ("API IoT (analisis / endpoints)", "iot/api_endpoints.py"),
    ],
    "integraciones_futuras_docs": [
        ("Requisitos futuros CAAE", "docs/legal/REQUISITOS-FUTUROS-CAAE.md"),
        ("Puntero CAAE en docs/iot", "docs/iot/REQUISITOS-CAAE.md"),
        ("Requisitos IoT futuro", "docs/iot/REQUISITOS-IOT.md"),
        ("Normas IoT referencia", "docs/iot/NORMATIVAS-IOT-REFERENCIA.md"),
        ("Netafim / riego futuro", "docs/iot/REQUISITOS-NETAFIM-FUTURO.md"),
        ("Marco CTAEX integracion (honestidad repo)", "docs/legal/CTAEX-INTEGRACION-MARCO-REPOSITORIO.md"),
    ],
    "technical": [
        ("Vegetal-Alloys (paquete)", "backend/vegetal_alloys/__init__.py"),
        ("Chemaxon integration", "backend/vegetal_alloys/chemaxon_integration.py"),
        ("GaiaChain GaiaChainAuditClient", "backend/utils/gaia_chain.py"),
        ("Integracion GaiaChain compliance", "backend/compliance/gaiachain_integration.py"),
        ("Servicio registro eventos cadena", "backend/api/services/gaiachain_service.py"),
        ("Validador GeoJSON SIGPAC local (GDAL opcional)", "backend/integrations/sigpac_validator.py"),
        ("Placeholder cliente SIGPAC remoto (sin URL)", "backend/integrations/sigpac_remote_placeholder.py"),
        ("Requisitos opcionales GDAL SIGPAC", "backend/integrations/requirements-sigpac-gdal.txt"),
        ("Cargador umbrales clima Extremadura", "backend/ctaex/climate_config.py"),
        ("Criptografia post-cuantica (Kyber + AES)", "backend/security/pq_crypto.py"),
        ("Manifiesto despliegue K8s (sabionda-core)", "k8s/sabionda-core/deployment.yaml"),
        ("Agentes autonomos (paquete)", "backend/agents_autonomous/__init__.py"),
        ("Contrato CASTUO_System.sol", "contracts/CASTUO_System.sol"),
        ("Doc plantilla GaiaChain", "docs/blockchain/gaiachain-deployment.md"),
    ],
    "compliance": [
        ("Este script de auditoria", "scripts/audit/audit_repo_evidence_check.py"),
        ("Tests SIGPAC validador local", "tests/integrations/test_sigpac_validator.py"),
        ("Tests roadmap AEMET (mocks sin red)", "tests/integrations/test_aemet_integration.py"),
        ("Tests umbrales clima Extremadura", "tests/ctaex/test_climate_config.py"),
        ("Tests pq_crypto", "backend/security/tests/test_pq_crypto.py"),
        ("Script prueba GaiaChain", "scripts/test_gaia_chain.py"),
        ("Generador informe compliance", "backend/scripts/generate_compliance_report.py"),
        ("Generador docs compliance", "compliance_docs/scripts/generate_compliance_docs.py"),
        (
            "Declaracion aplicabilidad ISO27001 (generado)",
            "compliance_docs/generated/02.04.01_Declaracion_Aplicabilidad_ISO27001.md",
        ),
        ("OPA compliance.rego", "monitoring/opa/policies/castuo/compliance.rego"),
        ("Rutas API audit (register_audit_event)", "backend/api/routes/audit.py"),
        ("AEMPS compliance (modulo)", "compliance/aemps_compliance.py"),
        ("Generador informes auditoria Jinja2", "backend/reports/audit_generator.py"),
        ("Plantilla informe AEMPS (Jinja2)", "templates/reports/aemps_audit.jinja2"),
    ],
    "ops_documentacion": [
        ("Plan 90 dias enterprise", "docs/ops/PLAN-90-DIAS-ENTERPRISE-EU-2026.md"),
        ("Prontuario excelencia sistema (analisis)", "docs/PRONTUARIO-MAESTRO-EXCELENCIA-SISTEMA-ANALISIS.md"),
        ("Prontuario 2040", "docs/PRONTUARIO-MAESTRO-CASTUO-SYSTEM-2040.md"),
        ("Guia despliegue", "docs/deployment/DEPLOYMENT_GUIDE.md"),
        ("Monitoring castu-monitoring", "castu-monitoring/README.md"),
        ("Prometheus config (stack local)", "castu-monitoring/prometheus/prometheus.yml"),
        ("Prometheus alert rules (kubernetes)", "kubernetes/prometheus/alert-rules.yaml"),
        ("Kubernetes security policies", "kubernetes/security-policies.yaml"),
        ("Security executive VSA PQC", "docs/security/CASTUO-SECURITY-VSA-PQC-EXECUTIVE.md"),
        ("Plantilla dashboard", "templates/dashboard.html"),
        ("Estaticos README", "static/README.md"),
        ("Doc dashboard y estaticos", "docs/ops/DASHBOARD-Y-ESTATICOS.md"),
        ("Register-SecurityEvent (PowerShell)", "scripts/Register-SecurityEvent.ps1"),
        ("Bootstrap Hetzner", "scripts/deploy/bootstrap-hetzner.sh"),
    ],
}


def _stat_entry(path: Path) -> dict[str, Any]:
    rel = str(path.relative_to(_REPO_ROOT))
    if not path.exists():
        return {"path": rel, "exists": False}
    if path.is_dir():
        return {"path": rel, "exists": True, "kind": "dir", "size": None}
    return {"path": rel, "exists": True, "kind": "file", "size": path.stat().st_size}


def check_evidence() -> dict[str, Any]:
    found: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for category, items in REQUIRED_EVIDENCE.items():
        for description, rel in items:
            full = _REPO_ROOT / rel
            st = _stat_entry(full)
            row = {"category": category, "description": description, **st}
            if st["exists"]:
                found.append(row)
            else:
                missing.append(row)

    status = "ok" if not missing else "missing_evidence"
    return {
        "status": status,
        "repo_root": str(_REPO_ROOT),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_version": "2.4",
        "inventory_revision": "2026-03-21",
        "territorio_note": (
            "Script = inventario de rutas. Sin APIs MAPA/AEMPS/CAAE/PAC/Netafim ficticias. "
            "SIGPAC: validacion local sigpac_validator.py + GDAL opcional; sin API REST MAPA ficticia. "
            "Marco docs/legal/SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md. "
            "Clima: config/extremadura_climate.yaml + climate_config.py; sin metricas ctaex_* Prometheus. "
            "CTAEX: router backend/routers/ctaex.py y contrato TRL10; backend/ctaex solo climate_config; sin api.ctaex.es/v2; "
            "marco docs/legal/CTAEX-INTEGRACION-MARCO-REPOSITORIO.md. "
            "Flags --caae/--pac/--market/--iot no existen; solo --json y --post-register-api. "
            "IoT: iot/ y backend/routers/iot.py; marcos en docs/iot/ y docs/legal/CAAE-PAC-MERCADO-MARCO-REPOSITORIO.md."
        ),
        "gaiachain_note": (
            "Inventario local: sin tx por defecto. Cadena: register_event_in_chain + "
            "POST /api/audit/register-event (JWT). Cliente utilidad: GaiaChainAuditClient.get_consent_status. "
            "Opcional: --post-register-api + CASTUO_AUDIT_API_URL + CASTUO_AUDIT_API_TOKEN."
        ),
        "summary": {
            "total_required": len(found) + len(missing),
            "present": len(found),
            "missing": len(missing),
        },
        "found": found,
        "missing": missing,
    }


def try_register_via_audit_api(results: dict[str, Any]) -> dict[str, Any]:
    """POST opcional; cuerpo compatible con register_event_in_chain (no inventar claves)."""
    if results.get("status") != "ok":
        return {"skipped": True, "reason": "evidence_incomplete"}

    base = (os.environ.get("CASTUO_AUDIT_API_URL") or "").strip()
    token = (os.environ.get("CASTUO_AUDIT_API_TOKEN") or "").strip()
    if not base or not token:
        return {
            "skipped": True,
            "reason": "set CASTUO_AUDIT_API_URL and CASTUO_AUDIT_API_TOKEN to post",
        }

    try:
        token_id = int(os.environ.get("CASTUO_AUDIT_TOKEN_ID") or "1")
    except ValueError:
        token_id = 1

    payload = {
        "tokenId": token_id,
        "action": "repository_evidence_check",
        "status": "ok",
        "details": {
            "script": "audit_repo_evidence_check.py",
            "protocol_version": results.get("protocol_version"),
            "present": results["summary"]["present"],
            "missing": results["summary"]["missing"],
            "timestamp_utc": results["timestamp_utc"],
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw) if raw else {}
        return {"skipped": False, "ok": True, "response": parsed}
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return {
            "skipped": False,
            "ok": False,
            "http_status": exc.code,
            "error": err_body or str(exc),
        }
    except Exception as exc:  # noqa: BLE001
        return {"skipped": False, "ok": False, "error": str(exc)}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true", help="Salida JSON")
    p.add_argument(
        "--post-register-api",
        action="store_true",
        help="Tras inventario OK, POST a CASTUO_AUDIT_API_URL (Bearer CASTUO_AUDIT_API_TOKEN)",
    )
    args = p.parse_args()
    try:
        results: dict[str, Any] = check_evidence()
        register_info: dict[str, Any] | None = None
        if args.post_register_api:
            register_info = try_register_via_audit_api(results)
            results["register_api"] = register_info

        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            ts = results["timestamp_utc"]
            ok = results["status"] == "ok"
            s = results["summary"]
            print("CASTUO / auditoria evidencias repo (v2.4 UE + territorio)")
            print("=" * 55)
            print(f"Raiz repo: {results['repo_root']}")
            print(f"UTC:       {ts}")
            print(f"Estado:    {'OK (todo presente)' if ok else 'FALTAN RUTAS'}")
            print(f"Presentes: {s['present']}/{s['total_required']}")
            print(f"Faltantes: {s['missing']}")
            print(f"Territorio: {results['territorio_note']}")
            print(f"GaiaChain: {results['gaiachain_note']}")
            if register_info is not None:
                if register_info.get("skipped"):
                    print(f"API audit: omitido — {register_info.get('reason')}")
                elif register_info.get("ok"):
                    print(f"API audit: OK — {register_info.get('response')}")
                else:
                    print(f"API audit: fallo — {register_info}", file=sys.stderr)
            if results["missing"]:
                print("\nFaltantes:")
                for item in results["missing"]:
                    print(f"  - [{item['category']}] {item['description']}: {item['path']}")
            print("\nPresentes:")
            for item in results["found"]:
                sz = item.get("size")
                szs = f"{sz} B" if sz is not None else "(dir)"
                print(f"  - [{item['category']}] {item['description']}: {item['path']} {szs}")
        return 0 if results["status"] == "ok" else 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error durante la auditoria: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
