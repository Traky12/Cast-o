from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import jwt
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from main import app
from services.ai.semantic_memory import get_semantic_memory_service


client = TestClient(app)
JWT_SECRET = "test-semantic-secret"


def _auth_header(roles: list[str]) -> dict[str, str]:
    payload = {
        "sub": "pytest-semantic",
        "roles": roles,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_semantic_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", JWT_SECRET)
    service = get_semantic_memory_service()
    service.reset()


def test_extract_notes_returns_hash_and_queue_status() -> None:
    response = client.post(
        "/api/v1/notes/extract",
        headers=_auth_header(["tecnico"]),
        json=[
            {
                "id": "nota-1",
                "content": "La agricultura regenerativa mejora el suelo y la resiliencia.",
                "metadata": {"source": "obsidian", "tags": ["suelo", "agro"]},
                "path": "Vault/nota-1.md",
            }
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["notes"][0]["status"] == "queued"
    assert len(body["notes"][0]["hash"]) == 64


def test_generate_embeddings_links_similar_notes() -> None:
    first = client.post(
        "/api/v1/embeddings/generate",
        headers=_auth_header(["tecnico"]),
        json={
            "id": "nota-1",
            "content": "La agricultura de precision usa sensores IoT y analitica para optimizar riego.",
            "metadata": {"source": "obsidian"},
            "path": "Vault/nota-1.md",
        },
    )
    second = client.post(
        "/api/v1/embeddings/generate",
        headers=_auth_header(["tecnico"]),
        json={
            "id": "nota-2",
            "content": "La agricultura de precision combina IoT, datos y modelos para optimizar riego y fertilizacion.",
            "metadata": {"source": "logseq"},
            "path": "Graph/nota-2.md",
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200

    body = second.json()
    assert body["note_id"] == "nota-2"
    assert body["embedding_dim"] > 0
    assert body["blockchain_txid"].startswith("local-")
    assert any(item["note_id"] == "nota-1" for item in body["similar_notes"])


def test_graph_endpoints_return_nodes_relationships_and_xr_positions() -> None:
    client.post(
        "/api/v1/embeddings/generate",
        headers=_auth_header(["tecnico"]),
        json={
            "id": "nota-1",
            "content": "Embeddings semanticos para notas de campo.",
            "metadata": {"agent": "sabionda"},
            "path": "Vault/nota-1.md",
        },
    )
    client.post(
        "/api/v1/embeddings/generate",
        headers=_auth_header(["tecnico"]),
        json={
            "id": "nota-2",
            "content": "Grafo semantico con agentes, conceptos y notas relacionadas.",
            "metadata": {"agent": "sabionda"},
            "path": "Vault/nota-2.md",
        },
    )

    graph_response = client.get("/api/v1/graph", headers=_auth_header(["auditor"]))
    xr_response = client.get("/api/v1/graph/xr", headers=_auth_header(["auditor"]))

    assert graph_response.status_code == 200
    assert xr_response.status_code == 200

    graph = graph_response.json()
    xr_graph = xr_response.json()

    assert len(graph["nodes"]) == 2
    assert "relationships" in graph
    assert all("x" in node and "y" in node for node in graph["nodes"])
    assert all("z" in node for node in xr_graph["nodes"])


def test_update_graph_returns_blockchain_trace() -> None:
    client.post(
        "/api/v1/embeddings/generate",
        headers=_auth_header(["tecnico"]),
        json={
            "id": "nota-1",
            "content": "El agente conecta notas y conceptos del cultivo.",
            "metadata": {"agent": "sabionda"},
            "path": "Vault/nota-1.md",
        },
    )
    client.post(
        "/api/v1/embeddings/generate",
        headers=_auth_header(["tecnico"]),
        json={
            "id": "nota-2",
            "content": "El cultivo y el agente comparten relaciones semanticas fuertes.",
            "metadata": {"agent": "sabionda"},
            "path": "Vault/nota-2.md",
        },
    )

    response = client.post(
        "/api/v1/neo4j/update",
        headers=_auth_header(["tecnico"]),
        json={"note_id": "nota-2", "limit": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "updated"
    assert body["blockchain_txid"].startswith("local-")
    assert body["relationships_added"] >= 0