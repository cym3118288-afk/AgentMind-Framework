"""Tests for AgentMind orchestration strategies."""

import time
import pytest
from agentmind.core import Agent, AgentMind, CollaborationStrategy, Message
from agentmind.llm import LLMProvider, LLMResponse
from agentmind.orchestration.consensus import ConsensusOrchestrator, VotingMechanism


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, model="mock-model", response_prefix="Mock", **kwargs):
        super().__init__(model, **kwargs)
        self.response_prefix = response_prefix

    async def generate(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock response."""
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        return LLMResponse(
            content=f"{self.response_prefix} response to: {user_msg}",
            model=self.model,
            usage={"total_tokens": 15},
            metadata={}
        )

    async def generate_stream(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock streaming response."""
        yield "Mock stream"


@pytest.mark.asyncio
async def test_agentmind_with_llm_provider():
    """Test AgentMind with LLM provider."""
    provider = MockLLMProvider()
    mind = AgentMind(llm_provider=provider)

    agent1 = Agent(name="agent1", role="analyst")
    agent2 = Agent(name="agent2", role="creative")

    mind.add_agent(agent1)
    mind.add_agent(agent2)

    # Agents should have LLM provider set
    assert agent1.llm_provider is provider
    assert agent2.llm_provider is provider


@pytest.mark.asyncio
async def test_broadcast_strategy_with_llm():
    """Test broadcast strategy with LLM."""
    provider = MockLLMProvider()
    mind = AgentMind(strategy=CollaborationStrategy.BROADCAST, llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", use_llm=True)

    assert result.success
    assert result.total_messages >= 3  # Initial + 2 responses
    assert len(result.agent_contributions) == 2


@pytest.mark.asyncio
async def test_round_robin_strategy():
    """Test round-robin strategy."""
    provider = MockLLMProvider()
    mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN, llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))
    mind.add_agent(Agent(name="agent3", role="critic"))

    result = await mind.start_collaboration("Test task", max_rounds=3, use_llm=True)

    assert result.success
    # Round-robin should have agents take turns
    assert result.total_rounds <= 3


@pytest.mark.asyncio
async def test_hierarchical_strategy():
    """Test hierarchical strategy with supervisor."""
    provider = MockLLMProvider()
    mind = AgentMind(strategy=CollaborationStrategy.HIERARCHICAL, llm_provider=provider)

    # Add supervisor first
    mind.add_agent(Agent(name="supervisor", role="supervisor"))
    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", use_llm=True)

    assert result.success
    # Supervisor should have contributed
    assert "supervisor" in result.agent_contributions


@pytest.mark.asyncio
async def test_hierarchical_without_supervisor():
    """Test hierarchical strategy falls back without supervisor."""
    provider = MockLLMProvider()
    mind = AgentMind(strategy=CollaborationStrategy.HIERARCHICAL, llm_provider=provider)

    # No supervisor, should fall back to broadcast
    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", use_llm=True)

    assert result.success
    assert len(result.agent_contributions) == 2


@pytest.mark.asyncio
async def test_collaboration_without_llm():
    """Test collaboration without LLM (template mode)."""
    mind = AgentMind(strategy=CollaborationStrategy.BROADCAST)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", use_llm=False)

    assert result.success
    assert result.total_messages >= 3


