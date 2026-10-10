"""Durable LangGraph runtime for CASTÚO.

The runtime is intentionally local-first. SQLite is suitable for deterministic
validation and single-node staging; production promotion remains blocked until
PostgreSQL/TimescaleDB checkpointing, backup/restore and remote observability
are separately verified.
"""
from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

try:  # package import
    from .graph import build_graph, build_initial_state
except ImportError:  # direct module execution from castuo_graph/
    from graph import build_graph, build_initial_state

GRAPH_VERSION = "casto-langgraph-3.1.0-durable-sqlite-v1"


class DurableAgentRuntime:
    """Run and resume the CASTÚO graph with a persistent checkpoint store."""

    def __init__(self, checkpoint_path: str | os.PathLike[str] | None = None) -> None:
        configured = checkpoint_path or os.getenv("CASTUO_CHECKPOINT_PATH", "./data/castuo-checkpoints.sqlite")
        self.checkpoint_path = Path(configured).expanduser()
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def _compiled(self) -> AsyncIterator[Any]:
        async with AsyncSqliteSaver.from_conn_string(str(self.checkpoint_path)) as saver:
            await saver.setup()
            yield build_graph(checkpointer=saver)

    @staticmethod
    def _config(thread_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": thread_id}}

    async def run(self, initial_state: dict[str, Any], thread_id: str | None = None) -> dict[str, Any]:
        thread_id = thread_id or f"thread-{uuid.uuid4()}"
        run_id = f"run-{uuid.uuid4()}"
        state = build_initial_state(initial_state)
        state.update(
            {
                "thread_id": thread_id,
                "run_id": run_id,
                "graph_version": GRAPH_VERSION,
                "resumed_from_checkpoint": False,
                "recovery_state": "cold_start",
            }
        )
        async with self._compiled() as graph:
            final_state = await graph.ainvoke(state, config=self._config(thread_id))
            snapshot = await graph.aget_state(self._config(thread_id))
        return self._result(final_state, thread_id, run_id, snapshot)

    async def resume(self, thread_id: str, values: dict[str, Any] | None = None) -> dict[str, Any]:
        run_id = f"run-{uuid.uuid4()}"
        config = self._config(thread_id)
        async with self._compiled() as graph:
            current = await graph.aget_state(config)
            if current is None or not current.values:
                raise KeyError(f"unknown_thread_id:{thread_id}")
            update = dict(values or {})
            update.update(
                {
                    "thread_id": thread_id,
                    "run_id": run_id,
                    "graph_version": GRAPH_VERSION,
                    "resumed_from_checkpoint": True,
                    "recovery_state": "resumed",
                }
            )
            final_state = await graph.ainvoke(update, config=config)
            snapshot = await graph.aget_state(config)
        return self._result(final_state, thread_id, run_id, snapshot)

    async def state(self, thread_id: str) -> dict[str, Any]:
        config = self._config(thread_id)
        async with self._compiled() as graph:
            snapshot = await graph.aget_state(config)
        if snapshot is None or not snapshot.values:
            raise KeyError(f"unknown_thread_id:{thread_id}")
        return {
            "thread_id": thread_id,
            "checkpoint_id": getattr(snapshot, "config", {}).get("configurable", {}).get("checkpoint_id"),
            "values": snapshot.values,
            "next": list(snapshot.next),
            "claim_boundary": "LOCAL_RESULT_NO_CLAIM",
            "promotion": "BLOCKED",
        }

    @staticmethod
    def _result(final_state: dict[str, Any], thread_id: str, run_id: str, snapshot: Any) -> dict[str, Any]:
        checkpoint_id = getattr(snapshot, "config", {}).get("configurable", {}).get("checkpoint_id")
        return {
            "status": final_state.get("status"),
            "lote_id": final_state.get("lote_id"),
            "thread_id": thread_id,
            "run_id": run_id,
            "graph_version": GRAPH_VERSION,
            "checkpoint_id": checkpoint_id,
            "resumed_from_checkpoint": bool(final_state.get("resumed_from_checkpoint", False)),
            "recovery_state": final_state.get("recovery_state"),
            "qr_url": final_state.get("qr_url"),
            "blockchain_tx": final_state.get("gaiachain_tx_hash"),
            "human_review_required": final_state.get("ai_act_human_review_required"),
            "error": final_state.get("error"),
            "compensations_executed": final_state.get("compensations_executed", []),
            "claim_boundary": "LOCAL_RESULT_NO_CLAIM",
            "promotion": "BLOCKED",
        }
