# -*- coding: utf-8 -*-
"""
Integración CASTUO Academy con LMS (Moodle vía REST) y GaiaChain.
Matrícula, finalización de módulos, emisión y verificación de certificados.
"""
import logging
from typing import Any, Dict, Optional

import json
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


class CastuaLMS:
    """
    Cliente para Moodle REST (core_enrol_enrol_users, mod_scorm_*, tool_customcert_*).
    Registra eventos en GaiaChain: matrícula, módulo completado, certificado emitido.
    """

    def __init__(
        self,
        moodle_url: str = "https://academy.castu/system",
        token: str = "",
    ) -> None:
        self.moodle_url = moodle_url.rstrip("/")
        self.token = token
        self.blockchain = GaiaChainClient() if GaiaChainClient else None

    def _call_moodle(self, method: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Llamada a Moodle REST (webservice/rest/server.php)."""
        url = f"{self.moodle_url}/webservice/rest/server.php?wstoken={self.token}&wsfunction={method}&moodlewsrestformat=json"
        data = urllib.parse.urlencode(args).encode() if args else b""
        req = urllib.request.Request(url, data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            logger.warning("Moodle call %s failed: %s", method, e)
            return {"error": str(e), "status": "error"}

    def enroll_user(self, user_id: int, course_id: int) -> bool:
        """Matricula usuario en curso. Registra en GaiaChain."""
        result = self._call_moodle("core_enrol_enrol_users", {
            "enrolments[0][roleid]": 5,
            "enrolments[0][userid]": user_id,
            "enrolments[0][courseid]": course_id,
            "enrolments[0][timestart]": 0,
            "enrolments[0][timeend]": 0,
        })
        if result.get("error") or (isinstance(result, list) and len(result) > 0 and result[0].get("warningcode")):
            return False
        if self.blockchain:
            self.blockchain.log_academy_event({
                "user_id": user_id,
                "course_id": course_id,
                "event": "enrollment",
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            })
        return True

    def complete_module(
        self,
        user_id: int,
        course_id: int,
        module_id: int,
        score: float,
    ) -> Optional[str]:
        """Registra finalización de módulo (SCORM). Devuelve certificate_id si curso completado."""
        result = self._call_moodle("mod_scorm_insert_track", {
            "scoid": module_id,
            "userid": user_id,
            "attempt": 1,
            "element": "cmi.core.score.raw",
            "value": str(score),
        })
        if result.get("error"):
            return None
        if self.blockchain:
            self.blockchain.log_academy_event({
                "user_id": user_id,
                "course_id": course_id,
                "module_id": module_id,
                "event": "module_completed",
                "score": score,
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            })
        if self._is_course_complete(user_id, course_id):
            return self.issue_certificate(user_id, course_id)
        return None

    def _is_course_complete(self, user_id: int, course_id: int) -> bool:
        """Comprueba si el usuario ha completado todos los módulos del curso (stub)."""
        result = self._call_moodle("mod_scorm_get_scorms_by_courses", {"courseids[0]": course_id})
        if result.get("error") or not result:
            return False
        scorms = result if isinstance(result, list) else result.get("scorms", [])
        return len(scorms) > 0  # Simplificado: asumir completo si hay SCORM

    def issue_certificate(self, user_id: int, course_id: int) -> Optional[str]:
        """Emite certificado y lo registra en GaiaChain."""
        import time
        code = f"CASTUA-{int(time.time()):X}"
        result = self._call_moodle("tool_customcert_issue_certificate", {
            "userid": user_id,
            "courseid": course_id,
            "code": code,
        })
        if result.get("error"):
            return None
        cert_data = {
            "certificate_id": code,
            "user_id": user_id,
            "course_id": course_id,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "metadata": {"code": code},
        }
        if self.blockchain:
            self.blockchain.log_certificate(cert_data)
        return code

    def verify_certificate(self, certificate_code: str) -> Optional[Dict[str, Any]]:
        """Verifica certificado en GaiaChain y opcionalmente en Moodle."""
        if self.blockchain:
            cert_data = self.blockchain.get_certificate(certificate_code)
            if cert_data:
                return cert_data
        result = self._call_moodle("tool_customcert_get_certificate", {"code": certificate_code})
        if result.get("error"):
            return None
        return result
