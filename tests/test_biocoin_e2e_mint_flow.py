"""E2E off-chain: evidence (NIR+geo) → manifest → firma oráculo compatible BioCoinVault."""
from __future__ import annotations

import pytest

from backend.biocoin.mint_message import mint_message_hash, sign_mint_oracle
from backend.biocoin.security_orchestrator import (
    build_manifest_canonical,
    compute_evidence_hash,
    evidence_score_from_layers,
    harvest_geolocation_digest,
    manifest_canonical_hash,
)

pytest.importorskip("eth_account")


def test_harvest_digest_stable():
    h1 = harvest_geolocation_digest(39.2, -6.1, decimals=5)
    h2 = harvest_geolocation_digest(39.2, -6.1, decimals=5)
    assert h1 == h2
    assert h1 != harvest_geolocation_digest(39.20001, -6.1, decimals=5)


def test_evidence_nir_geo_binding():
    geo = harvest_geolocation_digest(40.0, -5.0)
    a = compute_evidence_hash("CASTUO-042", "nir_payload_A", geo)
    b = compute_evidence_hash("CASTUO-042", "nir_payload_B", geo)
    assert a != b
    piezo = compute_evidence_hash("CASTUO-042", "nir_payload_A", geo, piezo_baseline_normalized="1.02e6")
    assert piezo != compute_evidence_hash("CASTUO-042", "nir_payload_A", geo, piezo_baseline_normalized="1.03e6")


def test_piezo_tamper_zeroes_evidence_score():
    assert evidence_score_from_layers(1.0, False, 1.0) == 0
    assert evidence_score_from_layers(0.9, True, 0.95) > 9000


def test_sign_mint_oracle_matches_vault_msg_hash():
    from eth_account import Account

    acct = Account.create()
    ev = compute_evidence_hash("X", "nir", "geo")
    manifest = build_manifest_canonical("X", "EXT", 42.0)
    mh = manifest_canonical_hash(manifest)
    ev_h = "0x" + ev.hex()
    v, r, s = sign_mint_oracle(ev_h, mh, 7, acct.address, acct.address, 137, acct.key.hex())
    msg_hash = mint_message_hash(ev, bytes.fromhex(mh[2:]), 7, acct.address, acct.address, 137)
    sig_bytes = int(r, 16).to_bytes(32, "big") + int(s, 16).to_bytes(32, "big")
    recovered = Account._recover_hash(msg_hash, vrs=(v, int(r, 16), int(s, 16)))
    assert recovered.lower() == acct.address.lower()
