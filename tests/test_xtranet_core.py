from backend.xtranet.core import CastuoDAO, XtranetCore


def test_dao_chain():
    d = CastuoDAO()
    assert len(d.blockchain) == 1
    h = d.add_audit_log({"test": 1})
    assert len(h) == 128
    assert d.blockchain[-1].previous_hash == d.blockchain[-2].hash


def test_xtranet_cycle():
    x = XtranetCore()
    h = x.execute_hyper_automation({"nfc": "UID-1", "co2": 1.2, "biomass_type": "CHLORELLA-5PRO"})
    assert len(h) == 128
    assert "BIOC-UID-1" in x.bio_assets.assets
