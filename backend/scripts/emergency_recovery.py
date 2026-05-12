#!/usr/bin/env python3
# backend/scripts/emergency_recovery.py
# Herramienta CLI de recuperación de emergencia. EU/OSS.
# Uso: python backend/scripts/emergency_recovery.py <seal|unseal|rotate-mk|notify|generate-report|procedures> [args]

import argparse
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _get_emergency_service():
    try:
        from backend.api.services.emergency import EmergencyService
    except ImportError:
        from api.services.emergency import EmergencyService
    return EmergencyService()


def cmd_seal(_):
    s = _get_emergency_service()
    r = s.seal_vault()
    if r.get("success"):
        logger.info("Vault sellado. TX: %s. Se requieren 3 shares para desbloquear.", r.get("tx_hash"))
    else:
        logger.error("Error: %s", r.get("message"))
        sys.exit(1)


def cmd_unseal(args):
    if len(args.shares) < 3:
        logger.error("Se requieren al menos 3 shares Shamir")
        sys.exit(1)
    s = _get_emergency_service()
    r = s.unseal_vault(args.shares)
    if r.get("success"):
        logger.info("Vault desbloqueado. TX: %s", r.get("tx_hash"))
    else:
        logger.error("Error: %s", r.get("message"))
        sys.exit(1)


def cmd_rotate_mk(args):
    if len(args.shares) != 5:
        logger.error("Se requieren exactamente 5 shares para rotar la clave maestra")
        sys.exit(1)
    s = _get_emergency_service()
    r = s.rotate_master_key(args.shares)
    if r.get("success"):
        logger.info("Clave maestra rotada. TX: %s. Guarde las nuevas shares.", r.get("tx_hash"))
    else:
        logger.error("Error: %s", r.get("message"))
        sys.exit(1)


def cmd_notify(args):
    details = {}
    if args.details:
        try:
            details = json.loads(args.details) if isinstance(args.details, str) else args.details
        except json.JSONDecodeError:
            logger.error("--details debe ser JSON válido")
            sys.exit(1)
    s = _get_emergency_service()
    r = s.notify_authorities(args.incident_type, details)
    if r.get("success"):
        logger.info("Notificaciones enviadas para %s. TX: %s", args.incident_type, r.get("tx_hash"))
    else:
        logger.error("Error: %s", r.get("message"))
        sys.exit(1)


def cmd_generate_report(args):
    details = {}
    if args.details:
        try:
            details = json.loads(args.details) if isinstance(args.details, str) else args.details
        except json.JSONDecodeError:
            logger.error("--details debe ser JSON válido")
            sys.exit(1)
    s = _get_emergency_service()
    report = s.generate_emergency_report(args.incident_type, details)
    out = args.output or "emergency_report.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info("Informe guardado: %s. TX: %s", out, report.get("evidence", {}).get("gaiachain_tx", ""))


def cmd_procedures(_):
    s = _get_emergency_service()
    procs = s.get_emergency_procedures()
    for incident_type, proc in procs.items():
        print("\n%s: %s" % (incident_type, proc.get("title", "")))
        print("  Cumplimiento:", proc.get("compliance", {}))
        for i, step in enumerate(proc.get("steps", []), 1):
            print("  %d. %s - %s (%s)" % (i, step.get("title"), step.get("responsible"), step.get("timeframe")))


def main():
    parser = argparse.ArgumentParser(description="Recuperación de emergencia CASTÚO-SYSTEM™")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("seal", help="Sellar Vault").set_defaults(func=cmd_seal)
    u = sub.add_parser("unseal", help="Desbloquear Vault con 3+ shares")
    u.add_argument("shares", nargs="+", help="Shares Shamir")
    u.set_defaults(func=cmd_unseal)

    r = sub.add_parser("rotate-mk", help="Rotar clave maestra (5 shares)")
    r.add_argument("shares", nargs=5, help="5 shares nuevas")
    r.set_defaults(func=cmd_rotate_mk)

    n = sub.add_parser("notify", help="Notificar incidente a autoridades")
    n.add_argument("incident_type", choices=["data_breach", "service_outage", "security_incident"])
    n.add_argument("--details", default="{}", help="JSON con detalles")
    n.set_defaults(func=cmd_notify)

    g = sub.add_parser("generate-report", help="Generar informe de emergencia")
    g.add_argument("incident_type", choices=["data_breach", "service_outage", "security_incident"])
    g.add_argument("--details", default="{}", help="JSON con detalles")
    g.add_argument("--output", default="emergency_report.json", help="Archivo de salida")
    g.set_defaults(func=cmd_generate_report)

    sub.add_parser("procedures", help="Listar procedimientos de emergencia").set_defaults(func=cmd_procedures)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
