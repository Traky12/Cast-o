"""
Logs XAI firmados + encadenamiento CASTUO Ledger.
El ancla de cada evento amarra el anterior: prueba temporal para patrimonio (grieta t0 vs t+2a).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

_HEX64 = re.compile(r"^(0x)?[a-fA-F0-9]{64}$")


def genesis_ledger_hash() -> str:
    return "0x" + "0" * 64


def _norm_hex(h: str) -> bytes:
    s = h.strip().lower().removeprefix("0x")
    if len(s) != 64:
        raise ValueError("ledger hash debe ser 32 bytes hex")
    return bytes.fromhex(s)


def build_canonical_unsigned(
    event_id: str,
    timestamp: str,
    unit_id: str,
    decision: dict[str, Any],
    telemetry_snapshot: dict[str, Any],
    ledger_hash: str,
    mission_id: str | None = None,
) -> str:
    """JSON canónico firmable (sin signature ni event_anchor_hash)."""
    body: dict[str, Any] = {
        "schema_version": "castuo.xai_ledger_log.v1",
        "event_id": event_id,
        "timestamp": timestamp,
        "unit_id": unit_id,
        "decision": decision,
        "telemetry_snapshot": telemetry_snapshot,
        "ledger_hash": ledger_hash.lower() if ledger_hash.startswith("0x") else "0x" + ledger_hash.lower(),
    }
    if mission_id:
        body["mission_id"] = mission_id
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_event_anchor_hash(parent_ledger_hash_hex: str, canonical_unsigned: str) -> str:
    parent = _norm_hex(parent_ledger_hash_hex)
    inner = hashlib.sha256(canonical_unsigned.encode("utf-8")).digest()
    chained = hashlib.sha256(parent + inner).digest()
    return "0x" + chained.hex()


@dataclass
class XAILedgerLogV1:
    event_id: str
    timestamp: str
    unit_id: str
    decision: dict[str, Any]
    telemetry_snapshot: dict[str, Any]
    ledger_hash: str
    event_anchor_hash: str
    signature: str
    mission_id: str | None = None
    signer_pubkey_hint: str | None = None

    def to_committed_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "schema_version": "castuo.xai_ledger_log.v1",
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "unit_id": self.unit_id,
            "decision": self.decision,
            "telemetry_snapshot": self.telemetry_snapshot,
            "ledger_hash": self.ledger_hash,
            "event_anchor_hash": self.event_anchor_hash,
            "signature": self.signature,
        }
        if self.mission_id:
            d["mission_id"] = self.mission_id
        if self.signer_pubkey_hint:
            d["signer_pubkey_hint"] = self.signer_pubkey_hint
        return d

    @classmethod
    def build_pending(
        cls,
        *,
        event_id: str,
        timestamp: str,
        unit_id: str,
        decision: dict[str, Any],
        telemetry_snapshot: dict[str, Any],
        parent_ledger_hash: str,
        mission_id: str | None = None,
    ) -> tuple[str, str]:
        """Retorna (canonical_unsigned, event_anchor_hex) para firmar en SE."""
        canon = build_canonical_unsigned(
            event_id, timestamp, unit_id, decision, telemetry_snapshot, parent_ledger_hash, mission_id
        )
        anchor = compute_event_anchor_hash(parent_ledger_hash, canon)
        return canon, anchor

    @classmethod
    def seal(
        cls,
        *,
        event_id: str,
        timestamp: str,
        unit_id: str,
        decision: dict[str, Any],
        telemetry_snapshot: dict[str, Any],
        parent_ledger_hash: str,
        signature_hex: str,
        mission_id: str | None = None,
        signer_pubkey_hint: str | None = None,
    ) -> XAILedgerLogV1:
        canon, anchor = cls.build_pending(
            event_id=event_id,
            timestamp=timestamp,
            unit_id=unit_id,
            decision=decision,
            telemetry_snapshot=telemetry_snapshot,
            parent_ledger_hash=parent_ledger_hash,
            mission_id=mission_id,
        )
        lh = parent_ledger_hash if parent_ledger_hash.startswith("0x") else "0x" + parent_ledger_hash
        return cls(
            event_id=event_id,
            timestamp=timestamp,
            unit_id=unit_id,
            decision=decision,
            telemetry_snapshot=telemetry_snapshot,
            ledger_hash=lh.lower(),
            event_anchor_hash=anchor.lower(),
            signature=signature_hex,
            mission_id=mission_id,
            signer_pubkey_hint=signer_pubkey_hint,
        )


def verify_log_chain(logs: list[dict[str, Any]]) -> tuple[bool, str]:
    """Ordena por timestamp ISO; comprueba parent == ledger_hash encadenado y recomputa anchor."""
    if not logs:
        return True, "empty"
    prev_anchor = genesis_ledger_hash()
    sorted_logs = sorted(logs, key=lambda x: x.get("timestamp", ""))
    for i, rec in enumerate(sorted_logs):
        lh = rec.get("ledger_hash", "")
        if not _HEX64.match(lh or ""):
            return False, f"idx{i}: ledger_hash invalido"
        if lh.lower() != prev_anchor.lower():
            return False, f"idx{i}: cadena rota esperado {prev_anchor} got {lh}"
        canon = build_canonical_unsigned(
            rec["event_id"],
            rec["timestamp"],
            rec["unit_id"],
            rec["decision"],
            rec["telemetry_snapshot"],
            lh,
            rec.get("mission_id"),
        )
        expect = compute_event_anchor_hash(lh, canon)
        got = rec.get("event_anchor_hash", "")
        if got.lower() != expect.lower():
            return False, f"idx{i}: anchor mismatch"
        prev_anchor = expect
    return True, "ok"


def sign_anchor_with_eth_dev_key(anchor_hex: str, private_key_hex: str) -> str:
    """Solo laboratorio: firma ECDSA del digest anchor (32 B). SE real replica sobre mismo digest."""
    try:
        from eth_account import Account
    except ImportError as e:
        raise RuntimeError("eth-account requerido para firma dev") from e
    h = bytes.fromhex(anchor_hex.replace("0x", ""))
    pk = private_key_hex.strip().removeprefix("0x")
    acct = Account.from_key(pk)
    sig = Account.unsafe_sign_hash(h, private_key=acct.key)
    return "0x" + sig.signature.hex()
