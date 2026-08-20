from __future__ import annotations

from pathlib import Path

import pytest
from langgraph.graph import END, START, StateGraph

from castuo_graph import durable_runtime as durable


def _test_graph(checkpointer):
    graph = StateGraph(dict)

    async def step(state):
        return {"value": int(state.get("value", 0)) + 1}

    graph.add_node("step", step)
    graph.add_edge(START, "step")
    graph.add_edge("step", END)
    return graph.compile(checkpointer=checkpointer)


@pytest.mark.asyncio
async def test_runtime_persists_state_across_runtime_instances(tmp_path: Path, monkeypatch):
    db = tmp_path / "durable.sqlite"
    monkeypatch.setattr(durable, "build_graph", _test_graph)
    monkeypatch.setattr(durable, "build_initial_state", lambda value: {"value": value["value"]})

    first = durable.DurableAgentRuntime(db)
    result = await first.run({"value": 4}, thread_id="thread-a")
    assert result["thread_id"] == "thread-a"
    assert result["claim_boundary"] == "LOCAL_RESULT_NO_CLAIM"
    assert result["promotion"] == "BLOCKED"

    second = durable.DurableAgentRuntime(db)
    snapshot = await second.state("thread-a")
    assert snapshot["thread_id"] == "thread-a"
    assert snapshot["values"]["value"] == 5


@pytest.mark.asyncio
async def test_runtime_isolates_threads(tmp_path: Path, monkeypatch):
    db = tmp_path / "durable.sqlite"
    monkeypatch.setattr(durable, "build_graph", _test_graph)
    monkeypatch.setattr(durable, "build_initial_state", lambda value: {"value": value["value"]})

    runtime = durable.DurableAgentRuntime(db)
    await runtime.run({"value": 10}, thread_id="thread-a")
    await runtime.run({"value": 20}, thread_id="thread-b")

    state_a = await runtime.state("thread-a")
    state_b = await runtime.state("thread-b")
    assert state_a["values"]["value"] == 11
    assert state_b["values"]["value"] == 21
