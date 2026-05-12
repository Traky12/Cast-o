# backend/api/services/emergency.py
"""Procedimientos de emergencia y notificación a autoridades. EU/OSS."""
from __future__ import annotations

import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from .key_rotation import KeyRotationService
except ImportError:
    from backend.api.services.key_rotation import KeyRotationService

try:
    from .gaiachain import GaiaChainService
except ImportError:
    from backend.api.services.gaiachain import GaiaChainService


def _audit_log(event_type: str, data: Dict[str, Any], compliance: Dict[str, Any]) -> None:
    try:
        from backend.api.security.audit import audit_logger
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(
                    audit_logger.log_event(request=None, event_type=event_type, data=data, compliance=compliance)
                )
            else:
                loop.run_until_complete(
                    audit_logger.log_event(request=None, event_type=event_type, data=data, compliance=compliance)
                )
        except RuntimeError:
            asyncio.run(
                audit_logger.log_event(request=None, event_type=event_type, data=data, compliance=compliance)
            )
    except Exception as e:
        logger.debug("Audit emergency: %s", e)


class EmergencyService:
    def __init__(self) -> None:
        self.key_rotation = KeyRotationService()
        self.gaiachain = GaiaChainService()
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.castuo-system.eu")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.alert_emails = {
            "aepd": os.getenv("AEPD_EMAIL", "incidencias@aepd.es"),
            "junta_extremadura": os.getenv("JUNTA_EMAIL", "seguridad@juntaex.es"),
            "security_team": os.getenv("SECURITY_TEAM_EMAIL", "security@castuo-system.eu"),
        }

    def seal_vault(self) -> Dict[str, Any]:
        return self.key_rotation.emergency_seal()

    def unseal_vault(self, shares: List[str]) -> Dict[str, Any]:
        return self.key_rotation.emergency_unseal(shares)

    def rotate_master_key(self, new_shares: List[str]) -> Dict[str, Any]:
        """Rota la clave maestra (rekey). Requiere 3 de 5 shares para completar."""
        if not self.key_rotation.client:
            return {"success": False, "message": "Vault no configurado"}
        try:
            init_r = self.key_rotation.client.sys.rekey_init(key_shares=5, key_threshold=3)
            if not init_r.get("started"):
                return {"success": False, "message": "Rekey no iniciado"}
            for share in new_shares[:3]:
                self.key_rotation.client.sys.rekey_update(share)
            tx = self.gaiachain.register_event_sync(
                token_id=0,
                action_type="master_key_rotation",
                status="completed",
                ipfs_cid="",
                norms=["ISO_27001:A.10.1.1", "GDPR:Art.32"],
                legal_basis={"description": "Rotación clave maestra (3/5 custodios)"},
            )
            _audit_log("master_key_rotation", {"tx_hash": tx}, {"iso_27001": ["A.10.1.1"], "gdpr": ["Art.32"]})
            return {"success": True, "tx_hash": tx, "message": "Clave maestra rotada (3/5 shares para desbloquear)."}
        except Exception as e:
            logger.exception("rotate_master_key")
            return {"success": False, "message": str(e), "error": str(e)}

    def _norms_for_incident(self, incident_type: str) -> List[str]:
        m = {
            "data_breach": ["GDPR:Art.33", "GDPR:Art.34", "Ley_3_2023:Art.20", "ISO_27001:A.16.1.4"],
            "service_outage": ["ISO_27001:A.16.1.4", "ISO_27001:A.17.1.1"],
            "security_incident": ["GDPR:Art.32", "ISO_27001:A.16.1.4", "Ley_3_2023:Art.20"],
        }
        return m.get(incident_type, ["ISO_27001:A.16.1.4"])

    def _compliance_for_incident(self, incident_type: str) -> Dict[str, List[str]]:
        m = {
            "data_breach": {"gdpr": ["Art.33", "Art.34"], "iso_27001": ["A.16.1.4"], "ley_3_2023": ["Art.20"]},
            "service_outage": {"iso_27001": ["A.16.1.4", "A.17.1.1"]},
            "security_incident": {"gdpr": ["Art.32"], "iso_27001": ["A.16.1.4"], "ley_3_2023": ["Art.20"]},
        }
        return m.get(incident_type, {"iso_27001": ["A.16.1.4"]})

    def notify_authorities(self, incident_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        try:
            tx_hash = self.gaiachain.register_event_sync(
                token_id=0,
                action_type=f"emergency_notification_{incident_type}",
                status="completed",
                ipfs_cid="",
                norms=self._norms_for_incident(incident_type),
                legal_basis={"description": f"Notificación emergencia {incident_type}", "details": details},
            )
            if incident_type == "data_breach":
                self._notify_data_breach(details, tx_hash)
            elif incident_type == "service_outage":
                self._notify_service_outage(details, tx_hash)
            else:
                self._notify_security_incident(details, tx_hash)
            _audit_log(
                f"emergency_notification_{incident_type}",
                {"tx_hash": tx_hash, "incident_type": incident_type, "details": details},
                self._compliance_for_incident(incident_type),
            )
            return {
                "success": True,
                "tx_hash": tx_hash,
                "message": f"Notificaciones enviadas para {incident_type}",
                "notified_authorities": list(self.alert_emails.keys()),
            }
        except Exception as e:
            logger.exception("notify_authorities")
            return {"success": False, "message": str(e), "error": str(e)}

    def _notify_data_breach(self, details: Dict[str, Any], tx_hash: str) -> None:
        ts = details.get("timestamp", datetime.now(timezone.utc).isoformat())
        body_aepd = (
            f"Notificación brecha de datos (GDPR Art. 33). Fecha: {ts}. "
            f"Tipo: {details.get('type', 'N/A')}. Sistemas: {details.get('affected_systems', [])}. "
            f"Medidas: {details.get('mitigation_measures', [])}. TX: {tx_hash}"
        )
        body_junta = (
            f"Incidente Ley 3/2023 Art. 20. Fecha: {ts}. "
            f"Datos afectados: {details.get('compromised_data', 'N/A')}. TX: {tx_hash}"
        )
        self._send_email(self.alert_emails["aepd"], f"[CASTÚO-SYSTEM] Brecha datos GDPR - {tx_hash[:16]}", body_aepd)
        self._send_email(self.alert_emails["junta_extremadura"], f"[CASTÚO-SYSTEM] Incidente Ley 3/2023 - {tx_hash[:16]}", body_junta)

    def _notify_service_outage(self, details: Dict[str, Any], tx_hash: str) -> None:
        body = (
            f"Interrupción servicio. Servicio: {details.get('service', 'N/A')}. "
            f"Inicio: {details.get('start_time', 'N/A')}. Impacto: {details.get('impact', 'N/A')}. TX: {tx_hash}"
        )
        self._send_email(self.alert_emails["security_team"], f"[CASTÚO-SYSTEM] Interrupción - {tx_hash[:16]}", body)

    def _notify_security_incident(self, details: Dict[str, Any], tx_hash: str) -> None:
        body = (
            f"Incidente seguridad. Tipo: {details.get('type', 'N/A')}. "
            f"Gravedad: {details.get('severity', 'Alta')}. TX: {tx_hash}"
        )
        self._send_email(self.alert_emails["security_team"], f"[CASTÚO-SYSTEM] Seguridad - {tx_hash[:16]}", body)

    def _send_email(self, to: str, subject: str, body: str) -> None:
        if not all([self.smtp_server, self.smtp_user, self.smtp_password]):
            logger.warning("SMTP no configurado, email no enviado")
            return
        msg = MIMEMultipart()
        msg["From"] = self.smtp_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            logger.info("Email enviado a %s", to)
        except Exception as e:
            logger.error("Error enviando email: %s", e)

    def generate_emergency_report(self, incident_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        tx_hash = self.gaiachain.register_event_sync(
            token_id=0,
            action_type=f"emergency_report_{incident_type}",
            status="generated",
            ipfs_cid="",
            norms=self._norms_for_incident(incident_type),
            legal_basis={"description": f"Informe emergencia {incident_type}", "details": details},
        )
        _audit_log(
            f"emergency_report_{incident_type}",
            {"report_id": tx_hash, "incident_type": incident_type, "details": details},
            self._compliance_for_incident(incident_type),
        )
        report = {
            "metadata": {
                "incident_type": incident_type,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "generated_by": "CASTÚO-SYSTEM™ Emergency Service",
                "compliance": self._compliance_for_incident(incident_type),
            },
            "details": details,
            "actions_taken": [{"action": "Registro en GaiaChain y auditoría", "timestamp": datetime.now(timezone.utc).isoformat(), "evidence": tx_hash}],
            "evidence": {"gaiachain_tx": tx_hash, "audit_logs": [], "affected_systems": details.get("affected_systems", [])},
        }
        if incident_type in ("data_breach", "security_incident"):
            nr = self.notify_authorities(incident_type, details)
            if nr.get("success"):
                report["notifications"] = [{"authority": a, "status": "sent"} for a in nr.get("notified_authorities", [])]
                report["actions_taken"].append({"action": "Notificación a autoridades", "details": nr})
        return report

    def get_emergency_procedures(self) -> Dict[str, Any]:
        return {
            "data_breach": {
                "title": "Procedimiento para Brecha de Datos (GDPR Art. 33)",
                "steps": [
                    {"title": "Contención Inmediata", "actions": ["Aislar sistemas", "Revocar tokens", "Deshabilitar cuentas"], "responsible": "Equipo de Seguridad", "timeframe": "<1h"},
                    {"title": "Investigación", "actions": ["Analizar logs", "Identificar vectores", "Datos comprometidos"], "responsible": "Security Officer", "timeframe": "<6h"},
                    {"title": "Notificación", "actions": ["AEPD <72h", "Junta <24h", "Afectados si riesgo alto"], "responsible": "DPO", "timeframe": "Según normativa"},
                    {"title": "Recuperación", "actions": ["Restaurar backups", "Rotar claves", "Parches"], "responsible": "Equipo Técnico", "timeframe": "<48h"},
                ],
                "compliance": {"gdpr": ["Art.33", "Art.34"], "ley_3_2023": ["Art.20"], "iso_27001": ["A.16.1.4", "A.16.1.5"]},
                "evidence_requirements": ["Registro GaiaChain", "Logs Wazuh", "Informe lecciones aprendidas"],
            },
            "service_outage": {
                "title": "Procedimiento para Interrupción del Servicio",
                "steps": [
                    {"title": "Evaluación", "actions": ["Alcance", "Sistemas afectados", "ETR"], "responsible": "Operaciones", "timeframe": "<30 min"},
                    {"title": "Comunicación", "actions": ["Notificar usuarios", "Status page", "Interno"], "responsible": "Soporte", "timeframe": "<1h"},
                    {"title": "Recuperación", "actions": ["Contingencia", "Backups si aplica", "Integridad"], "responsible": "Equipo Técnico", "timeframe": "Según ETR"},
                ],
                "compliance": {"iso_27001": ["A.16.1.4", "A.17.1.1", "A.17.1.2"]},
                "evidence_requirements": ["Tiempo inactividad", "Logs recuperación", "Post-mortem"],
            },
            "security_incident": {
                "title": "Procedimiento para Incidente de Seguridad",
                "steps": [
                    {"title": "Detección y Contención", "actions": ["Confirmar incidente", "Aislar sistemas", "Preservar evidencias"], "responsible": "Seguridad", "timeframe": "Inmediato"},
                    {"title": "Análisis y Erradicación", "actions": ["Causa raíz", "Eliminar acceso no autorizado", "Parches"], "responsible": "Security Officer", "timeframe": "<24h"},
                    {"title": "Recuperación", "actions": ["Restaurar a estado seguro", "Verificar vectores", "Monitorizar"], "responsible": "Equipo Técnico", "timeframe": "<48h"},
                ],
                "compliance": {"gdpr": ["Art.32"], "ley_3_2023": ["Art.20"], "iso_27001": ["A.16.1.4", "A.16.1.5", "A.16.1.6"]},
                "evidence_requirements": ["Logs auditoría", "Informe forense", "Erradicación"],
            },
        }
