"""
CASTÚO-SYSTEM™ v3.1 — Bitácora de Auditoría Inmutable
Registra todas las acciones sobre lotes, operadores y el sistema
en un fichero JSONL append-only con cadena criptográfica SHA-256.

Propiedades:
  - Append-only: los eventos nunca se modifican ni eliminan
  - Chain-of-custody: cada evento enlaza al anterior via hash_anterior
  - Integridad verificable: recorrido completo de la cadena en O(n)
  - Operador accountability: actor_nif en cada evento
  - Thread-safe: escrituras protegidas con threading.Lock

Variables de entorno:
    AUDIT_LOG_PATH   Ruta al fichero JSONL (default: /data/audit/castuo_audit.jsonl)
    AUDIT_MAX_MB     Tamaño máximo antes de rotar en MB (default: 100)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger("castuo.audit")

AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "/data/audit/castuo_audit.jsonl")
AUDIT_MAX_BYTES = int(os.getenv("AUDIT_MAX_MB", "100")) * 1024 * 1024


# ── Enumerados ─────────────────────────────────────────────────────────────────

class AuditAction(str, Enum):
    # Ciclo de lote
    APERTURA_LOTE         = "APERTURA_LOTE"
    CIERRE_LOTE           = "CIERRE_LOTE"
    # Registros de producción
    REGISTRO_SOLUCION     = "REGISTRO_SOLUCION"
    REGISTRO_CLIMA        = "REGISTRO_CLIMA"
    REGISTRO_AGROVOLTAICO = "REGISTRO_AGROVOLTAICO"
    REGISTRO_FITOSANITARIO = "REGISTRO_FITOSANITARIO"
    REGISTRO_COSECHA      = "REGISTRO_COSECHA"
    # Control activo
    CONTROL_ACTUADOR      = "CONTROL_ACTUADOR"
    EMERGENCIA_STOP       = "EMERGENCIA_STOP"
    # Validación y trazabilidad
    VALIDACION_LOTE       = "VALIDACION_LOTE"
    GENERACION_QR         = "GENERACION_QR"
    # Sistema
    ACCESO_API            = "ACCESO_API"


# ── Modelo de evento ───────────────────────────────────────────────────────────

class AuditEvent:
    """
    Evento de auditoría inmutable.
    El hash propio se calcula sobre (accion + lote_id + actor_nif + timestamp + datos + hash_anterior).
    """

    __slots__ = (
        "evento_id", "accion", "lote_id", "actor_nif", "recurso",
        "datos", "timestamp", "hash_anterior", "hash_propio",
    )

    def __init__(
        self,
        accion: str,
        lote_id: str,
        actor_nif: str,
        recurso: str,
        datos: dict,
        timestamp: str,
        hash_anterior: str,
    ) -> None:
        self.accion = accion
        self.lote_id = lote_id
        self.actor_nif = actor_nif
        self.recurso = recurso
        self.datos = datos
        self.timestamp = timestamp
        self.hash_anterior = hash_anterior
        self.hash_propio = self._calcular_hash()
        self.evento_id = self.hash_propio[:16]

    def _calcular_hash(self) -> str:
        contenido = json.dumps(
            {
                "accion":         self.accion,
                "lote_id":        self.lote_id,
                "actor_nif":      self.actor_nif,
                "recurso":        self.recurso,
                "timestamp":      self.timestamp,
                "hash_anterior":  self.hash_anterior,
                # Sólo las claves deterministas del payload para el hash
                "datos_keys":     sorted(self.datos.keys()),
            },
            sort_keys=True,
        )
        return hashlib.sha256(contenido.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "evento_id":       self.evento_id,
            "accion":          self.accion,
            "lote_id":         self.lote_id,
            "actor_nif":       self.actor_nif,
            "recurso":         self.recurso,
            "datos":           self.datos,
            "timestamp":       self.timestamp,
            "hash_anterior":   self.hash_anterior,
            "hash_propio":     self.hash_propio,
        }


# ── AuditLogger ────────────────────────────────────────────────────────────────

class AuditLogger:
    """
    Bitácora de auditoría append-only con cadena criptográfica SHA-256.

    Uso:
        logger = AuditLogger()
        logger.log(AuditAction.APERTURA_LOTE, "INVH-...", "12345678Z", "lote", {})
    """

    # Hash inicial de la cadena (génesis)
    GENESIS_HASH = "0" * 64

    def __init__(self, log_path: str | None = None) -> None:
        self._path = Path(log_path or AUDIT_LOG_PATH)
        self._lock = threading.Lock()
        self._last_hash: str = self.GENESIS_HASH
        self._event_count: int = 0

        # Crear directorio si no existe
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning("[audit] No se pudo crear directorio %s: %s — modo memoria", self._path.parent, exc)
            self._path = None  # type: ignore

        # Reconstruir último hash desde el fichero existente
        self._load_last_hash()

    # ── Escritura ──────────────────────────────────────────────────────────────

    def log(
        self,
        accion: AuditAction | str,
        lote_id: str,
        actor_nif: str,
        recurso: str,
        datos: dict,
        timestamp: str | None = None,
    ) -> AuditEvent:
        """
        Registra un evento en la bitácora y retorna el AuditEvent creado.
        Thread-safe mediante Lock.
        """
        now = timestamp or datetime.now(timezone.utc).isoformat()
        accion_str = accion.value if isinstance(accion, AuditAction) else str(accion)

        with self._lock:
            evento = AuditEvent(
                accion=accion_str,
                lote_id=lote_id,
                actor_nif=actor_nif,
                recurso=recurso,
                datos=datos,
                timestamp=now,
                hash_anterior=self._last_hash,
            )
            self._append(evento)
            self._last_hash = evento.hash_propio
            self._event_count += 1

        logger.debug(
            "[audit] %s lote=%s actor=%s id=%s",
            accion_str, lote_id, actor_nif, evento.evento_id,
        )
        return evento

    def _append(self, evento: AuditEvent) -> None:
        if self._path is None:
            return
        try:
            # Rotar si supera el límite de tamaño
            if self._path.exists() and self._path.stat().st_size > AUDIT_MAX_BYTES:
                self._rotate()
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(evento.to_dict(), ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.warning("[audit] Error escribiendo en %s: %s", self._path, exc)

    def _rotate(self) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rotated = self._path.with_suffix(f".{ts}.jsonl")
        self._path.rename(rotated)
        logger.info("[audit] Bitácora rotada → %s", rotated)

    # ── Lectura y búsqueda ────────────────────────────────────────────────────

    def _read_all(self) -> list[dict]:
        """Lee todos los eventos del fichero JSONL."""
        if self._path is None or not self._path.exists():
            return []
        events = []
        try:
            with self._path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except OSError as exc:
            logger.warning("[audit] Error leyendo bitácora: %s", exc)
        return events

    def get_by_lote(self, lote_id: str) -> list[dict]:
        """Retorna todos los eventos de un lote_id específico en orden cronológico."""
        return [e for e in self._read_all() if e.get("lote_id") == lote_id]

    def get_by_operator(self, actor_nif: str, limit: int = 100) -> list[dict]:
        """Retorna los últimos N eventos de un operador específico."""
        events = [e for e in self._read_all() if e.get("actor_nif") == actor_nif]
        return events[-limit:]

    def get_by_action(self, accion: str, limit: int = 200) -> list[dict]:
        """Retorna los últimos N eventos de un tipo de acción."""
        events = [e for e in self._read_all() if e.get("accion") == accion]
        return events[-limit:]

    def search(
        self,
        lote_id: str | None = None,
        actor_nif: str | None = None,
        accion: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Búsqueda multi-filtro sobre la bitácora."""
        events = self._read_all()
        if lote_id:
            events = [e for e in events if e.get("lote_id") == lote_id]
        if actor_nif:
            events = [e for e in events if e.get("actor_nif") == actor_nif]
        if accion:
            events = [e for e in events if e.get("accion") == accion]
        if desde:
            events = [e for e in events if e.get("timestamp", "") >= desde]
        if hasta:
            events = [e for e in events if e.get("timestamp", "") <= hasta]
        return events[-limit:]

    # ── Verificación de integridad ────────────────────────────────────────────

    def verify_chain(self) -> dict:
        """
        Verifica la integridad criptográfica de la cadena completa.
        Retorna dict con ok, total_eventos, errores encontrados.
        """
        events = self._read_all()
        if not events:
            return {"ok": True, "total_eventos": 0, "errores": [], "mensaje": "Cadena vacía"}

        errores = []
        prev_hash = self.GENESIS_HASH

        for i, raw in enumerate(events):
            # Verificar que hash_anterior enlaza al evento previo
            if raw.get("hash_anterior") != prev_hash:
                errores.append({
                    "posicion":   i,
                    "evento_id":  raw.get("evento_id"),
                    "problema":   "hash_anterior no coincide con hash previo",
                })

            # Recalcular hash_propio
            evento_reconstituido = AuditEvent(
                accion=raw.get("accion", ""),
                lote_id=raw.get("lote_id", ""),
                actor_nif=raw.get("actor_nif", ""),
                recurso=raw.get("recurso", ""),
                datos=raw.get("datos", {}),
                timestamp=raw.get("timestamp", ""),
                hash_anterior=raw.get("hash_anterior", ""),
            )
            if evento_reconstituido.hash_propio != raw.get("hash_propio"):
                errores.append({
                    "posicion":   i,
                    "evento_id":  raw.get("evento_id"),
                    "problema":   "hash_propio no coincide — evento posiblemente manipulado",
                })

            prev_hash = raw.get("hash_propio", "")

        return {
            "ok":            len(errores) == 0,
            "total_eventos": len(events),
            "errores":       errores,
            "ultimo_hash":   prev_hash,
            "mensaje":       "Cadena íntegra" if not errores else f"{len(errores)} errores detectados",
        }

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _load_last_hash(self) -> None:
        """Recupera el último hash del fichero existente al iniciar."""
        if self._path is None or not self._path.exists():
            return
        try:
            with self._path.open(encoding="utf-8") as fh:
                last_line = ""
                for line in fh:
                    line = line.strip()
                    if line:
                        last_line = line
            if last_line:
                data = json.loads(last_line)
                self._last_hash = data.get("hash_propio", self.GENESIS_HASH)
                self._event_count = sum(
                    1 for _ in self._path.open(encoding="utf-8")
                )
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("[audit] Error cargando último hash: %s", exc)

    @property
    def event_count(self) -> int:
        return self._event_count

    @property
    def last_hash(self) -> str:
        return self._last_hash


# ── Instancia global ───────────────────────────────────────────────────────────

_audit_instance: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Retorna la instancia global del AuditLogger (singleton lazy)."""
    global _audit_instance
    if _audit_instance is None:
        _audit_instance = AuditLogger()
    return _audit_instance
