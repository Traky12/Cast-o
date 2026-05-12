# -*- coding: utf-8 -*-
"""
Sentinel v5 — IDS (Detección de intrusos). Anomalías en tiempo real, registro en GaiaChain.
Normativas: ISO 27033, NIST SP 800-94.
"""
import socket
import time
from datetime import datetime
from typing import Any, Dict, List

import psutil

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


class SentinelIDS:
    """
    Detección de anomalías: CPU alto, procesos nuevos, conexiones sospechosas.
    Respuesta: alerta, bloqueo, registro en GaiaChain.
    """

    def __init__(self) -> None:
        self.blockchain = GaiaChainClient() if GaiaChainClient else None
        self.baseline: Dict[str, Any] = self._establish_baseline()
        self.rules = {
            "high_cpu": {"threshold": 90, "action": "alert"},
            "new_process": {"action": "investigate"},
            "unusual_connection": {"ports": [22, 3389, 8545], "action": "block"},
        }
        self.alerts: List[Dict[str, Any]] = []

    def _establish_baseline(self) -> Dict[str, Any]:
        """Establece métricas base del sistema."""
        return {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory().percent,
            "connections": len(psutil.net_connections()),
            "processes": set(psutil.pids()),
        }

    def _get_suspicious_connections(self) -> List[Dict[str, Any]]:
        """Lista conexiones a puertos sensibles (SSH, RDP, RPC)."""
        suspicious = []
        try:
            for conn in psutil.net_connections():
                if conn.status == "ESTABLISHED" and conn.raddr and conn.laddr:
                    if conn.raddr.port in self.rules["unusual_connection"]["ports"]:
                        suspicious.append({
                            "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}",
                            "remote_addr": f"{conn.raddr.ip}:{conn.raddr.port}",
                            "pid": conn.pid,
                            "status": conn.status,
                        })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return suspicious

    def _get_new_processes(self) -> List[Dict[str, Any]]:
        """Procesos nuevos desde el baseline."""
        current_pids = set(psutil.pids())
        prev = self.baseline.get("processes") or set()
        new_processes = []
        for pid in (current_pids - prev):
            try:
                p = psutil.Process(pid)
                new_processes.append({
                    "pid": pid,
                    "name": p.name(),
                    "exe": p.exe(),
                    "cmdline": " ".join(p.cmdline()) if p.cmdline() else "",
                    "username": p.username(),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return new_processes

    def _get_top_processes(self, n: int = 5) -> List[Dict[str, Any]]:
        """Top N procesos por uso de CPU."""
        procs = []
        for p in psutil.process_iter(["pid", "name", "username", "cpu_percent"]):
            try:
                p.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        time.sleep(0.1)
        for p in psutil.process_iter(["pid", "name", "username", "cpu_percent"]):
            try:
                procs.append({
                    "pid": p.info["pid"],
                    "name": p.info["name"],
                    "user": p.info["username"],
                    "cpu": p.info.get("cpu_percent") or 0,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(procs, key=lambda x: x["cpu"], reverse=True)[:n]

    def _is_known_process(self, exe_path: str) -> bool:
        """Comprueba si el ejecutable está en whitelist."""
        known = ["/usr/bin/python", "/opt/castu", "/usr/sbin/sshd", "/usr/bin/docker", "python"]
        return any(k in (exe_path or "") for k in known)

    def _check_cpu_usage(self, current: Dict[str, Any]) -> None:
        if current.get("cpu", 0) > self.rules["high_cpu"]["threshold"]:
            alert = {
                "type": "high_cpu_usage",
                "value": current["cpu"],
                "threshold": self.rules["high_cpu"]["threshold"],
                "timestamp": current["timestamp"],
                "action": self.rules["high_cpu"]["action"],
                "processes": self._get_top_processes(5),
            }
            self._handle_alert(alert)

    def _check_new_processes(self, current: Dict[str, Any]) -> None:
        for proc in current.get("processes") or []:
            if not self._is_known_process(proc.get("exe", "")):
                alert = {
                    "type": "suspicious_process",
                    "process": proc,
                    "timestamp": current["timestamp"],
                    "action": self.rules["new_process"]["action"],
                }
                self._handle_alert(alert)

    def _check_connections(self, current: Dict[str, Any]) -> None:
        for conn in current.get("connections") or []:
            alert = {
                "type": "suspicious_connection",
                "connection": conn,
                "timestamp": current["timestamp"],
                "action": self.rules["unusual_connection"]["action"],
            }
            self._handle_alert(alert)

    def _determine_severity(self, alert_type: str) -> str:
        sev = {"high_cpu_usage": "medium", "suspicious_process": "high", "suspicious_connection": "critical"}
        return sev.get(alert_type, "low")

    def _handle_alert(self, alert: Dict[str, Any]) -> None:
        self.alerts.append(alert)
        if self.blockchain:
            self.blockchain.log_security_alert({
                "type": alert["type"],
                "data": alert,
                "timestamp": alert["timestamp"],
                "node_id": socket.gethostname(),
                "severity": self._determine_severity(alert["type"]),
            })
        if alert.get("action") == "block" and alert.get("type") == "suspicious_connection":
            conn = alert.get("connection", {})
            remote = conn.get("remote_addr", "").split(":")[0]
            if remote:
                pass  # En producción: iptables/nftables para bloquear remote

    def monitor_system(self) -> None:
        """Bucle de monitoreo (cada 5 s)."""
        while True:
            current = {
                "timestamp": datetime.now().isoformat(),
                "cpu": psutil.cpu_percent(interval=1),
                "memory": psutil.virtual_memory().percent,
                "connections": self._get_suspicious_connections(),
                "processes": self._get_new_processes(),
            }
            self.baseline["processes"] = set(psutil.pids())
            self._check_cpu_usage(current)
            self._check_new_processes(current)
            self._check_connections(current)
            time.sleep(5)
