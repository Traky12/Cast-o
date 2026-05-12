import os

import pytest

pytestmark = pytest.mark.trl6


def test_chain_register_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CASTUO_ROBOTICS_LAB_CHAIN_REGISTER", raising=False)
    from backend.integrations.robotics import lab_gaiachain_optional as mod

    assert mod.robotics_lab_chain_register_enabled() is False


def test_resolve_token_id_explicit():
    from backend.integrations.robotics.lab_gaiachain_optional import resolve_snapshot_token_id

    assert resolve_snapshot_token_id(7) == 7


def test_chain_status_misconfigured(monkeypatch):
    monkeypatch.setenv("CASTUO_ROBOTICS_LAB_CHAIN_REGISTER", "1")
    from backend.integrations.robotics import lab_gaiachain_optional as mod

    assert mod.robotics_lab_chain_status() == "misconfigured"


def test_build_snapshot_payload_minimal():
    from backend.integrations.robotics.lab_gaiachain_optional import build_snapshot_audit_payload

    p = build_snapshot_audit_payload(
        token_id=1,
        action="PEI001_SNAPSHOT",
        status="REGISTERED",
        digest_with_prefix="sha256:abc",
        parcel_id="EX-1",
        neuromorphic=None,
    )
    assert p["tokenId"] == 1
    assert p["details"]["digest"] == "sha256:abc"
    assert "parcel_ref" not in p["details"]
