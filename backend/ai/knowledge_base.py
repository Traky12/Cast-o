# backend/ai/knowledge_base.py — Base de conocimiento federada (GaiaChain, embeddings, GDPR Art.17)

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from backend.security.pq_crypto import PostQuantumCrypto
    _CRYPTO = True
except ImportError:
    PostQuantumCrypto = None
    _CRYPTO = False

try:
    from backend.ai.embeddings import EmbeddingManager
    _EMBED = True
except ImportError:
    EmbeddingManager = None
    _EMBED = False


class KnowledgeBase:
    """
    Base de conocimiento federada: cache local, embeddings, consultas a GaiaChain opcionales.
    Cumplimiento GDPR Art. 30 (registro) y Art. 17 (derecho al olvido).
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.crypto: Any = PostQuantumCrypto() if _CRYPTO else None
        self.embeddings = EmbeddingManager() if _EMBED else None
        self.local_cache: Dict[str, Dict] = {}

    def get_product_embeddings(self, product_ids: List[str]) -> Dict[str, Dict]:
        result: Dict[str, Dict] = {}
        for pid in product_ids:
            if pid in self.local_cache:
                result[pid] = self.local_cache[pid]
            else:
                data = self._query_gaiachain(f"product:{pid}")
                if data:
                    if self.embeddings:
                        data["embedding"] = self.embeddings.generate_embedding(
                            f"{data.get('name', '')}: {data.get('description', '')}"
                        )
                    self.local_cache[pid] = data
                    result[pid] = data
        return result

    def _query_gaiachain(self, key: str) -> Optional[Dict]:
        script = os.path.join(os.path.dirname(__file__), "..", "scripts", "query_gaiachain.py")
        if not os.path.isfile(script):
            return None
        try:
            r = subprocess.run(
                [os.environ.get("PYTHON", "python"), script, "--key", key],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.path.dirname(__file__) or ".",
            )
            if r.returncode != 0 or not r.stdout:
                return None
            data = json.loads(r.stdout)
            if isinstance(data, dict) and data.get("encrypted") and self.crypto:
                return json.loads(self.crypto.hybrid_decrypt(data["data"]))
            return data if isinstance(data, dict) else None
        except Exception as e:
            self.logger.debug("query_gaiachain %s: %s", key, e)
            return None

    def get_events_for_date(self, date_str: str) -> List[Dict]:
        script = os.path.join(os.path.dirname(__file__), "..", "scripts", "query_gaiachain.py")
        if not os.path.isfile(script):
            return []
        try:
            r = subprocess.run(
                [os.environ.get("PYTHON", "python"), script, "--type", "events", "--date", date_str],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode != 0 or not r.stdout:
                return []
            data = json.loads(r.stdout)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and data.get("encrypted") and self.crypto:
                return json.loads(self.crypto.hybrid_decrypt(data["data"]))
            return [data] if isinstance(data, dict) else []
        except Exception as e:
            self.logger.debug("get_events_for_date: %s", e)
            return []

    def get_market_trends(self) -> Dict:
        script = os.path.join(os.path.dirname(__file__), "..", "scripts", "query_gaiachain.py")
        if not os.path.isfile(script):
            return {"trends": [], "last_updated": datetime.utcnow().isoformat()}
        try:
            r = subprocess.run(
                [os.environ.get("PYTHON", "python"), script, "--type", "market_trends", "--limit", "7"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode != 0 or not r.stdout:
                return {"trends": [], "last_updated": datetime.utcnow().isoformat()}
            data = json.loads(r.stdout)
            if isinstance(data, dict) and data.get("encrypted") and self.crypto:
                data = json.loads(self.crypto.hybrid_decrypt(data["data"]))
            return data if isinstance(data, dict) else {"trends": [], "last_updated": datetime.utcnow().isoformat()}
        except Exception as e:
            self.logger.debug("get_market_trends: %s", e)
            return {"trends": [], "last_updated": datetime.utcnow().isoformat()}

    def search_semantic(self, query: str, top_k: int = 3) -> List[Dict]:
        if not self.embeddings:
            return []
        qe = self.embeddings.generate_embedding(query)
        results: List[tuple] = []
        for item_id, item in self.local_cache.items():
            if "embedding" in item:
                sim = self.embeddings.cosine_similarity(qe, item["embedding"])
                results.append((sim, item))
        results.sort(key=lambda x: x[0], reverse=True)
        return [item for (_, item) in results[:top_k]]

    def forget(self, knowledge_id: str) -> bool:
        """GDPR Art. 17: derecho al olvido."""
        if knowledge_id in self.local_cache:
            del self.local_cache[knowledge_id]
        script = os.path.join(os.path.dirname(__file__), "..", "scripts", "register_gaiachain_event.py")
        if not os.path.isfile(script) or not self.crypto:
            return True
        try:
            payload = {"action": "forget", "knowledge_id": knowledge_id, "timestamp": datetime.utcnow().isoformat(), "gdpr_article": "Art.17"}
            enc = self.crypto.hybrid_encrypt_large(json.dumps(payload))
            subprocess.run(
                [os.environ.get("PYTHON", "python"), script, "--event_type", "gdpr_forget", "--details", json.dumps(enc), "--norms", "GDPR:Art.17"],
                check=False,
                timeout=30,
            )
        except Exception as e:
            self.logger.debug("forget GaiaChain: %s", e)
        return True
