from __future__ import annotations

import hashlib
import logging
import math
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


logger = logging.getLogger("castuo.semantic_memory")
_TOKEN_RE = re.compile(r"[\w\-]{2,}", re.UNICODE)


@dataclass
class SemanticNote:
    note_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    path: str = ""
    content_hash: str = ""
    embedding: list[float] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SimilarityEdge:
    source: str
    target: str
    score: float
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SemanticMemoryService:
    def __init__(self) -> None:
        self.dimension = int(os.getenv("SEMANTIC_EMBEDDING_DIM", "32"))
        self.model_name = os.getenv("SEMANTIC_EMEDDING_MODEL", "hash-embedding-v1")
        self.requested_backend = os.getenv("SEMANTIC_VECTOR_BACKEND", "memory").lower()
        self.active_backend = "memory"
        self.notes: dict[str, SemanticNote] = {}
        self.edges: dict[tuple[str, str], SimilarityEdge] = {}
        self.queue: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.notes.clear()
        self.edges.clear()
        self.queue.clear()

    def queue_note(
        self,
        note_id: str,
        content: str,
        metadata: dict[str, Any],
        path: str,
    ) -> dict[str, Any]:
        content_hash = self.compute_content_hash(content)
        payload = {
            "id": note_id,
            "content": content,
            "metadata": metadata,
            "path": path,
            "hash": content_hash,
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }
        self.queue.append(payload)
        return payload

    def upsert_note(
        self,
        note_id: str,
        content: str,
        metadata: dict[str, Any],
        path: str,
    ) -> SemanticNote:
        embedding = self.generate_embedding(content)
        note = SemanticNote(
            note_id=note_id,
            content=content,
            metadata=metadata,
            path=path,
            content_hash=self.compute_content_hash(content),
            embedding=embedding,
        )
        self.notes[note_id] = note
        return note

    def generate_embedding(self, text: str) -> list[float]:
        encoder = self._load_sentence_transformer()
        if encoder is not None:
            vector = encoder.encode(text)
            return [float(value) for value in vector]

        tokens = _TOKEN_RE.findall(text.lower())
        if not tokens:
            tokens = [text.lower() or "empty"]

        vector = [0.0] * self.dimension
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for index in range(self.dimension):
                byte_value = digest[index % len(digest)]
                vector[index] += (byte_value / 255.0) * 2.0 - 1.0

        norm = math.sqrt(sum(component * component for component in vector)) or 1.0
        return [round(component / norm, 6) for component in vector]

    def search_similar_by_note(
        self,
        note_id: str,
        limit: int = 5,
        min_score: float = 0.15,
    ) -> list[dict[str, Any]]:
        note = self.notes.get(note_id)
        if note is None:
            return []

        matches: list[dict[str, Any]] = []
        for other in self.notes.values():
            if other.note_id == note_id:
                continue
            score = self._cosine_similarity(note.embedding, other.embedding)
            if score < min_score:
                continue
            matches.append(
                {
                    "note_id": other.note_id,
                    "score": round(score, 4),
                    "path": other.path,
                    "metadata": other.metadata,
                }
            )

        matches.sort(key=lambda item: float(item["score"]), reverse=True)
        return matches[:limit]

    def search_similar_by_text(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.15,
    ) -> list[dict[str, Any]]:
        query_embedding = self.generate_embedding(query)
        matches: list[dict[str, Any]] = []
        for note in self.notes.values():
            score = self._cosine_similarity(query_embedding, note.embedding)
            if score < min_score:
                continue
            matches.append(
                {
                    "note_id": note.note_id,
                    "score": round(score, 4),
                    "path": note.path,
                    "metadata": note.metadata,
                }
            )

        matches.sort(key=lambda item: float(item["score"]), reverse=True)
        return matches[:limit]

    def enrich_graph(self, note_id: str, limit: int = 3, min_score: float = 0.15) -> list[SimilarityEdge]:
        related = self.search_similar_by_note(note_id=note_id, limit=limit, min_score=min_score)
        created_edges: list[SimilarityEdge] = []
        for item in related:
            source, target = sorted((note_id, str(item["note_id"])))
            edge = SimilarityEdge(source=source, target=target, score=float(item["score"]))
            self.edges[(source, target)] = edge
            created_edges.append(edge)
        return created_edges

    def build_graph_projection(self, xr: bool = False) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        for note in self.notes.values():
            x, y, z = self._coords_from_embedding(note.embedding)
            node = {
                "id": note.note_id,
                "label": note.metadata.get("title") or note.note_id,
                "type": "Nota",
                "path": note.path,
                "metadata": note.metadata,
                "x": x,
                "y": y,
            }
            if xr:
                node["z"] = z
            nodes.append(node)

        relationships = [
            {
                "source": edge.source,
                "target": edge.target,
                "type": "SIMILAR_A",
                "score": round(edge.score, 4),
                "updated_at": edge.updated_at,
            }
            for edge in self.edges.values()
        ]

        return {
            "nodes": nodes,
            "relationships": relationships,
            "backend": self.active_backend,
            "model": self.model_name,
        }

    def compute_content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _load_sentence_transformer(self) -> Any | None:
        if os.getenv("SEMANTIC_USE_SENTENCE_TRANSFORMERS", "false").lower() != "true":
            return None

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

            self.active_backend = self.requested_backend
            return SentenceTransformer(os.getenv("SEMANTIC_EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
        except Exception as exc:  # pragma: no cover - fallback operativo
            logger.warning("SentenceTransformer no disponible, usando fallback hash: %s", exc)
            return None

    def _coords_from_embedding(self, embedding: list[float]) -> tuple[float, float, float]:
        if not embedding:
            return (0.0, 0.0, 0.0)
        x = round(embedding[0] * 20, 3)
        y = round(embedding[1 % len(embedding)] * 20, 3)
        z = round(embedding[2 % len(embedding)] * 20, 3)
        return (x, y, z)

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
        right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
        return numerator / (left_norm * right_norm)


_SEMANTIC_MEMORY = SemanticMemoryService()


def get_semantic_memory_service() -> SemanticMemoryService:
    return _SEMANTIC_MEMORY