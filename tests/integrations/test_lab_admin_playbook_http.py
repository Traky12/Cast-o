import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.trl6


@pytest.fixture()
def admin_token(monkeypatch):
    monkeypatch.setenv("CASTUO_ADMIN_GENERAL_BEARER", "playbook-test-admin-token")
    return "playbook-test-admin-token"


def test_admin_playbook_requires_bearer(admin_token):
    from backend.integrations.robotics.lab_stub_app import app

    c = TestClient(app)
    r = c.get("/admin_general/playbook")
    assert r.status_code == 401


def test_admin_playbook_ok(admin_token):
    from backend.integrations.robotics.lab_stub_app import app

    c = TestClient(app)
    r = c.get(
        "/admin_general/playbook",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["role"] == "admin_general"
    assert data["version"] == "2.5.5-20260316"
    assert "encryption_stack_detail" in data


def test_playbook_mutation_does_not_alter_template():
    from backend.models import system_admin_playbook as mod

    before = mod.ADMIN_GENERAL_PLAYBOOK["version"]
    p = mod.get_admin_general_playbook()
    p["version"] = "tampered"
    assert mod.ADMIN_GENERAL_PLAYBOOK["version"] == before
