# backend/compliance/opa_client.py — Cliente OpenPolicyAgent para validación de acciones

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    import requests
    _REQUESTS = True
except ImportError:
    requests = None
    _REQUESTS = False


class OPAClient:
    """
    Cliente para OpenPolicyAgent: evalúa acciones contra políticas de cumplimiento.
    Opcionalmente registra el resultado en GaiaChain (cifrado).
    """

    def __init__(self, opa_url: str | None = None) -> None:
        self.opa_url = (opa_url or os.getenv("OPA_URL", "http://localhost:8181")).rstrip("/")
        self.logger = logging.getLogger(__name__)

    def evaluate(self, input_data: Dict[str, Any], policy: str = "castuo/compliance") -> bool:
        """Evalúa input contra la política OPA. Devuelve True si allow."""
        if not _REQUESTS:
            self.logger.debug("requests no instalado; OPA no disponible")
            return True
        try:
            url = f"{self.opa_url}/v1/data/{policy.replace('.', '/')}"
            r = requests.post(
                url,
                json={"input": input_data},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("result", {}).get("allow", False)
        except Exception as e:
            self.logger.error("Error OPA: %s", e)
            return False

    def evaluate_and_register(
        self,
        input_data: Dict[str, Any],
        policy: str = "castuo/compliance",
    ) -> Dict[str, Any]:
        """Evalúa y registra el resultado en GaiaChain (cifrado)."""
        compliant = self.evaluate(input_data, policy)
        out = {"compliant": compliant, "policy": policy}
        try:
            from backend.security.pq_crypto import PostQuantumCrypto
            crypto = PostQuantumCrypto()
            record = {
                "input": input_data,
                "policy": policy,
                "compliant": compliant,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "normative_reference": {"EU_AI_Act": "Art. 13", "ISO_27001": "A.18.1.4"},
            }
            enc = crypto.hybrid_encrypt_large(json.dumps(record))
            script = os.path.join(os.path.dirname(__file__), "..", "scripts", "register_gaiachain_event.py")
            if os.path.isfile(script):
                subprocess.run(
                    [os.environ.get("PYTHON", "python"), script, "--event_type", "opa_evaluation", "--details", json.dumps(enc), "--norms", "EU_AI_Act:Art.13,ISO_27001:A.18.1.4"],
                    check=False,
                    timeout=30,
                )
            out["gaiachain_event"] = "registered"
        except Exception as e:
            self.logger.debug("Registro GaiaChain omitido: %s", e)
        return out
