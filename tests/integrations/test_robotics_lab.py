import json
import os
from pathlib import Path

import pytest

pytestmark = [pytest.mark.trl6, pytest.mark.trl7]

os.environ.setdefault("CASTUO_ROBOTICS_LAB", "1")


def test_signal_manager_roundtrip():
    from backend.integrations.robotics.signal_manager import SignalManager

    m = SignalManager("ROBOT-TEST")
    snap = m.simulated_radio_sample()
    enc = m.encrypt_snapshot(snap)
    dec = m.decrypt_snapshot(enc)
    assert dec.data_b64 == snap.data_b64
    m.log_snapshot(dec)
    assert len(m.history()) == 1


def test_evolution_engine_checkpoint(tmp_path: Path):
    from backend.integrations.robotics.evolution_engine import EvolutionEngine
    from backend.integrations.robotics.robot_traceability import build_robot_evolution_audit_payload

    eng = EvolutionEngine(population_size=16)
    state = eng.evolve(generations=3, genes=6)
    p = tmp_path / "ckpt.json"
    digest = eng.save_checkpoint(state, str(p), robot_id="R1")
    assert p.read_text(encoding="utf-8")
    payload = build_robot_evolution_audit_payload(
        token_id=1,
        robot_id="R1",
        state_or_checkpoint=state,
    )
    assert payload["tokenId"] == 1
    assert payload["details"]["digest"].startswith("sha256:")
    assert digest


def test_security_layer_roundtrip():
    from backend.integrations.robotics.security_layer import RobotSecurityLayer

    layer = RobotSecurityLayer("R-SEC")
    blob = layer.seal_utf8("comando:parar")
    opened = layer.open_sealed(blob)
    assert opened == "comando:parar"
    sig = layer.sign_payload("log:ok")
    assert layer.verify_payload("log:ok", sig)
