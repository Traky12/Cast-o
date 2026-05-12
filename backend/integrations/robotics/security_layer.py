from __future__ import annotations

from typing import Any, Dict

from backend.security.pq_crypto import PostQuantumCrypto


class RobotSecurityLayer:
    """
    Autenticación/sellado alineado con el territorio Castúo: reutiliza pq_crypto (Kyber+DEM si pqcrypto; si no, ruta documentada en módulo).
    No expone APIs que no existan en cryptography hazmat.
    """

    def __init__(self, robot_id: str) -> None:
        self.robot_id = robot_id
        self._pqc = PostQuantumCrypto()

    def seal_utf8(self, message: str) -> Dict[str, Any]:
        return self._pqc.kyber_encrypt(message)

    def open_sealed(self, envelope: Dict[str, Any]) -> str:
        return self._pqc.kyber_decrypt(envelope)

    def sign_payload(self, message: str) -> str:
        return self._pqc.dilithium_sign(message)

    def verify_payload(self, message: str, signature_b64: str) -> bool:
        return self._pqc.dilithium_verify(message, signature_b64)
