# tests/test_timestamping_service.py — Pruebas de TimestampingService (notarización TSA)

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def test_timestamping_service_get_timestamp():
    """get_timestamp devuelve sello con hash y status."""
    from backend.compliance.timestamping_service import TimestampingService

    ts = TimestampingService(tsa_url="http://nonexistent")
    data = b"evidence payload"
    result = ts.get_timestamp(data)
    assert "hash" in result
    assert "timestamp" in result
    assert result.get("status") in ("success", "error")
    if result["status"] == "success":
        assert "signature" in result or "policy" in result


def test_timestamping_service_verify_timestamp():
    """verify_timestamp valida estructura de sello."""
    from backend.compliance.timestamping_service import TimestampingService

    ts = TimestampingService()
    assert ts.verify_timestamp({"status": "success", "hash": "abc"}) is True
    assert ts.verify_timestamp({"status": "error"}) is False
    assert ts.verify_timestamp({}) is False


def test_immutable_traceability_timestamping_for_critical_events():
    """Eventos forensic_evidence, security_incident, key_rotation reciben timestamping."""
    from backend.security.end_to_end_encryption import EndToEndEncryption
    from backend.compliance.immutable_traceability import ImmutableTraceability

    enc = EndToEndEncryption()
    trace = ImmutableTraceability(enc)
    assert trace.timestamping_service is not None
    assert "forensic_evidence" in trace._timestamping_event_types
    assert "security_incident" in trace._timestamping_event_types
    assert "key_rotation" in trace._timestamping_event_types

    trace.register_event({"type": "forensic_evidence", "data": "test"})
    assert len(trace.current_chain) == 1
    assert "timestamping" in trace.current_chain[0]
    ts_data = trace.current_chain[0]["timestamping"]
    assert ts_data.get("status") == "success"
    assert "hash" in ts_data
