from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path


def cert_needs_rotation(cert_path: str, max_days: int = 60) -> bool:
    path = Path(cert_path)
    if not path.exists():
        return True
    age_days = (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).days
    return age_days >= max_days


if __name__ == "__main__":
    cert = "certs/server.crt"
    print("rotate" if cert_needs_rotation(cert) else "ok")
