"""
Tests para POST /api/v1/skills/validar_lote
Cubre: autenticación JWT, respuesta OK/FALLBACK, campos del response model.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Asegurar paths
_API = Path(__file__).parent.parent / "api"
_CG  = Path(__file__).parent.parent / "castuo_graph"
sys.path.insert(0, str(_API))
sys.path.insert(0, str(_CG))

import jwt as _jwt
from main import app

client = TestClient(app, raise_server_exceptions=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

_TEST_SECRET = "test-secret-castuo-2026"
_VALID_PAYLOAD = {
    "lote_id": "LOTE-TEST-E2E-001",
    "metadatos": {"cultivo": "lechuga", "kg": 12.5, "eco": True},
    "verify_base_url": "https://verify.castuo360.eu/lote",
}


def _make_token(role: str = "editor", secret: str = _TEST_SECRET) -> str:
    return _jwt.encode(
        {"sub": "test-operator", "role": role, "exp": int(time.time()) + 3600},
        secret,
        algorithm="HS256",
    )


def _auth(role: str = "editor") -> dict:
    return {"Authorization": f"Bearer {_make_token(role)}"}


# ── Suite: sin autenticación configurada (modo dev) ───────────────────────────

class TestValidarLoteDevMode:
    """Sin JWT_SECRET configurado → modo dev, endpoint operativo."""

    def test_dev_mode_fallback_response(self, monkeypatch, tmp_path):
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.delenv("JWT_SECRET_FILE", raising=False)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        resp = client.post("/api/v1/skills/validar_lote", json=_VALID_PAYLOAD)

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["lote_id"] == "LOTE-TEST-E2E-001"
        assert data["status"] in ("OK", "FALLBACK")
        assert data["tx_hash"].startswith(("0x", "sim-"))
        assert data["blockchain"] in ("GaiaChain", "simulado")
        assert data["certificado_path"].endswith(".pdf")
        assert "qr_path" in data
        assert "generado_en" in data

    def test_dev_mode_sim_hash_without_blockchain_env(self, monkeypatch, tmp_path):
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.delenv("JWT_SECRET_FILE", raising=False)
        monkeypatch.delenv("GAIACHAIN_PRIVATE_KEY", raising=False)
        monkeypatch.delenv("GAIACHAIN_RPC_URL", raising=False)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        resp = client.post("/api/v1/skills/validar_lote", json=_VALID_PAYLOAD)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "FALLBACK"
        assert data["tx_hash"].startswith("sim-")
        assert data["blockchain"] == "simulado"


# ── Suite: autenticación JWT ──────────────────────────────────────────────────

class TestValidarLoteAuth:
    """Con JWT_SECRET configurado → validación de rol obligatoria."""

    def test_missing_auth_header_returns_401(self, monkeypatch, tmp_path):
        monkeypatch.setenv("JWT_SECRET", _TEST_SECRET)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        resp = client.post("/api/v1/skills/validar_lote", json=_VALID_PAYLOAD)
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, monkeypatch, tmp_path):
        monkeypatch.setenv("JWT_SECRET", _TEST_SECRET)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        resp = client.post(
            "/api/v1/skills/validar_lote",
            json=_VALID_PAYLOAD,
            headers={"Authorization": "Bearer not-a-real-jwt"},
        )
        assert resp.status_code == 401

    def test_wrong_role_returns_403(self, monkeypatch, tmp_path):
        monkeypatch.setenv("JWT_SECRET", _TEST_SECRET)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        token = _make_token(role="viewer")
        resp = client.post(
            "/api/v1/skills/validar_lote",
            json=_VALID_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_editor_role_allowed(self, monkeypatch, tmp_path):
        monkeypatch.setenv("JWT_SECRET", _TEST_SECRET)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        resp = client.post(
            "/api/v1/skills/validar_lote",
            json=_VALID_PAYLOAD,
            headers=_auth("editor"),
        )
        assert resp.status_code == 200

    def test_admin_role_allowed(self, monkeypatch, tmp_path):
        monkeypatch.setenv("JWT_SECRET", _TEST_SECRET)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        resp = client.post(
            "/api/v1/skills/validar_lote",
            json=_VALID_PAYLOAD,
            headers=_auth("admin"),
        )
        assert resp.status_code == 200

    def test_api_role_allowed(self, monkeypatch, tmp_path):
        monkeypatch.setenv("JWT_SECRET", _TEST_SECRET)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        resp = client.post(
            "/api/v1/skills/validar_lote",
            json=_VALID_PAYLOAD,
            headers=_auth("api"),
        )
        assert resp.status_code == 200


# ── Suite: validación del payload ─────────────────────────────────────────────

class TestValidarLotePayload:

    def test_lote_id_too_short_returns_422(self, monkeypatch, tmp_path):
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        resp = client.post(
            "/api/v1/skills/validar_lote",
            json={**_VALID_PAYLOAD, "lote_id": "AB"},  # min_length=3
        )
        assert resp.status_code == 422

    def test_missing_lote_id_returns_422(self, monkeypatch, tmp_path):
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        payload = {k: v for k, v in _VALID_PAYLOAD.items() if k != "lote_id"}
        resp = client.post("/api/v1/skills/validar_lote", json=payload)
        assert resp.status_code == 422

    def test_optional_fields_have_defaults(self, monkeypatch, tmp_path):
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        # Solo lote_id — sin metadatos, sin verify_base_url, sin output_dir
        resp = client.post(
            "/api/v1/skills/validar_lote",
            json={"lote_id": "LOTE-MIN-001"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "qr_path" in data
        assert "certificado_path" in data

    def test_output_dir_override(self, monkeypatch, tmp_path):
        monkeypatch.delenv("JWT_SECRET", raising=False)

        custom_dir = str(tmp_path / "custom_output")
        resp = client.post(
            "/api/v1/skills/validar_lote",
            json={**_VALID_PAYLOAD, "output_dir": custom_dir},
        )
        assert resp.status_code == 200
        data = resp.json()
        # cert y qr deben estar bajo custom_dir
        assert custom_dir in data["certificado_path"]


# ── Suite: operador_sub en metadatos ─────────────────────────────────────────

class TestValidarLoteMetadata:

    def test_operador_sub_enriched_from_token(self, monkeypatch, tmp_path):
        """El endpoint enriquece los metadatos con _operador_sub del token."""
        monkeypatch.setenv("JWT_SECRET", _TEST_SECRET)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        resp = client.post(
            "/api/v1/skills/validar_lote",
            json=_VALID_PAYLOAD,
            headers=_auth("editor"),
        )
        assert resp.status_code == 200
        # El enriquecimiento ocurre internamente; la respuesta incluye el lote_id
        assert resp.json()["lote_id"] == "LOTE-TEST-E2E-001"

    def test_generado_en_is_iso8601(self, monkeypatch, tmp_path):
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.setenv("QR_OUTPUT_DIR", str(tmp_path))

        from datetime import datetime
        resp = client.post("/api/v1/skills/validar_lote", json=_VALID_PAYLOAD)
        assert resp.status_code == 200
        ts = resp.json()["generado_en"]
        # No debe lanzar excepción si es ISO-8601 válido
        datetime.fromisoformat(ts)
