"""Comprehensive tests for advanced Agent features.

Tests:
- State management and transitions
- Multi-modal support
- Human-in-the-loop workflows
- Sub-agent management
- Learning and adaptation
- State persistence
"""

import asyncio
import json
from pathlib import Path

import pytest

from agentmind.core.agent import Agent, AgentState, ApprovalPolicy, ContentType
from agentmind.core.types import AgentConfig, Message, MessageRole


class TestStateManagement:
    """Test advanced state management."""

    @pytest.mark.asyncio
    async def test_state_transitions(self):
        """Test state transitions."""
        agent = Agent(name="test_agent", role="analyst")

        assert agent.state == AgentState.IDLE

        # Transition to thinking
        agent.transition_state(AgentState.THINKING)
        assert agent.state == AgentState.THINKING

        # Check history
        assert len(agent.state_history) == 1
        assert agent.state_history[0]["from"] == "idle"
        assert agent.state_history[0]["to"] == "thinking"

    @pytest.mark.asyncio
    async def test_state_hooks(self):
        """Test state transition hooks."""
        agent = Agent(name="test_agent", role="analyst")

        hook_called = []

        def test_hook(old_state, new_state, metadata):
            hook_called.append((old_state, new_state))

        agent.add_state_hook("on_transition", test_hook)

        agent.transition_state(AgentState.THINKING)

        assert len(hook_called) == 1
        assert hook_called[0][0] == AgentState.IDLE
        assert hook_called[0][1] == AgentState.THINKING

    @pytest.mark.asyncio
    async def test_get_state_history(self):
        """Test getting state history."""
        agent = Agent(name="test_agent", role="analyst")

        # Make several transitions
        agent.transition_state(AgentState.THINKING)
        agent.transition_state(AgentState.EXECUTING)
        agent.transition_state(AgentState.IDLE)

        history = agent.get_state_history(limit=2)
        assert len(history) == 2


class TestMultiModal:
    """Test multi-modal support."""

    @pytest.mark.asyncio
    async def test_enable_multimodal(self):
        """Test enabling multi-modal support."""
        agent = Agent(name="test_agent", role="analyst")

        agent.enable_multimodal(
            content_types=[ContentType.TEXT, ContentType.IMAGE],
            streaming=True,
        )

        assert ContentType.TEXT in agent.supported_content_types
        assert ContentType.IMAGE in agent.supported_content_types
        assert agent.streaming_enabled is True

    @pytest.mark.asyncio
    async def test_validate_content_type(self):
        """Test content type validation."""
        agent = Agent(name="test_agent", role="analyst")

        agent.enable_multimodal(content_types=[ContentType.TEXT])

        assert agent.validate_content_type(ContentType.TEXT) is True
        assert agent.validate_content_type(ContentType.IMAGE) is False

    @pytest.mark.asyncio
    async def test_process_multimodal_message(self):
        """Test processing multi-modal messages."""
        agent = Agent(name="test_agent", role="analyst")

        agent.enable_multimodal(content_types=[ContentType.TEXT, ContentType.IMAGE])

        message = Message(
            content="Test message",
            sender="user",
            role=MessageRole.USER,
        )

        # Process text
        response = await agent.process_multimodal_message(message, ContentType.TEXT)
        assert response is not None
        assert response.sender == "test_agent"

        # Process image
        response = await agent.process_multimodal_message(message, ContentType.IMAGE)
        assert response is not None
        assert "[IMAGE CONTENT]" in response.content


class TestHumanInLoop:
    """Test human-in-the-loop features."""

    @pytest.mark.asyncio
    async def test_request_approval(self):
        """Test requesting human approval."""

        def approval_callback(request):
            return True

        agent = Agent(
            name="test_agent",
            role="analyst",
            human_in_loop=True,
            human_callback=approval_callback,
        )

        approved = await agent.request_human_approval("Test action", {"context": "test"})

        assert approved is True
        assert agent.state == AgentState.IDLE

    @pytest.mark.asyncio
    async def test_approval_policy(self):
        """Test approval policies."""
        agent = Agent(
            name="test_agent",
            role="analyst",
            approval_policy=ApprovalPolicy.ALWAYS,
        )

        assert agent.should_request_approval("message") is True

        agent.approval_policy = ApprovalPolicy.NEVER
        assert agent.should_request_approval("message") is False

        agent.approval_policy = ApprovalPolicy.ON_TOOL_USE
        assert agent.should_request_approval("tool_use") is True
        assert agent.should_request_approval("message") is False

    @pytest.mark.asyncio
    async def test_collect_feedback(self):
        """Test collecting feedback."""
        agent = Agent(name="test_agent", role="analyst", enable_learning=True)

        await agent.collect_feedback({"rating": 5, "comments": "Great!"})

        assert len(agent.feedback_history) == 1
        assert agent.feedback_history[0]["feedback"]["rating"] == 5


