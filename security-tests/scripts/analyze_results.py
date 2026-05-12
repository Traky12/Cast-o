#!/usr/bin/env python3
import json
import logging
import os
from pathlib import Path


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_latest_json_report(reports_dir: Path) -> Path | None:
    json_files = sorted(reports_dir.glob("security_scan_*.json"))
    return json_files[-1] if json_files else None


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    reports_dir = root / "security-tests" / "reports"
    if not reports_dir.exists():
        logger.error("Directorio de informes no existe: %s", reports_dir)
        raise SystemExit(1)

    report_path = find_latest_json_report(reports_dir)
    if not report_path:
        logger.error("No se encontraron informes JSON en %s", reports_dir)
        raise SystemExit(1)

    logger.info("Analizando informe: %s", report_path)
    data = json.loads(report_path.read_text(encoding="utf-8"))
    comp = data.get("compliance_status", {})
    overall = comp.get("overall", True)
    reason = comp.get("reason", "")
    counts = comp.get("counts", {})
    logger.info("Vulnerabilidades por severidad: %s", counts)

    if not overall:
        logger.error("Escaneo NO cumple umbrales: %s", reason)
        from security_tests.zap.zap_utils import ZAPUtils  # type: ignore

        utils = ZAPUtils()
        utils.send_slack_alert(
            "Escaneo de seguridad NO cumple umbrales",
            severity="critical",
            context={"reason": reason, "report": str(report_path)},
        )
        raise SystemExit(1)

    logger.info("Escaneo cumple umbrales de seguridad.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()

