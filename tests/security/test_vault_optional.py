"""vault.py sin hvac / sin VAULT_TOKEN debe fallar silencioso (cadena vacía)."""

import os

import pytest

pytestmark = pytest.mark.trl6


def test_read_kv_without_vault_returns_empty(monkeypatch):
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.delenv("VAULT_TOKEN_FILE", raising=False)
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    from backend.security import vault as v

    assert v.read_kv_v2("castuo/admin_general/bearer") == ""


def test_vault_token_for_client_prefers_env_over_file(monkeypatch, tmp_path):
    p = tmp_path / "vault_token"
    p.write_text("fromfile\n", encoding="utf-8")
    monkeypatch.setenv("VAULT_TOKEN", "fromenv")
    monkeypatch.setenv("VAULT_TOKEN_FILE", str(p))
    from backend.security import vault as v

    assert v.vault_token_for_client() == "fromenv"


def test_vault_token_for_client_reads_file_when_env_empty(monkeypatch, tmp_path):
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    p = tmp_path / "vault_token"
    p.write_text("tok-from-disk", encoding="utf-8")
    monkeypatch.setenv("VAULT_TOKEN_FILE", str(p))
    from backend.security import vault as v

    assert v.vault_token_for_client() == "tok-from-disk"


def test_vault_constants_paths():
    from backend.security.vault import (
        PATH_ADMIN_GENERAL_BEARER,
        PATH_ADMIN_MASTER_KEY,
        PATH_GAIA_CHAIN_PRIVATE_KEY,
        PATH_ROBOTICS_LAB_BEARER,
    )

    assert "admin_general" in PATH_ADMIN_GENERAL_BEARER
    assert "robotics" in PATH_ROBOTICS_LAB_BEARER
    assert "gaia" in PATH_GAIA_CHAIN_PRIVATE_KEY
    assert "admin" in PATH_ADMIN_MASTER_KEY
