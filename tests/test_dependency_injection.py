# tests/test_dependency_injection.py
import pytest


def test_dependency_injection_resolve():
    from backend.core.dependency_injector import injector
    from backend.agents.selfhealing_agent import SelfHealingAgent

    injector.clear()
    mock_agent = SelfHealingAgent()
    injector.register("SelfHealingAgent", mock_agent)

    resolved = injector.resolve("SelfHealingAgent")
    assert resolved is mock_agent
    injector.clear()


def test_injector_inject_class():
    from backend.core.dependency_injector import injector
    from backend.agents.selfhealing_agent import SelfHealingAgent

    injector.clear()

    class TestClass:
        def __init__(self, agent: SelfHealingAgent):
            self.agent = agent

    mock_agent = SelfHealingAgent()
    injector.register("SelfHealingAgent", mock_agent)

    instance = injector.inject(TestClass)
    assert instance.agent is mock_agent
    injector.clear()


def test_master_agent_without_injector():
    from backend.agents.master_agent import MasterAgent

    agent = MasterAgent()
    assert agent.agent_registry is not None
    assert "selfhealing" in agent.agent_registry
