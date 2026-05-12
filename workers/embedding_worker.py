from __future__ import annotations

import json
import logging
import os
from typing import Any

from services.ai.semantic_memory import get_semantic_memory_service
from services.blockchain.graph_change_logger import GraphChangeLogger


logger = logging.getLogger("castuo.embedding_worker")
TOPIC = os.getenv("SEMANTIC_NOTES_TOPIC", "notes_to_process")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")


def process_note(note: dict[str, Any]) -> dict[str, Any]:
    semantic_memory = get_semantic_memory_service()
    logger_service = GraphChangeLogger()

    record = semantic_memory.upsert_note(
        note_id=str(note["id"]),
        content=str(note["content"]),
        metadata=dict(note.get("metadata", {})),
        path=str(note.get("path", "")),
    )
    edges = semantic_memory.enrich_graph(record.note_id, limit=3)
    trace = logger_service.log_change(
        "embedding_worker_processed",
        {
            "note_id": record.note_id,
            "relationships_added": len(edges),
            "topic": TOPIC,
        },
        actor="embedding_worker",
    )
    return {
        "note_id": record.note_id,
        "embedding_dim": len(record.embedding),
        "relationships_added": len(edges),
        "blockchain_txid": trace["txid"],
    }


def main() -> None:
    try:
        from kafka import KafkaConsumer  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - worker opcional
        raise RuntimeError("kafka-python no está instalado en este entorno") from exc

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_deserializer=lambda payload: json.loads(payload.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id=os.getenv("SEMANTIC_WORKER_GROUP", "semantic-memory-workers"),
    )

    logger.info("Embedding worker escuchando topic=%s bootstrap=%s", TOPIC, BOOTSTRAP_SERVERS)
    for message in consumer:
        try:
            result = process_note(dict(message.value))
            logger.info("Nota procesada: %s", result)
        except Exception as exc:  # pragma: no cover - logging operativo
            logger.exception("Error procesando nota Kafka: %s", exc)


if __name__ == "__main__":  # pragma: no cover
    main()