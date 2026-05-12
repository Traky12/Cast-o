#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera config/castuo_enterprise_eu.json (blueprint organitzativo + claudecode EU)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "config" / "castuo_enterprise_eu.json"

DATA: dict = {
    "claudecode_eu": {
        "profile": "EU",
        "data_sovereignty": (
            "Blueprint CASTÚO: datos operativos y facturación bajo control del operador en UE; "
            "las rutas /subscription/ai/* no sustituyen firma humana en cobros ni contratos."
        ),
        "code_assistant_policy": (
            "Claude Code y asistentes alineados a política interna EU-first cuando aplique soberanía del dato."
        ),
    },
    "empresa": {
        "nombre": "CASTÚO-SYSTEM S.L.",
        "mision": (
            "Proveer soluciones de agricultura inteligente con trazabilidad y monetización transparente"
        ),
        "vision": (
            "Ser referencia en agritech con facturación automática y gestión de clientes soberana"
        ),
        "valores": ["Transparencia", "Sostenibilidad", "Innovación", "Excelencia Operativa"],
    },
    "estructura_organizacional": {
        "consejo_directivo": {
            "presidente": "Gregorio Jiménez Bodes",
            "responsabilidades": [
                "Definición estratégica",
                "Aprobación de políticas de monetización",
                "Relación con stakeholders",
            ],
        },
        "direccion_ejecutiva": {
            "ceo": "Gregorio Jiménez Bodes",
            "cto": {
                "nombre": "To be defined",
                "responsabilidades": [
                    "Arquitectura técnica",
                    "Integración con sistemas externos",
                    "Seguridad de datos",
                ],
            },
            "cfo": {
                "nombre": "To be defined",
                "responsabilidades": [
                    "Gestión financiera",
                    "Facturación y cobros",
                ],
            },
        },
        "departamentos": [
            {
                "nombre": "Operaciones y Monetización",
                "equipo": [
                    {
                        "rol": "Gestor de Cuentas",
                        "herramientas": [
                            "POST /water/ctaex/subscription/register",
                            "GET /water/ctaex/subscription/usage-report",
                            "scripts/migrate_clients.py",
                        ],
                    },
                    {
                        "rol": "Especialista en Facturación",
                        "herramientas": [
                            "POST /water/ctaex/subscription/generate-invoices",
                            "POST /water/ctaex/subscription/send-invoice",
                            "scripts/send_invoices.py",
                            "scripts/send_reminders.py",
                        ],
                    },
                    {
                        "rol": "Analista de Datos",
                        "herramientas": [
                            "scripts/monitoring.py",
                            "GET /water/ctaex/subscription/certification",
                            "scripts/monthly_report.py",
                            "scripts/certification.py",
                        ],
                    },
                ],
            },
            {
                "nombre": "Tecnología y Desarrollo",
                "equipo": [
                    {
                        "rol": "Desarrollador Backend",
                        "herramientas": [
                            "backend/services/water_billing.py",
                            "backend/routers/water_ctaex.py",
                        ],
                    },
                    {
                        "rol": "Especialista en Automatización",
                        "herramientas": [
                            "scripts/complete_monthly_billing.sh",
                            "Docker Compose",
                        ],
                    },
                ],
            },
        ],
    },
    "roles_ia_endpoints": {
        "gestor_cuentas": "POST /water/ctaex/subscription/ai/register",
        "analista_financiero": "GET /water/ctaex/subscription/ai/monitoring",
        "soporte_tecnico": "GET /water/ctaex/subscription/ai/health",
        "blueprint_empresa": "GET /water/ctaex/subscription/ai/enterprise-blueprint",
    },
    "seguridad": {
        "politicas": [
            "No almacenar API keys en claro en SQLite de facturación (solo hash)",
            "X-AI-KEY y AI_INTEGRATION_KEY con rotación trimestral recomendada",
        ],
    },
}


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(DATA, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Escrito", OUT)


if __name__ == "__main__":
    main()
