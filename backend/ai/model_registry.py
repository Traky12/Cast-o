# backend/ai/model_registry.py — Registro de modelos para federated learning (EU AI Act Anexo IV)

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from backend.security.pq_crypto import PostQuantumCrypto
    _CRYPTO = True
except ImportError:
    PostQuantumCrypto = None
    _CRYPTO = False


def _blake3_hex(data: bytes) -> str:
    try:
        return hashlib.blake3(data).hexdigest()
    except AttributeError:
        return hashlib.sha3_512(data).hexdigest()


class ModelRegistry:
    """
    Registro de modelos de IA: versionado, integridad, registro en GaiaChain.
    EU AI Act Anexo IV, ISO 27001 A.10.1.1.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.crypto = PostQuantumCrypto() if _CRYPTO else None
        self.local_models: Dict[str, Dict[str, Any]] = {}

    def get_local_models(self) -> Dict[str, Any]:
        return dict(self.local_models)

    def register_model(self, model_name: str, model_data: Dict[str, Any], version: Optional[str] = None) -> Optional[str]:
        version = version or datetime.utcnow().strftime("%Y%m%d%H%M")
        model_hash = _blake3_hex(json.dumps(model_data, sort_keys=True).encode())
        record = {
            "model_name": model_name,
            "version": version,
            "data": model_data,
            "hash": model_hash,
            "timestamp": datetime.utcnow().isoformat(),
            "normative_compliance": {"EU_AI_Act": "Anexo IV", "ISO_27001": "A.10.1.1"},
        }
        if self.crypto:
            script = os.path.join(os.path.dirname(__file__), "..", "scripts", "register_gaiachain_event.py")
            if os.path.isfile(script):
                try:
                    enc = self.crypto.hybrid_encrypt_large(json.dumps(record))
                    subprocess.run(
                        [os.environ.get("PYTHON", "python"), script, "--event_type", "model_registry", "--details", json.dumps(enc), "--norms", "EU_AI_Act:Anexo_IV"],
                        check=False,
                        timeout=30,
                    )
                except Exception as e:
                    self.logger.debug("register_gaiachain model: %s", e)
        if model_name not in self.local_models:
            self.local_models[model_name] = {}
        self.local_models[model_name][version] = record
        return version

    def get_model(self, model_name: str, version: str = "latest") -> Optional[Dict]:
        if model_name not in self.local_models:
            return None
        versions = list(self.local_models[model_name].keys())
        versions.sort()
        v = versions[-1] if version == "latest" and versions else (version if version in self.local_models[model_name] else None)
        if v is None:
            return None
        return self.local_models[model_name][v].get("data")

    def verify_model_integrity(self, model_name: str, version: str) -> bool:
        rec = self.local_models.get(model_name, {}).get(version)
        if not rec:
            return False
        current = _blake3_hex(json.dumps(rec["data"], sort_keys=True).encode())
        return current == rec.get("hash")
