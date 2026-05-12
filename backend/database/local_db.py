# -*- coding: utf-8 -*-
"""
LocalResilienceDB: continuidad operativa sin GaiaChain/eIDAS/internet.

Diseño:
 - Persistimos operaciones críticas en SQLite para sincronizarlas cuando la red vuelva.
 - Separar "evidencia local" de "prueba on-chain" preserva soberanía y no rompe flujos.
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SyncResult:
    status: str
    synced: int
    failed: int
    total: int


class LocalResilienceDB:
    def __init__(self, db_path: str | Path | None = None) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.db_path = Path(db_path) if db_path else (repo_root / "resilience.db")
        self.gaiachain_cli = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Cada operación abre su conexión: robusto bajo concurrencia moderada.
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
        with self._connect() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    retries INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    gaiachain_tx TEXT,
                    error_log TEXT
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lote_id TEXT NOT NULL,
                    certificate_data TEXT NOT NULL,
                    pdf_hash TEXT NOT NULL,
                    xml_hash TEXT NOT NULL,
                    gaiachain_tx TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'local_only'
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_data TEXT NOT NULL,
                    pdf_path TEXT,
                    gaiachain_tx TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'local_only'
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    severity TEXT DEFAULT 'info'
                )
                """
            )

            conn.commit()

    def log_system_event(self, event_type: str, details: str, severity: str = "info") -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO system_events (event_type, details, severity) VALUES (?, ?, ?)",
                (event_type, details, severity),
            )
            conn.commit()
            return int(cur.lastrowid)

    def _is_gaiachain_ok(self, gaiachain_tx: Optional[str]) -> bool:
        if not gaiachain_tx:
            return False
        if gaiachain_tx in ("gaiachain-no-cli", "pending"):
            return False
        if isinstance(gaiachain_tx, str) and gaiachain_tx.startswith("Error:"):
            return False
        return True

    def log_operation(
        self,
        operation_type: str,
        data: Dict[str, Any],
        gaiachain_tx: Optional[str] = None,
        error: Optional[str] = None,
    ) -> int:
        """
        Registra una operación crítica.

        - Si no hay TX o hay fallo, queda en cola (status='pending').
        - Si hay TX válido, se registra como 'synced' (opcionalmente, para trazabilidad).
        """
        status = "synced" if self._is_gaiachain_ok(gaiachain_tx) else "pending"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO pending_operations
                    (operation_type, data_json, retries, status, gaiachain_tx, error_log)
                VALUES
                    (?, ?, 0, ?, ?, ?)
                """,
                (
                    operation_type,
                    json.dumps(data, ensure_ascii=False),
                    status,
                    gaiachain_tx,
                    error,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def get_pending_operations(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, operation_type, data_json, retries, error_log, timestamp
                FROM pending_operations
                WHERE status = 'pending'
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
            out: List[Dict[str, Any]] = []
            for row in rows:
                out.append(
                    {
                        "id": row[0],
                        "operation_type": row[1],
                        "data": json.loads(row[2]),
                        "retries": row[3],
                        "error": row[4],
                        "timestamp": row[5],
                    }
                )
            return out

    def mark_as_synced(self, operation_id: int, gaiachain_tx: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE pending_operations
                SET status = 'synced', gaiachain_tx = ?, retries = retries + 1
                WHERE id = ?
                """,
                (gaiachain_tx, operation_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT event_type, details, severity, timestamp
                FROM system_events
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [
                {
                    "type": r[0],
                    "details": r[1],
                    "severity": r[2],
                    "timestamp": r[3],
                }
                for r in rows
            ]

    def log_certificate(self, certificate_data: Dict[str, Any]) -> int:
        """
        Guarda evidencia local de certificados (pdf/xml hashes) con estado.
        """
        lote_id = str(certificate_data.get("lote_id", "unknown"))
        pdf_hash = str(certificate_data.get("pdf_hash", "") or "")
        xml_hash = str(certificate_data.get("xml_hash", "") or "")
        gaiachain_tx = certificate_data.get("gaiachain_tx")
        status = "synced" if self._is_gaiachain_ok(gaiachain_tx) else "local_only"

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO certificates
                    (lote_id, certificate_data, pdf_hash, xml_hash, gaiachain_tx, status)
                VALUES
                    (?, ?, ?, ?, ?, ?)
                """,
                (
                    lote_id,
                    json.dumps(certificate_data.get("certificate_data", certificate_data), ensure_ascii=False),
                    pdf_hash,
                    xml_hash,
                    gaiachain_tx,
                    status,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def log_invoice(self, invoice_data: Dict[str, Any]) -> int:
        """
        Guarda evidencia local de facturas (pdf + hashes vía data_json).
        """
        pdf_path = invoice_data.get("pdf_path")
        gaiachain_tx = invoice_data.get("gaiachain_tx")
        status = "synced" if self._is_gaiachain_ok(gaiachain_tx) else "local_only"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO invoices
                    (invoice_data, pdf_path, gaiachain_tx, status)
                VALUES
                    (?, ?, ?, ?)
                """,
                (
                    json.dumps(invoice_data.get("invoice_data", invoice_data), ensure_ascii=False),
                    pdf_path,
                    gaiachain_tx,
                    status,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def get_certificate_by_tx(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un certificado local por transacción (GaiaChain tx o tx local).
        """
        if not tx_hash:
            return None
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT lote_id, certificate_data, pdf_hash, xml_hash, gaiachain_tx, status, timestamp
                FROM certificates
                WHERE gaiachain_tx = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (tx_hash,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "lote_id": row[0],
                "certificate_data": json.loads(row[1]),
                "pdf_hash": row[2],
                "xml_hash": row[3],
                "gaiachain_tx": row[4],
                "status": row[5],
                "timestamp": row[6],
            }

    def update_certificate_tx(
        self,
        lote_id: str,
        pdf_hash: str,
        gaiachain_tx: str,
        status: str = "synced",
    ) -> bool:
        """
        Reasigna gaiachain_tx del certificado local cuando GaiaChain vuelve.
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE certificates
                SET gaiachain_tx = ?, status = ?
                WHERE lote_id = ? AND pdf_hash = ?
                """,
                (gaiachain_tx, status, lote_id, pdf_hash),
            )
            conn.commit()
            return cur.rowcount > 0

    def list_local_certificates(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT lote_id, certificate_data, pdf_hash, xml_hash, gaiachain_tx, status, timestamp
                FROM certificates
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
            out: List[Dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "lote_id": r[0],
                        "certificate_data": json.loads(r[1]),
                        "pdf_hash": r[2],
                        "xml_hash": r[3],
                        "gaiachain_tx": r[4],
                        "status": r[5],
                        "timestamp": r[6],
                    }
                )
            return out

    def list_local_invoices(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, invoice_data, pdf_path, gaiachain_tx, status, timestamp
                FROM invoices
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
            out: List[Dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "id": r[0],
                        "invoice_data": json.loads(r[1]),
                        "pdf_path": r[2],
                        "gaiachain_tx": r[3],
                        "status": r[4],
                        "timestamp": r[5],
                    }
                )
            return out

    def _gaiachain_available(self) -> bool:
        return bool(self.gaiachain_cli) and Path(self.gaiachain_cli).is_file()

    def sync_with_gaiachain(self) -> SyncResult:
        """
        Intenta registrar en GaiaChain todas las operaciones pendientes.
        No rompe el flujo si la red sigue caida.
        """
        if not self._gaiachain_available():
            self.log_system_event("gaiachain_offline", "GaiaChain CLI no disponible; sin sincronización.", "warning")
            return SyncResult(status="offline", synced=0, failed=0, total=0)

        pending = self.get_pending_operations()
        if not pending:
            return SyncResult(status="success", synced=0, failed=0, total=0)

        import subprocess

        synced = 0
        failed = 0
        total = len(pending)

        for op in pending:
            op_id = int(op["id"])
            op_type = str(op["operation_type"])
            op_data = op["data"]

            try:
                r = subprocess.run(
                    [self.gaiachain_cli, "record", "--type", op_type, "--data", json.dumps(op_data, ensure_ascii=False)],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                tx = (r.stdout or "").strip()
                if r.returncode == 0 and tx:
                    if self.mark_as_synced(op_id, tx):
                        # Para que la verificación offline (tx local) converja con la prueba on-chain,
                        # actualizamos el tx del certificado final cuando GaiaChain lo registra.
                        if op_type == "final_certificate" and isinstance(op_data, dict):
                            lote_id = str(op_data.get("lote_id", "") or "")
                            cert_hash = str(op_data.get("certificate_hash", "") or "")
                            if lote_id and cert_hash:
                                self.update_certificate_tx(lote_id=lote_id, pdf_hash=cert_hash, gaiachain_tx=tx)
                        self.log_system_event(
                            "sync_success",
                            f"Operación {op_type} sincronizada. TX: {tx}.",
                            "info",
                        )
                        synced += 1
                    else:
                        failed += 1
                else:
                    err = (r.stderr or "").strip() or "gaiachain_error"
                    self.log_system_event(
                        "sync_failed",
                        f"Error sincronizando {op_type}: {err}",
                        "error",
                    )
                    # Mantener pending para reintentos.
                    failed += 1
                    # Actualizar error_log en la fila sin perder la trazabilidad:
                    with self._connect() as conn:
                        cur = conn.cursor()
                        cur.execute("UPDATE pending_operations SET error_log = ? WHERE id = ?", (err, op_id))
                        conn.commit()
            except Exception as e:
                failed += 1
                err = str(e)
                self.log_system_event("sync_exception", f"Excepción sincronizando {op_type}: {err}", "error")
                with self._connect() as conn:
                    cur = conn.cursor()
                    cur.execute("UPDATE pending_operations SET error_log = ? WHERE id = ?", (err, op_id))
                    conn.commit()

        status = "partial_success" if failed > 0 else "success"
        return SyncResult(status=status, synced=synced, failed=failed, total=total)


# Instancia global: soberanía local con alcance del proceso.
local_db = LocalResilienceDB()

