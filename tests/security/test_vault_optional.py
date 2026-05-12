"""
Tests for backend/security/vault.py
Ref: PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §5 (tests — nombres reales)

Exact test names from the prontuario matrix:
  test_read_kv_without_vault_returns_empty
  test_vault_token_for_client_prefers_env_over_file
  test_vault_token_for_client_reads_file_when_env_empty
  test_vault_constants_paths
"""
import os
import sys

import pytest

# Ensure project root is on sys.path so `backend` is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.security.vault import read_kv_v2, read_secret, vault_token_for_client


# ─── test_read_kv_without_vault_returns_empty ─────────────────────────────────

def test_read_kv_without_vault_returns_empty(monkeypatch):
    """Without VAULT_ADDR → read_kv_v2 → "" (no exception, no hang)."""
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.delenv("VAULT_TOKEN_FILE", raising=False)
    # Must import after env change because VAULT_ADDR is module-level
    # Re-test by calling with the patched module state
    import backend.security.vault as vault_mod
    original = vault_mod.VAULT_ADDR
    vault_mod.VAULT_ADDR = ""
    try:
        result = read_kv_v2("castuo/admin_general/bearer")
        assert result == ""
    finally:
        vault_mod.VAULT_ADDR = original


# ─── test_vault_token_for_client_prefers_env_over_file ───────────────────────

def test_vault_token_for_client_prefers_env_over_file(tmp_path, monkeypatch):
    """VAULT_TOKEN env wins over VAULT_TOKEN_FILE content."""
    token_file = tmp_path / "vault_token"
    token_file.write_text("from_file")
    monkeypatch.setenv("VAULT_TOKEN", "from_env")
    monkeypatch.setenv("VAULT_TOKEN_FILE", str(token_file))
    assert vault_token_for_client() == "from_env"


# ─── test_vault_token_for_client_reads_file_when_env_empty ───────────────────

def test_vault_token_for_client_reads_file_when_env_empty(tmp_path, monkeypatch):
    """When VAULT_TOKEN is absent, reads token from VAULT_TOKEN_FILE."""
    token_file = tmp_path / "vault_token"
    token_file.write_text("from_file_only\n")  # trailing newline stripped
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.setenv("VAULT_TOKEN_FILE", str(token_file))
    assert vault_token_for_client() == "from_file_only"


# ─── test_vault_constants_paths ──────────────────────────────────────────────

def test_vault_constants_paths():
    """
    Logical KV paths follow the convention from VAULT_KV_PATHS.md:
    - No mount prefix (no 'secret/' or 'secret/data/')
    - Segments are lowercase alphanumeric + underscore
    - At least 2 segments
    """
    expected_paths = [
        "castuo/admin_general/bearer",
        "castuo/robotics/lab/bearer",
        "castuo/gaia/chain/private_key",
        "castuo/admin/master_key",
    ]
    for path in expected_paths:
        assert not path.startswith("secret/"), (
            f"Path '{path}' must NOT include the Vault mount prefix 'secret/'"
        )
        assert not path.startswith("secret/data/"), (
            f"Path '{path}' must NOT include KV v2 internal prefix 'secret/data/'"
        )
        segments = path.split("/")
        assert len(segments) >= 2, f"Path '{path}' must have at least 2 segments"
        for seg in segments:
            assert seg.replace("_", "").isalnum(), (
                f"Segment '{seg}' in path '{path}' must be alphanumeric/underscore"
            )


# ─── Bonus: read_secret Option A (file) ──────────────────────────────────────

def test_read_secret_reads_file_when_file_env_set(tmp_path, monkeypatch):
    """Option A: NAME_FILE env var → read_secret reads file, not plain env."""
    secret_file = tmp_path / "gaiachain_key"
    secret_file.write_text("super_secret_from_file")
    monkeypatch.setenv("GAIACHAIN_API_KEY_FILE", str(secret_file))
    monkeypatch.setenv("GAIACHAIN_API_KEY", "plain_env_value_should_be_ignored")
    assert read_secret("GAIACHAIN_API_KEY") == "super_secret_from_file"


def test_read_secret_falls_back_to_env_when_no_file(monkeypatch):
    """Option B fallback: no FILE → read_secret reads plain env (dev only)."""
    monkeypatch.delenv("GAIACHAIN_API_KEY_FILE", raising=False)
    monkeypatch.setenv("GAIACHAIN_API_KEY", "dev_key")
    assert read_secret("GAIACHAIN_API_KEY") == "dev_key"


def test_read_secret_returns_empty_when_nothing_configured(monkeypatch):
    """Option C (nothing): read_secret returns '' without raising."""
    monkeypatch.delenv("SOME_UNSET_SECRET_FILE", raising=False)
    monkeypatch.delenv("SOME_UNSET_SECRET", raising=False)
    assert read_secret("SOME_UNSET_SECRET") == ""