@pytest.mark.asyncio
async def test_stop_condition():
    """Test collaboration with stop condition."""
    provider = MockLLMProvider()
    mind = AgentMind(llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    # Stop condition that always triggers
    def stop_fn(messages):
        return True

    result = await mind.start_collaboration(
        "Test task",
        stop_condition=stop_fn,
        use_llm=True
    )

    assert result.success


@pytest.mark.asyncio
async def test_broadcast_message_with_llm():
    """Test broadcast_message with LLM."""
    provider = MockLLMProvider()
    mind = AgentMind(llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    message = Message(content="Test message", sender="system")
    responses = await mind.broadcast_message(message, use_llm=True)

    assert len(responses) == 2
    assert all("Mock response" in r.content for r in responses)


@pytest.mark.asyncio
async def test_agent_specific_llm_provider():
    """Test agents can have their own LLM providers."""
    global_provider = MockLLMProvider(response_prefix="Global")
    agent_provider = MockLLMProvider(response_prefix="Agent")

    mind = AgentMind(llm_provider=global_provider)

    # Agent with its own provider
    agent1 = Agent(name="agent1", role="analyst", llm_provider=agent_provider)
    # Agent that will use global provider
    agent2 = Agent(name="agent2", role="creative")

    mind.add_agent(agent1)
    mind.add_agent(agent2)

    # agent1 should keep its own provider
    assert agent1.llm_provider is agent_provider
    # agent2 should get global provider
    assert agent2.llm_provider is global_provider


@pytest.mark.asyncio
async def test_collaboration_result_metadata():
    """Test collaboration result contains proper metadata."""
    provider = MockLLMProvider()
    mind = AgentMind(llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", use_llm=True)

    assert result.success
    assert result.total_rounds > 0
    assert result.total_messages > 0
    assert result.final_output is not None
    assert len(result.agent_contributions) == 2
    assert result.error is None


@pytest.mark.asyncio
async def test_multiple_rounds_round_robin():
    """Test multiple rounds in round-robin mode."""
    provider = MockLLMProvider()
    mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN, llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", max_rounds=5, use_llm=True)

    assert result.success
    # Should complete requested rounds or less
    assert result.total_rounds <= 5


class TestOrchestrationEdgeCases:
    """Test edge cases in orchestration."""

    @pytest.mark.asyncio
    async def test_no_agents(self):
        """Test collaboration with no agents."""
        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)

        result = await mind.start_collaboration("Test task", use_llm=True)

        # Should handle gracefully
        assert not result.success or result.total_messages == 1

    @pytest.mark.asyncio
    async def test_single_agent(self):
        """Test collaboration with single agent."""
        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)

        mind.add_agent(Agent(name="agent1", role="analyst"))

        result = await mind.start_collaboration("Test task", use_llm=True)

        assert result.success
        assert len(result.agent_contributions) == 1

    @pytest.mark.asyncio
    async def test_max_rounds_zero(self):
        """Test with max_rounds=0."""
        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)

        mind.add_agent(Agent(name="agent1", role="analyst"))

        result = await mind.start_collaboration("Test task", max_rounds=0, use_llm=True)

        # Should handle gracefully - may do at least 1 round
        assert result.total_rounds <= 1

    @pytest.mark.asyncio
    async def test_all_agents_inactive(self):
        """Test when all agents are inactive."""
        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)

        agent1 = Agent(name="agent1", role="analyst")
        agent2 = Agent(name="agent2", role="creative")
        agent1.active = False
        agent2.active = False

        mind.add_agent(agent1)
        mind.add_agent(agent2)

        result = await mind.start_collaboration("Test task", use_llm=True)

        # Should complete but with minimal activity
        assert result.success

    @pytest.mark.asyncio
    async def test_empty_task(self):
        """Test collaboration with empty task."""
        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)

        mind.add_agent(Agent(name="agent1", role="analyst"))

        # Empty string not allowed, use minimal task instead
        result = await mind.start_collaboration(" ", use_llm=True)

        assert result.success

    @pytest.mark.asyncio
    async def test_very_long_task(self):
        """Test collaboration with very long task description."""
        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)

        mind.add_agent(Agent(name="agent1", role="analyst"))

        long_task = "x" * 10000
        result = await mind.start_collaboration(long_task, use_llm=True)

        assert result.success


class TestOrchestrationStrategies:
    """Test different orchestration strategies in detail."""

    @pytest.mark.asyncio
    async def test_broadcast_all_receive(self):
        """Test that broadcast sends to all agents."""
        provider = MockLLMProvider()
        mind = AgentMind(strategy=CollaborationStrategy.BROADCAST, llm_provider=provider)

        agents = [Agent(name=f"agent{i}", role="analyst") for i in range(5)]
        for agent in agents:
            mind.add_agent(agent)

        result = await mind.start_collaboration("Test task", max_rounds=1, use_llm=True)

        assert result.success
        assert len(result.agent_contributions) == 5

    @pytest.mark.asyncio
    async def test_round_robin_order(self):
        """Test that round-robin maintains order."""
        provider = MockLLMProvider()
        mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN, llm_provider=provider)

        mind.add_agent(Agent(name="agent1", role="analyst"))
        mind.add_agent(Agent(name="agent2", role="creative"))
        mind.add_agent(Agent(name="agent3", role="critic"))

        result = await mind.start_collaboration("Test task", max_rounds=6, use_llm=True)

        assert result.success
        # Each agent should have participated
        assert len(result.agent_contributions) == 3

    @pytest.mark.asyncio
    async def test_hierarchical_supervisor_first(self):
        """Test that hierarchical strategy prioritizes supervisor."""
        provider = MockLLMProvider()
        mind = AgentMind(strategy=CollaborationStrategy.HIERARCHICAL, llm_provider=provider)

        mind.add_agent(Agent(name="supervisor", role="supervisor"))
        mind.add_agent(Agent(name="worker1", role="analyst"))
        mind.add_agent(Agent(name="worker2", role="creative"))

        result = await mind.start_collaboration("Test task", use_llm=True)

        assert result.success
        assert "supervisor" in result.agent_contributions


