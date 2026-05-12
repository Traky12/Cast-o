import hashlib
import time
from typing import Dict


def mock_digital_signature(data: Dict) -> str:
    """Simula firma digital para demo AEPD (en producción usar HSM/cryptography)."""
    data_str = f"{data!r}{time.time()}"
    return hashlib.sha256(data_str.encode("utf-8")).hexdigest()[:16]

