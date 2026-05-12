import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict

import requests
from zapv2 import ZAPv2

from .zap_utils import ZAPUtils


logger = logging.getLogger(__name__)


class APIScanner:
    def __init__(self, config_path: str = "security-tests/config/zap_config.yaml") -> None:
        self.utils = ZAPUtils(config_path)
        self.zap: ZAPv2 = self.utils.initialize_zap()
        self.scan_id = str(uuid.uuid4())
        self.scan_config = self.utils.get_scan_config("api")

    def run_scan(self) -> Dict[str, Any]:
        logger.info("Iniciando escaneo API (ID=%s)", self.scan_id)
        start_time = datetime.utcnow().isoformat() + "Z"
        target_url = self.scan_config["target_url"]
        try:
            openapi_url = self.scan_config["openapi_spec"]
            logger.info("Cargando OpenAPI: %s", openapi_url)
            spec_resp = requests.get(openapi_url, timeout=20)
            spec_resp.raise_for_status()
            openapi_spec = spec_resp.json()

            context_name = f"APIScan_{self.scan_id}"
            context_id = self.zap.context.new_context(context_name)
            for path in openapi_spec.get("paths", {}).keys():
                full = f"{target_url}{path}"
                self.zap.context.include_in_context(context_name, f"{full}.*")

            # Spider
            spider_id = self.zap.spider.scan(target_url, recurse=True)
            while int(self.zap.spider.status(spider_id)) < 100:
                logger.info("Spider API progreso: %s%%", self.zap.spider.status(spider_id))
                time.sleep(5)

            ascan_id = self.zap.ascan.scan(target_url, recurse=True, inscopeonly=True)
            while int(self.zap.ascan.status(ascan_id)) < 100:
                logger.info("Active scan API progreso: %s%%", self.zap.ascan.status(ascan_id))
                time.sleep(10)

            alerts = self.zap.core.alerts(baseurl=target_url, start=0, count=1000)
            vulns = self.utils.enrich_with_catalog(alerts, scan_type="api", scan_id=self.scan_id)
            compliance = self.utils.check_compliance_thresholds(vulns)

            scan_result: Dict[str, Any] = {
                "scan_id": self.scan_id,
                "scan_type": "api",
                "target_url": target_url,
                "openapi_spec": openapi_url,
                "start_time": start_time,
                "end_time": datetime.utcnow().isoformat() + "Z",
                "vulnerabilities": vulns,
                "vulnerabilities_found": len(vulns),
                "vulnerabilities_by_severity": {
                    "critical": sum(1 for v in vulns if v["severity"] == "critical"),
                    "high": sum(1 for v in vulns if v["severity"] == "high"),
                    "medium": sum(1 for v in vulns if v["severity"] == "medium"),
                    "low": sum(1 for v in vulns if v["severity"] == "low"),
                },
                "compliance_status": compliance,
                "technical_details": {
                    "spider_scan_id": spider_id,
                    "active_scan_id": ascan_id,
                    "context_id": context_id,
                    "zap_version": self.zap.core.version,
                    "openapi_paths": list(openapi_spec.get("paths", {}).keys()),
                },
            }
            tx = self.utils.register_scan_result_in_gaiachain(scan_result)
            if tx:
                scan_result["gaiachain_tx"] = tx
            report_path = self.utils.generate_report(scan_result, fmt="json")
            scan_result["report_path"] = report_path

            critical = [v for v in vulns if v["severity"] == "critical"]
            if critical:
                for v in critical:
                    self.utils.send_slack_alert(
                        f"Vulnerabilidad CRÍTICA en API: {v['name']}",
                        severity="critical",
                        context={"url": v.get("url", ""), "cwe": v.get("cwe", "")},
                    )

            logger.info("Escaneo API completado: %s vulns", len(vulns))
            return scan_result
        except Exception as exc:
            logger.error("Error en escaneo API: %s", exc)
            return {
                "scan_id": self.scan_id,
                "scan_type": "api",
                "status": "failed",
                "error": str(exc),
                "start_time": start_time,
                "end_time": datetime.utcnow().isoformat() + "Z",
            }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    scanner = APIScanner()
    result = scanner.run_scan()
    if result.get("status") == "failed":
        raise SystemExit(1)
    raise SystemExit(0)