class TestConsensusOrchestration:
    """Test consensus-based orchestration."""

    @pytest.mark.asyncio
    async def test_majority_vote_consensus(self):
        """Test majority voting mechanism."""
        provider = MockLLMProvider(response_prefix="VOTE: YES\nREASONING: Good idea\nCONFIDENCE: 80")

        agents = [
            Agent(name="agent1", role="analyst", llm_provider=provider),
            Agent(name="agent2", role="creative", llm_provider=provider),
            Agent(name="agent3", role="critic", llm_provider=provider),
        ]

        orchestrator = ConsensusOrchestrator(agents)
        result = await orchestrator.reach_consensus(
            "Should we proceed?",
            mechanism=VotingMechanism.MAJORITY
        )

        assert result is not None
        assert "votes" in result
        assert len(result["votes"]) == 3

    @pytest.mark.asyncio
    async def test_unanimous_vote(self):
        """Test unanimous voting mechanism."""
        provider = MockLLMProvider(response_prefix="VOTE: YES\nREASONING: Agreed\nCONFIDENCE: 90")

        agents = [
            Agent(name="agent1", role="analyst", llm_provider=provider),
            Agent(name="agent2", role="creative", llm_provider=provider),
        ]

        orchestrator = ConsensusOrchestrator(agents)
        result = await orchestrator.reach_consensus(
            "Should we proceed?",
            mechanism=VotingMechanism.UNANIMOUS
        )

        assert result is not None
        # Check if unanimous field exists in result
        assert "unanimous" in result["result"]

    @pytest.mark.asyncio
    async def test_weighted_vote(self):
        """Test weighted voting mechanism."""
        provider = MockLLMProvider(response_prefix="VOTE: YES\nREASONING: Good\nCONFIDENCE: 80")

        agents = [
            Agent(name="expert", role="analyst", llm_provider=provider),
            Agent(name="junior", role="creative", llm_provider=provider),
        ]

        orchestrator = ConsensusOrchestrator(agents)
        weights = {"expert": 2.0, "junior": 1.0}

        result = await orchestrator.reach_consensus(
            "Should we proceed?",
            mechanism=VotingMechanism.WEIGHTED,
            weights=weights
        )

        assert result is not None
        assert "weighted_ratio" in result["result"]

    @pytest.mark.asyncio
    async def test_ranked_choice_vote(self):
        """Test ranked choice voting mechanism."""
        provider = MockLLMProvider(response_prefix="VOTE: YES\nREASONING: Good\nCONFIDENCE: 75")

        agents = [
            Agent(name="agent1", role="analyst", llm_provider=provider),
            Agent(name="agent2", role="creative", llm_provider=provider),
        ]

        orchestrator = ConsensusOrchestrator(agents)
        result = await orchestrator.reach_consensus(
            "Should we proceed?",
            mechanism=VotingMechanism.RANKED_CHOICE
        )

        assert result is not None
        # Check that result has decision field
        assert "decision" in result["result"] or "reason" in result["result"]

    @pytest.mark.asyncio
    async def test_multi_round_consensus(self):
        """Test multi-round consensus building."""
        provider = MockLLMProvider(response_prefix="VOTE: YES\nREASONING: Good\nCONFIDENCE: 80")

        agents = [
            Agent(name="agent1", role="analyst", llm_provider=provider),
            Agent(name="agent2", role="creative", llm_provider=provider),
        ]

        orchestrator = ConsensusOrchestrator(agents)
        result = await orchestrator.multi_round_consensus(
            "Should we proceed?",
            max_rounds=3
        )

        assert result is not None
        assert "rounds" in result
        assert result["rounds"] <= 3

    @pytest.mark.asyncio
    async def test_consensus_history(self):
        """Test consensus history tracking."""
        provider = MockLLMProvider(response_prefix="VOTE: YES\nREASONING: Good\nCONFIDENCE: 80")

        agents = [
            Agent(name="agent1", role="analyst", llm_provider=provider),
        ]

        orchestrator = ConsensusOrchestrator(agents)

        await orchestrator.reach_consensus("Proposal 1")
        await orchestrator.reach_consensus("Proposal 2")

        history = orchestrator.get_consensus_history()
        assert len(history) == 2
        assert history[0]["proposal"] == "Proposal 1"
        assert history[1]["proposal"] == "Proposal 2"


