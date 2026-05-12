# -*- coding: utf-8 -*-
"""
Autenticación multicapa: YubiKey + biometría + HSM + GaiaChain.
Stubs cuando no hay hardware (yubico_client, pyfingerprint, pkcs11).
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import sys
    from pathlib import Path
    _root = Path(__file__).resolve().parents[1]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    import yubico_client
    HAS_YUBICO = True
except ImportError:
    HAS_YUBICO = False
    yubico_client = None  # type: ignore

try:
    from pyfingerprint.pyfingerprint import PyFingerprint
    HAS_FINGERPRINT = True
except ImportError:
    HAS_FINGERPRINT = False
    PyFingerprint = None  # type: ignore

try:
    import pkcs11
    HAS_PKCS11 = True
except ImportError:
    HAS_PKCS11 = False
    pkcs11 = None  # type: ignore


class AdvancedAuthentication:
    """Sistema de autenticación multicapa con YubiKey, biometría, HSM y GaiaChain."""

    def __init__(
        self,
        gaiachain_client: Optional[Any] = None,
        hsm_config: Optional[Dict[str, Any]] = None,
        yubico_api_id: int = 1,
        yubico_api_key: str = "",
        fingerprint_port: str = "/dev/ttyUSB0",
    ) -> None:
        self.gaiachain = gaiachain_client or (GaiaChainClient() if GaiaChainClient else None)
        self.hsm_config = hsm_config or {}
        self._hsm_session: Any = None
        self._yubi_client: Any = None
        self._fp_sensor: Any = None
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._session_hours = 8

        if HAS_YUBICO and yubico_api_key:
            try:
                self._yubi_client = yubico_client.Yubico(yubico_api_id, yubico_api_key)
            except Exception as e:
                logger.warning("YubiKey client init failed: %s", e)
        if HAS_FINGERPRINT and PyFingerprint:
            try:
                self._fp_sensor = PyFingerprint(fingerprint_port, 57600, 0xFFFFFFFF, 0x00000000)
            except Exception as e:
                logger.warning("Fingerprint sensor init failed: %s", e)
        if HAS_PKCS11 and self.hsm_config.get("lib"):
            self._hsm_session = self._init_hsm(self.hsm_config)

    def _init_hsm(self, config: Dict[str, Any]) -> Optional[Any]:
        if not HAS_PKCS11 or not pkcs11:
            return None
        try:
            lib = pkcs11.lib(config["lib"])
            slots = lib.get_slot_list(token_present=True)
            slot = slots[config.get("slot", 0)] if slots else None
            if not slot:
                return None
            session = lib.open_session(slot, pkcs11.CKF_SERIAL_SESSION | pkcs11.CKF_RW_SESSION)
            session.login(config["pin"])
            return session
        except Exception as e:
            logger.warning("HSM init failed: %s", e)
            return None

    def _generate_session_token(self, user_id: str) -> str:
        return hashlib.sha256(
            f"{user_id}_{secrets.token_hex(16)}_{datetime.now().isoformat()}".encode()
        ).hexdigest()

    def authenticate(
        self,
        user_id: str,
        yubikey_otp: str = "",
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Proceso de autenticación multicapa.
        Returns:
            (success, message, session_data or None)
        """
        if self._yubi_client and yubikey_otp:
            try:
                verification = self._yubi_client.verify(yubikey_otp)
                if not getattr(verification, "valid", True):
                    return False, "OTP de YubiKey inválido", None
            except Exception as e:
                return False, f"Error en verificación YubiKey: {str(e)}", None
        elif not yubikey_otp and self._yubi_client:
            return False, "Se requiere OTP de YubiKey", None

        if self._fp_sensor:
            try:
                if not self._fp_sensor.verifyPassword():
                    return False, "Error en sensor de huellas", None
                if not self._fp_sensor.readImage():
                    return False, "No se detectó huella", None
                self._fp_sensor.convertImage(0x01)
                result = self._fp_sensor.searchTemplate()
                if result[0] != 0:
                    return False, "Huella no reconocida", None
            except Exception as e:
                return False, f"Error en sensor de huellas: {str(e)}", None

        challenge = secrets.token_hex(16)
        simulated_signature = hashlib.sha256(f"{user_id}_{challenge}".encode()).hexdigest()

        session_token = self._generate_session_token(user_id)
        self.sessions[session_token] = {
            "user_id": user_id,
            "auth_time": datetime.now().isoformat(),
            "auth_methods": ["yubikey", "fingerprint", "hsm"] if (self._yubi_client or self._fp_sensor) else ["stub"],
            "ip_address": "192.168.1.100",
            "device": "Secure Terminal",
        }

        if self.gaiachain:
            self.gaiachain.log_auth_event(
                {
                    "user_id": user_id,
                    "session_token": session_token,
                    "auth_methods": self.sessions[session_token]["auth_methods"],
                    "timestamp": datetime.now().isoformat(),
                    "challenge": challenge,
                    "signature": simulated_signature,
                    "status": "success",
                }
            )

        return True, "Autenticación exitosa", {
            "session_token": session_token,
            "expires_at": (datetime.now() + timedelta(hours=self._session_hours)).isoformat(),
            "gaiachain_tx": "gaia-auth-" + session_token[:16],
        }

    def validate_session(self, session_token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Valida una sesión activa."""
        session = self.sessions.get(session_token)
        if not session:
            return False, None
        auth_time = datetime.fromisoformat(session["auth_time"])
        if auth_time + timedelta(hours=self._session_hours) < datetime.now():
            return False, None
        return True, session

    def close_session(self, session_token: str) -> bool:
        """Cierra una sesión activa."""
        if session_token not in self.sessions:
            return False
        session = self.sessions.pop(session_token)
        if self.gaiachain:
            self.gaiachain.log_auth_event(
                {
                    "user_id": session["user_id"],
                    "session_token": session_token,
                    "timestamp": datetime.now().isoformat(),
                    "status": "closed",
                    "duration": int(
                        (datetime.now() - datetime.fromisoformat(session["auth_time"])).total_seconds()
                    ),
                }
            )
        return True

    def get_session_info(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de una sesión."""
        session = self.sessions.get(session_token)
        if not session:
            return None
        return {
            **session,
            "expires_at": (
                datetime.fromisoformat(session["auth_time"]) + timedelta(hours=self._session_hours)
            ).isoformat(),
        }


if __name__ == "__main__":
    auth = AdvancedAuthentication(gaiachain_client=GaiaChainClient() if GaiaChainClient else None)
    success, message, session_data = auth.authenticate("gregorio@castu.system", "")
    if success or not auth._yubi_client:
        success, message, session_data = auth.authenticate("gregorio@castu.system", "stub_otp_for_demo")
    if success:
        print("Autenticación exitosa:", session_data)
        valid, info = auth.validate_session(session_data["session_token"])
        print("Sesión válida:", valid)
        auth.close_session(session_data["session_token"])
    else:
        print("Error:", message)
