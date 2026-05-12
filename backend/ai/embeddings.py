# backend/ai/embeddings.py — Embeddings para búsqueda semántica (Mistral o fallback)

from __future__ import annotations

import hashlib
import logging
from typing import List

logger = logging.getLogger(__name__)

try:
    from mistralai.client import MistralClient
    _MISTRAL = True
except ImportError:
    MistralClient = None
    _MISTRAL = False


class EmbeddingManager:
    """Generación de embeddings (Mistral o fallback determinista)."""

    def __init__(self) -> None:
        self._client = None
        if _MISTRAL:
            import os
            key = os.getenv("MISTRAL_API_KEY_EU", "")
            if key:
                try:
                    self._client = MistralClient(api_key=key)
                except Exception as e:
                    logger.debug("Mistral embeddings no disponible: %s", e)
        self._dim = 1024

    def generate_embedding(self, text: str) -> List[float]:
        if self._client:
            try:
                r = self._client.embeddings(model="mistral-embed", input=[text])
                if r.data:
                    return r.data[0].embedding
            except Exception as e:
                logger.debug("Embedding Mistral falló: %s", e)
        h = hashlib.sha3_512(text.encode()).digest()
        return [((b - 128) / 128.0) for b in h[: self._dim]] if len(h) >= self._dim else [0.0] * self._dim

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        if na * nb == 0:
            return 0.0
        return dot / (na * nb)
