import pytest

from backend.models.system_admin_playbook import (
    ADMIN_GENERAL_ROLE,
    get_admin_general_playbook,
)

pytestmark = pytest.mark.trl6


def test_playbook_has_no_secrets():
    p = get_admin_general_playbook()
    assert p["role"] == ADMIN_GENERAL_ROLE
    assert p["version"] == "2.5.5-20260316"
    assert "admin_master_layer" in p["encryption_stack"]
    assert any("pq_crypto" in x["modulo"] for x in p["encryption_stack_detail"])
    assert "llmnr_multicast_off" in p["critical_hardening_checks"]
    assert p["critical_hardening_checks"]["llmnr_multicast_off"]["expected"] == [
        "LLMNR=no",
        "MulticastDNS=no",
    ]
    assert "remediation" in p["critical_hardening_checks"]["udp_5355_evidence"]
    blob = str(p).lower()
    assert "0x" not in blob
    assert "password" not in blob


def test_check_permission_admin_general_governance():
    from backend.models.permissions import check_permission

    assert check_permission("admin_general", "governance", "read") is True
    assert check_permission("admin_general", "users", "ban") is True
