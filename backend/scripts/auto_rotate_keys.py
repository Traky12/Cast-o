#!/usr/bin/env python3
# backend/scripts/auto_rotate_keys.py
# Servicio de rotación automática de claves. EU/OSS.
# Ejecutar desde raíz del repo: python backend/scripts/auto_rotate_keys.py

import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

# Permitir imports del backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

try:
    import schedule
except ImportError:
    schedule = None
    logger.warning("Instale 'schedule' para rotación programada: pip install schedule")

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    _HAS_SLACK = True
except ImportError:
    _HAS_SLACK = False


def _send_slack(message: str, severity: str = "good", context: dict = None) -> None:
    if not _HAS_SLACK or not os.getenv("SLACK_API_TOKEN"):
        return
    try:
        client = WebClient(token=os.getenv("SLACK_API_TOKEN"))
        channel = os.getenv("SLACK_ALERT_CHANNEL", "#security-alerts")
        emoji = "white_check_mark" if severity == "good" else "warning" if severity == "warning" else "x"
        text = f":{emoji}: *Rotación de claves*: {message}"
        if context:
            text += "\n" + " | ".join(f"{k}: {v}" for k, v in (context or {}).items())
        client.chat_postMessage(channel=channel, text=text)
    except Exception as e:
        logger.debug("Slack error: %s", e)


def rotate_keys_job() -> None:
    if not schedule:
        return
    try:
        from backend.api.services.key_rotation import KeyRotationService
    except ImportError:
        from api.services.key_rotation import KeyRotationService
    logger.info("Iniciando rotación automática de claves...")
    svc = KeyRotationService()
    results = svc.rotate_all_if_needed()
    for r in results:
        if r.get("success"):
            logger.info("OK %s (TX: %s)", r.get("message"), r.get("tx_hash"))
            _send_slack(r.get("message", ""), "good", {"tx_hash": r.get("tx_hash", "")})
        else:
            logger.error("Error: %s", r.get("message"))
            _send_slack(r.get("message", ""), "danger")


def check_rotation_status() -> None:
    try:
        from backend.api.services.key_rotation import KeyRotationService
    except ImportError:
        from api.services.key_rotation import KeyRotationService
    svc = KeyRotationService()
    status = svc.get_rotation_status()
    overdue = []
    for key_name, cfg in status.items():
        if cfg.get("last_rotated") == "Nunca":
            overdue.append(key_name)
            continue
        try:
            last = cfg.get("last_rotated", "")
            if not last:
                continue
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            days = 90
            for k, c in svc.rotation_schedule.items():
                if c.get("pqc_key") == cfg.get("pqc_key") or k == key_name:
                    days = c.get("days", 90)
                    break
            next_rot = last_dt + timedelta(days=days)
            if datetime.now(timezone.utc).replace(tzinfo=None) >= (next_rot.replace(tzinfo=None) if next_rot.tzinfo else next_rot):
                overdue.append(key_name)
        except Exception as e:
            logger.debug("Parse rotation date: %s", e)
            overdue.append(key_name)
    if overdue:
        msg = "Claves con rotación atrasada: " + ", ".join(overdue)
        logger.warning(msg)
        _send_slack(msg, "warning", {"keys": ", ".join(overdue)})


def health_check() -> None:
    try:
        from backend.api.services.key_rotation import KeyRotationService
        from backend.api.services.gaiachain import GaiaChainService
    except ImportError:
        from api.services.key_rotation import KeyRotationService
        from api.services.gaiachain import GaiaChainService
    try:
        svc = KeyRotationService()
        status = svc.get_rotation_status()
        logger.info("Health check: %s claves monitorizadas", len(status))
        if svc.client and not svc.client.is_authenticated():
            raise RuntimeError("Vault no autenticado")
        gaia = GaiaChainService()
        if not gaia.ping():
            raise RuntimeError("GaiaChain no disponible")
        _send_slack("Health check rotación: OK", "good")
    except Exception as e:
        logger.error("Health check fallido: %s", e)
        _send_slack("Health check fallido: " + str(e), "danger")


def run_scheduler() -> None:
    if not schedule:
        logger.warning("Sin 'schedule', no se programa rotación. Instale: pip install schedule")
        return
    schedule.every().day.at("03:00").do(rotate_keys_job)
    schedule.every(6).hours.do(check_rotation_status)
    interval = int(os.getenv("HEALTH_CHECK_INTERVAL", "3600"))
    schedule.every(interval).seconds.do(health_check)
    logger.info("Planificador de rotación iniciado (diario 03:00, estado cada 6h, health cada %ss)", interval)
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