class TestOrchestrationPerformance:
    """Test orchestration performance."""

    @pytest.mark.asyncio
    async def test_broadcast_performance_10_agents(self):
        """Test broadcast performance with 10 agents."""
        provider = MockLLMProvider()
        mind = AgentMind(strategy=CollaborationStrategy.BROADCAST, llm_provider=provider)

        for i in range(10):
            mind.add_agent(Agent(name=f"agent{i}", role="analyst"))

        start = time.time()
        result = await mind.start_collaboration("Test task", max_rounds=1, use_llm=True)
        elapsed = time.time() - start

        assert result.success
        assert len(result.agent_contributions) == 10
        # Should complete reasonably fast
        assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_round_robin_performance(self):
        """Test round-robin performance."""
        provider = MockLLMProvider()
        mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN, llm_provider=provider)

        for i in range(5):
            mind.add_agent(Agent(name=f"agent{i}", role="analyst"))

        start = time.time()
        result = await mind.start_collaboration("Test task", max_rounds=10, use_llm=True)
        elapsed = time.time() - start

        assert result.success
        assert elapsed < 5.0


class TestStopConditions:
    """Test stop conditions and early termination."""

    @pytest.mark.asyncio
    async def test_stop_on_keyword(self):
        """Test stopping when keyword appears."""
        provider = MockLLMProvider(response_prefix="DONE")
        mind = AgentMind(llm_provider=provider)

        mind.add_agent(Agent(name="agent1", role="analyst"))

        def stop_fn(messages):
            return any("DONE" in m.content for m in messages)

        result = await mind.start_collaboration(
            "Test task",
            stop_condition=stop_fn,
            max_rounds=10,
            use_llm=True
        )

        assert result.success
        # Should stop early
        assert result.total_rounds < 10

    @pytest.mark.asyncio
    async def test_stop_on_message_count(self):
        """Test stopping after N messages."""
        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)

        mind.add_agent(Agent(name="agent1", role="analyst"))
        mind.add_agent(Agent(name="agent2", role="creative"))

        def stop_fn(messages):
            return len(messages) >= 3

        result = await mind.start_collaboration(
            "Test task",
            stop_condition=stop_fn,
            max_rounds=10,
            use_llm=True
        )

        assert result.success
        # Stop condition triggers at 3 messages
        assert result.total_messages >= 3


class TestMessageRouting:
    """Test message routing between agents."""

    @pytest.mark.asyncio
    async def test_broadcast_message_routing(self):
        """Test that broadcast routes to all agents."""
        provider = MockLLMProvider()
        mind = AgentMind(strategy=CollaborationStrategy.BROADCAST, llm_provider=provider)

        agents = [Agent(name=f"agent{i}", role="analyst") for i in range(3)]
        for agent in agents:
            mind.add_agent(agent)

        message = Message(content="Test", sender="system")
        responses = await mind.broadcast_message(message, use_llm=True)

        assert len(responses) == 3

    @pytest.mark.asyncio
    async def test_message_metadata_preserved(self):
        """Test that message metadata is preserved."""
        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)

        mind.add_agent(Agent(name="agent1", role="analyst"))

        message = Message(
            content="Test",
            sender="system",
            metadata={"priority": "high", "task_id": "123"}
        )

        responses = await mind.broadcast_message(message, use_llm=True)

        assert len(responses) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