class TestSubAgents:
    """Test sub-agent management."""

    @pytest.mark.asyncio
    async def test_add_sub_agent(self):
        """Test adding sub-agents."""
        parent = Agent(name="parent", role="supervisor")
        child = Agent(name="child", role="analyst")

        parent.add_sub_agent(child)

        assert len(parent.sub_agents) == 1
        assert child.parent_agent == parent

    @pytest.mark.asyncio
    async def test_remove_sub_agent(self):
        """Test removing sub-agents."""
        parent = Agent(name="parent", role="supervisor")
        child = Agent(name="child", role="analyst")

        parent.add_sub_agent(child)
        removed = parent.remove_sub_agent("child")

        assert removed is True
        assert len(parent.sub_agents) == 0
        assert child.parent_agent is None

    @pytest.mark.asyncio
    async def test_delegate_task(self):
        """Test task delegation."""
        parent = Agent(name="parent", role="supervisor")
        child = Agent(name="child", role="analyst")

        parent.add_sub_agent(child)

        task = Message(
            content="Test task",
            sender="parent",
            role=MessageRole.AGENT,
        )

        response = await parent.delegate_task("child", task)

        assert response is not None
        assert len(parent.delegation_history) == 1

    @pytest.mark.asyncio
    async def test_broadcast_to_sub_agents(self):
        """Test broadcasting to sub-agents."""
        parent = Agent(name="parent", role="supervisor")
        child1 = Agent(name="child1", role="analyst")
        child2 = Agent(name="child2", role="researcher")

        parent.add_sub_agent(child1)
        parent.add_sub_agent(child2)

        message = Message(
            content="Broadcast message",
            sender="parent",
            role=MessageRole.AGENT,
        )

        responses = await parent.broadcast_to_sub_agents(message)

        assert len(responses) == 2

    @pytest.mark.asyncio
    async def test_get_sub_agent_health(self):
        """Test getting sub-agent health."""
        parent = Agent(name="parent", role="supervisor")
        child = Agent(name="child", role="analyst")

        parent.add_sub_agent(child)

        health = parent.get_sub_agent_health()

        assert "child" in health
        assert health["child"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_aggregate_results(self):
        """Test aggregating sub-agent results."""
        parent = Agent(name="parent", role="supervisor")

        results = [
            Message(content="Result 1", sender="agent1", role=MessageRole.AGENT),
            Message(content="Result 2", sender="agent2", role=MessageRole.AGENT),
        ]

        # Test concatenate
        aggregated = parent.aggregate_sub_agent_results(results, "concatenate")
        assert "Result 1" in aggregated
        assert "Result 2" in aggregated

        # Test vote
        aggregated = parent.aggregate_sub_agent_results(results, "vote")
        assert aggregated in ["Result 1", "Result 2"]


class TestLearning:
    """Test learning and adaptation features."""

    @pytest.mark.asyncio
    async def test_track_success(self):
        """Test tracking success/failure."""
        agent = Agent(name="test_agent", role="analyst", enable_learning=True)

        agent.track_success(True, response_time=0.5)
        agent.track_success(False, response_time=1.0)

        metrics = agent.get_performance_metrics()

        assert metrics["total_messages"] == 2
        assert metrics["successful_responses"] == 1
        assert metrics["failed_responses"] == 1
        assert metrics["success_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test getting performance metrics."""
        agent = Agent(name="test_agent", role="analyst", enable_learning=True)

        agent.track_success(True, response_time=0.3)
        agent.track_success(True, response_time=0.5)

        metrics = agent.get_performance_metrics()

        assert metrics["success_rate"] == 1.0
        assert metrics["average_response_time"] == 0.4

    @pytest.mark.asyncio
    async def test_suggest_improvements(self):
        """Test improvement suggestions."""
        agent = Agent(name="test_agent", role="analyst", enable_learning=True)

        # Simulate poor performance
        for _ in range(10):
            agent.track_success(False)

        suggestions = agent.suggest_improvements()

        assert len(suggestions) > 0

    @pytest.mark.asyncio
    async def test_ab_testing(self):
        """Test A/B testing."""
        agent = Agent(name="test_agent", role="analyst", enable_learning=True)

        agent.start_ab_test(
            "test",
            variant_a={"temp": 0.5},
            variant_b={"temp": 0.9},
        )

        assert "test" in agent.ab_tests

        # Record results
        agent.record_ab_result("test", True)
        agent.record_ab_result("test", False)

        results = agent.get_ab_test_results("test")

        assert results is not None
        assert "variant_a_success_rate" in results
        assert "variant_b_success_rate" in results


class TestPersistence:
    """Test state persistence and recovery."""

    @pytest.mark.asyncio
    async def test_save_state(self, tmp_path):
        """Test saving agent state."""
        agent = Agent(name="test_agent", role="analyst")

        # Add some data
        message = Message(
            content="Test",
            sender="user",
            role=MessageRole.USER,
        )
        await agent.process_message(message)

        # Save state
        state_file = tmp_path / "agent_state.json"
        success = agent.save_state(str(state_file))

        assert success is True
        assert state_file.exists()

        # Verify content
        with open(state_file) as f:
            data = json.load(f)

        assert data["name"] == "test_agent"
        assert len(data["memory"]) > 0

    @pytest.mark.asyncio
    async def test_load_state(self, tmp_path):
        """Test loading agent state."""
        # Create and save agent
        agent1 = Agent(name="test_agent", role="analyst")

        message = Message(
            content="Test",
            sender="user",
            role=MessageRole.USER,
        )
        await agent1.process_message(message)

        state_file = tmp_path / "agent_state.json"
        agent1.save_state(str(state_file))

        # Load into new agent
        agent2 = Agent(name="test_agent", role="analyst")
        success = agent2.load_state(str(state_file))

        assert success is True
        assert len(agent2.memory) == len(agent1.memory)

    @pytest.mark.asyncio
    async def test_recover_from_error(self):
        """Test error recovery."""
        agent = Agent(name="test_agent", role="analyst")

        # Set error state
        agent.transition_state(AgentState.ERROR)
        assert agent.state == AgentState.ERROR

        # Recover
        recovered = await agent.recover_from_error()

        assert recovered is True
        assert agent.state == AgentState.IDLE


class TestIntegration:
    """Integration tests for advanced features."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow with all features."""

        def approval_callback(request):
            return True

        # Create parent agent with all features
        parent = Agent(
            name="supervisor",
            role="supervisor",
            human_in_loop=True,
            approval_policy=ApprovalPolicy.ON_TOOL_USE,
            human_callback=approval_callback,
            enable_learning=True,
        )

        # Enable multi-modal
        parent.enable_multimodal([ContentType.TEXT, ContentType.IMAGE])

        # Add sub-agents
        analyst = Agent(name="analyst", role="analyst")
        researcher = Agent(name="researcher", role="researcher")

        parent.add_sub_agent(analyst)
        parent.add_sub_agent(researcher)

        # Process message
        message = Message(
            content="Analyze this problem",
            sender="user",
            role=MessageRole.USER,
        )

        response = await parent.process_message(message)

        assert response is not None
        assert parent.state == AgentState.IDLE

        # Delegate to sub-agent
        task = Message(
            content="Research the topic",
            sender="supervisor",
            role=MessageRole.AGENT,
        )

        delegation_response = await parent.delegate_task("researcher", task)

        assert delegation_response is not None
        assert len(parent.delegation_history) == 1

        # Track performance
        parent.track_success(True, response_time=0.5)

        metrics = parent.get_performance_metrics()
        assert metrics["total_messages"] > 0

        # Get health
        health = parent.get_sub_agent_health()
        assert len(health) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
