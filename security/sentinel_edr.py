# -*- coding: utf-8 -*-
"""
Sentinel v5 — EDR (Endpoint Detection and Response). Cambios de archivos, cuarentena, GaiaChain.
Normativas: ISO 27033, NIST SP 800-94.
"""
import hashlib
import os
import shutil
import time
from datetime import datetime
from typing import Dict, Set

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


class SentinelEDR:
    """
    Monitoreo de cambios en archivos bajo /opt/castu; detección de modificaciones no autorizadas;
    cuarentena y registro en GaiaChain.
    """

    def __init__(self, watch_root: str = "/opt/castu", quarantine_dir: str = "/opt/castu/quarantine") -> None:
        self.watch_root = watch_root
        self.quarantine_dir = quarantine_dir
        self.blockchain = GaiaChainClient() if GaiaChainClient else None
        self.known_files: Dict[str, str] = {}
        self._scan_known_files()
        os.makedirs(self.quarantine_dir, exist_ok=True)

    def _scan_known_files(self) -> None:
        """Registra hash de archivos conocidos bajo watch_root."""
        if not os.path.isdir(self.watch_root):
            self.known_files = {}
            return
        for root, _, files in os.walk(self.watch_root):
            if self.quarantine_dir and self.quarantine_dir.rstrip("/") in root:
                continue
            for f in files:
                path = os.path.join(root, f)
                try:
                    with open(path, "rb") as fp:
                        self.known_files[path] = hashlib.sha256(fp.read()).hexdigest()
                except (OSError, IOError):
                    continue

    def _file_hash(self, path: str) -> str:
        try:
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except (OSError, IOError):
            return ""

    def _quarantine_file(self, path: str, reason: str) -> bool:
        """Mueve archivo a cuarentena y registra en GaiaChain."""
        try:
            name = os.path.basename(path)
            dest = os.path.join(self.quarantine_dir, f"{int(time.time())}_{name}")
            shutil.move(path, dest)
            if self.blockchain:
                self.blockchain.log_security_alert({
                    "type": "file_quarantine",
                    "path": path,
                    "quarantine_path": dest,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                    "node_id": "edr",
                    "severity": "high",
                })
            return True
        except Exception:
            return False

    def monitor_file_changes(self) -> None:
        """Bucle: detecta archivos nuevos, modificados o eliminados; cuarentena si cambió hash."""
        if not os.path.isdir(self.watch_root):
            return
        while True:
            current: Dict[str, str] = {}
            for root, _, files in os.walk(self.watch_root):
                if self.quarantine_dir and self.quarantine_dir.rstrip("/") in root:
                    continue
                for f in files:
                    path = os.path.join(root, f)
                    h = self._file_hash(path)
                    if h:
                        current[path] = h

            for path, new_hash in current.items():
                old_hash = self.known_files.get(path)
                if old_hash is None:
                    continue  # nuevo archivo: opcional alert
                if old_hash != new_hash:
                    self._handle_alert("file_change", path, f"hash changed {old_hash[:8]} -> {new_hash[:8]}")
                    self._quarantine_file(path, "hash mismatch")

            gone: Set[str] = set(self.known_files) - set(current)
            for path in gone:
                if os.path.exists(path):
                    continue
                self._handle_alert("file_deleted", path, "file removed from watch root")

            self.known_files = current
            time.sleep(10)

    def _handle_alert(self, alert_type: str, path: str, detail: str) -> None:
        if self.blockchain:
            self.blockchain.log_security_alert({
                "type": alert_type,
                "path": path,
                "detail": detail,
                "timestamp": datetime.now().isoformat(),
                "node_id": "edr",
                "severity": "medium",
            })
