from __future__ import annotations

import hashlib
from dataclasses import dataclass
from math import sqrt
from typing import Any


@dataclass
class SemanticNote:
    note_id: str
    content: str
    metadata: dict[str, Any]
    path: str
    content_hash: str
    embedding: list[float]


class _SemanticMemoryService:
    """Servicio de memoria semántica con fallback in-memory para entornos dev."""

    def __init__(self) -> None:
        self._notes: dict[str, SemanticNote] = {}
        self._edges: set[tuple[str, str]] = set()
        self.active_backend = "in-memory"
        self.model_name = "hash-embedding-v1"

    @property
    def notes(self) -> dict[str, SemanticNote]:
        return self._notes

    def reset(self) -> None:
        self._notes.clear()
        self._edges.clear()

    def _embed(self, text: str, dims: int = 16) -> list[float]:
        base = hashlib.sha256(text.lower().strip().encode("utf-8")).digest()
        values = [((base[i] / 255.0) * 2.0) - 1.0 for i in range(dims)]
        norm = sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        return sum(x * y for x, y in zip(a, b, strict=False))

    def upsert_note(
        self,
        *,
        note_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        path: str,
    ) -> SemanticNote:
        content_hash = hashlib.sha256(f"{note_id}:{content}:{path}".encode("utf-8")).hexdigest()
        note = SemanticNote(
            note_id=note_id,
            content=content,
            metadata=metadata or {},
            path=path,
            content_hash=content_hash,
            embedding=self._embed(content),
        )
        self._notes[note_id] = note
        return note

    def add_note(self, text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        note_id = str(len(self._notes) + 1)
        note = self.upsert_note(note_id=note_id, content=text, metadata=metadata or {}, path=f"memory/{note_id}.md")
        return {
            "id": note.note_id,
            "text": note.content,
            "metadata": note.metadata,
            "path": note.path,
            "hash": note.content_hash,
        }

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        q = query.lower().strip()
        results = [
            {
                "id": n.note_id,
                "text": n.content,
                "metadata": n.metadata,
                "path": n.path,
            }
            for n in self._notes.values()
            if q in n.content.lower()
        ]
        return results[:limit]

    def queue_note(
        self,
        *,
        note_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        path: str,
    ) -> dict[str, Any]:
        note = self.upsert_note(
            note_id=note_id,
            content=content,
            metadata=metadata or {},
            path=path,
        )
        return {
            "id": note.note_id,
            "content": note.content,
            "metadata": note.metadata,
            "path": note.path,
            "hash": note.content_hash,
        }

    def search_similar_by_note(self, note_id: str, limit: int = 5) -> list[dict[str, Any]]:
        source = self._notes.get(note_id)
        if source is None:
            return []

        ranked: list[tuple[float, SemanticNote]] = []
        for other in self._notes.values():
            if other.note_id == note_id:
                continue
            score = self._cosine_similarity(source.embedding, other.embedding)
            ranked.append((score, other))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "note_id": n.note_id,
                "path": n.path,
                "score": round(score, 6),
            }
            for score, n in ranked[:limit]
        ]

    def search_similar_by_text(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_embedding = self._embed(query)
        ranked: list[tuple[float, SemanticNote]] = []
        for note in self._notes.values():
            score = self._cosine_similarity(query_embedding, note.embedding)
            ranked.append((score, note))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "note_id": note.note_id,
                "path": note.path,
                "score": round(score, 6),
            }
            for score, note in ranked[:limit]
        ]

    def enrich_graph(self, note_id: str, limit: int = 3) -> list[dict[str, Any]]:
        edges: list[dict[str, Any]] = []
        for similar in self.search_similar_by_note(note_id, limit=limit):
            src, dst = sorted((note_id, similar["note_id"]))
            self._edges.add((src, dst))
            edges.append({"source": src, "target": dst, "weight": similar["score"]})
        return edges

    def build_graph_projection(self, xr: bool = False) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        for idx, note in enumerate(self._notes.values()):
            node = {
                "id": note.note_id,
                "path": note.path,
                "x": float(idx),
                "y": float((idx % 3) - 1),
            }
            if xr:
                node["z"] = float((idx % 5) * 0.5)
            nodes.append(node)

        relationships = [
            {"source": source, "target": target}
            for source, target in sorted(self._edges)
        ]
        return {"nodes": nodes, "relationships": relationships}


_SERVICE = _SemanticMemoryService()


def get_semantic_memory_service() -> _SemanticMemoryService:
    return _SERVICE
