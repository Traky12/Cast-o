"""Tests para el router de registro en blockchain (GaiaChain)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest
import jwt
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from fastapi import FastAPI
    from api.routers.blockchain_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-blockchain-secret")


def _auth_header(roles: list[str]) -> dict[str, str]:
    payload = {
        "sub": "pytest-blockchain",
        "roles": roles,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()),
    }
    token = jwt.encode(payload, "test-blockchain-secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


class TestBlockchainLogEndpoint:
    """POST /api/v1/blockchain/log"""

    def test_log_event_returns_200_with_txid(self, client: TestClient) -> None:
        """Registro exitoso devuelve 200 con txid."""
        with patch("castuo_graph.blockchain.gaiachain.GaiachainConnector.register_hash") as mock_reg:
            mock_reg.return_value = "0xabc123deadbeef"
            resp = client.post(
                "/api/v1/blockchain/log",
                headers=_auth_header(["tecnico"]),
                json={
                    "event_type": "code_update",
                    "data": {"repo": "goldfish", "commit": "abc123"},
                    "actor": "github_actions",
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "txid" in body
        assert body["txid"] == "0xabc123deadbeef"

    def test_log_missing_event_type_returns_422(self, client: TestClient) -> None:
        """Falta event_type → 422."""
        resp = client.post(
            "/api/v1/blockchain/log",
            headers=_auth_header(["tecnico"]),
            json={"data": {"key": "val"}, "actor": "system"},
        )
        assert resp.status_code == 422

    def test_log_missing_actor_returns_422(self, client: TestClient) -> None:
        """Falta actor → 422."""
        resp = client.post(
            "/api/v1/blockchain/log",
            headers=_auth_header(["tecnico"]),
            json={"event_type": "test", "data": {}},
        )
        assert resp.status_code == 422

    def test_log_blockchain_error_returns_503(self, client: TestClient) -> None:
        """Error de GaiaChain → 503."""
        with patch("castuo_graph.blockchain.gaiachain.GaiachainConnector.register_hash") as mock_reg:
            mock_reg.side_effect = Exception("GaiaChain unreachable")
            resp = client.post(
                "/api/v1/blockchain/log",
                headers=_auth_header(["tecnico"]),
                json={
                    "event_type": "test",
                    "data": {"key": "value"},
                    "actor": "system",
                },
            )
        assert resp.status_code == 503

    def test_log_empty_event_type_returns_422(self, client: TestClient) -> None:
        """event_type vacío → 422."""
        resp = client.post(
            "/api/v1/blockchain/log",
            headers=_auth_header(["tecnico"]),
            json={"event_type": "", "data": {}, "actor": "system"},
        )
        assert resp.status_code == 422
