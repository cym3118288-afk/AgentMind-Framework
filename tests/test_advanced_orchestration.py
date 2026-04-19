"""Comprehensive tests for advanced orchestration modes."""

import asyncio
import pytest
from typing import List

from agentmind.core import Agent, AgentConfig
from agentmind.core.types import Message, MessageRole
from agentmind.orchestration.advanced_modes import (
    OrchestrationMode,
    OrchestrationMetrics,
    SequentialOrchestrator,
    HierarchicalOrchestrator,
    DebateOrchestrator,
    ConsensusOrchestrator,
    SwarmOrchestrator,
    GraphOrchestrator,
    HybridOrchestrator,
    create_orchestrator,
    get_available_modes,
    get_mode_description,
    recommend_mode,
)


def create_test_agents(num: int, prefix: str = "agent") -> List[Agent]:
    """Create test agents."""
    return [
        Agent(
            name=f"{prefix}_{i}",
            role="analyst",
            config=AgentConfig(name=f"{prefix}_{i}", role="analyst"),
        )
        for i in range(num)
    ]


class TestOrchestrationMetrics:
    """Test orchestration metrics."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = OrchestrationMetrics()
        assert metrics.total_messages == 0
        assert metrics.total_rounds == 0
        assert len(metrics.errors) == 0
        assert len(metrics.warnings) == 0

    def test_record_message(self):
        """Test recording messages."""
        metrics = OrchestrationMetrics()
        metrics.record_message("agent_1")
        metrics.record_message("agent_1")
        metrics.record_message("agent_2")

        assert metrics.total_messages == 3
        assert metrics.agent_workload["agent_1"] == 2
        assert metrics.agent_workload["agent_2"] == 1

    def test_record_error(self):
        """Test recording errors."""
        metrics = OrchestrationMetrics()
        metrics.record_error("Test error")

        assert len(metrics.errors) == 1
        assert metrics.errors[0] == "Test error"

    def test_get_duration(self):
        """Test duration calculation."""
        metrics = OrchestrationMetrics()
        import time
        time.sleep(0.1)
        metrics.finalize()

        duration = metrics.get_duration()
        assert duration >= 0.1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = OrchestrationMetrics()
        metrics.record_message("agent_1")
        metrics.finalize()

        data = metrics.to_dict()
        assert "duration" in data
        assert "total_messages" in data
        assert data["total_messages"] == 1


class TestSequentialOrchestrator:
    """Test sequential orchestration."""

    @pytest.mark.asyncio
    async def test_basic_sequential(self):
        """Test basic sequential execution."""
        agents = create_test_agents(3)
        orchestrator = SequentialOrchestrator()

        result = await orchestrator.orchestrate(agents, "Test task")

        assert result.success
        assert result.total_rounds == 3
        assert result.total_messages >= 3

    @pytest.mark.asyncio
    async def test_sequential_with_early_termination(self):
        """Test early termination on error."""
        agents = create_test_agents(5)
        # Deactivate middle agent to simulate failure
        agents[2].deactivate()

        orchestrator = SequentialOrchestrator()

        result = await orchestrator.orchestrate(
            agents, "Test task", early_termination=True
        )

        # Should still succeed as inactive agents are skipped
        assert result.success

    @pytest.mark.asyncio
    async def test_sequential_with_retries(self):
        """Test retry mechanism."""
        agents = create_test_agents(2)
        orchestrator = SequentialOrchestrator()

        result = await orchestrator.orchestrate(
            agents, "Test task", max_retries=2
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_sequential_empty_agents(self):
        """Test with no agents."""
        orchestrator = SequentialOrchestrator()
        result = await orchestrator.orchestrate([], "Test task")

        assert not result.success
        assert result.error is not None


class TestHierarchicalOrchestrator:
    """Test hierarchical orchestration."""

    @pytest.mark.asyncio
    async def test_basic_hierarchical(self):
        """Test basic hierarchical execution."""
        agents = [
            Agent("manager", "supervisor"),
            Agent("worker_1", "executor"),
            Agent("worker_2", "executor"),
            Agent("reviewer", "critic"),
        ]

        orchestrator = HierarchicalOrchestrator()
        result = await orchestrator.orchestrate(agents, "Test task")

        assert result.success
        assert result.total_rounds >= 3  # Planning, execution, review

    @pytest.mark.asyncio
    async def test_hierarchical_with_escalation(self):
        """Test escalation mechanism."""
        agents = create_test_agents(5)
        orchestrator = HierarchicalOrchestrator()

        result = await orchestrator.orchestrate(
            agents,
            "Test task",
            quality_threshold=0.9,  # High threshold
            max_escalations=1,
        )

        assert result.success
        # Check if escalation occurred
        metrics = result.metadata.get("metrics", {})
        assert "custom_metrics" in metrics

    @pytest.mark.asyncio
    async def test_hierarchical_insufficient_agents(self):
        """Test with insufficient agents."""
        agents = create_test_agents(2)
        orchestrator = HierarchicalOrchestrator()

        result = await orchestrator.orchestrate(agents, "Test task")

        assert not result.success


class TestDebateOrchestrator:
    """Test debate orchestration."""

    @pytest.mark.asyncio
    async def test_basic_debate(self):
        """Test basic debate execution."""
        agents = create_test_agents(4)
        orchestrator = DebateOrchestrator()

        result = await orchestrator.orchestrate(
            agents, "Should we adopt feature X?", debate_rounds=2
        )

        assert result.success
        assert result.total_rounds >= 2

    @pytest.mark.asyncio
    async def test_debate_with_moderator(self):
        """Test debate with moderator."""
        agents = create_test_agents(5)
        orchestrator = DebateOrchestrator()

        result = await orchestrator.orchestrate(
            agents,
            "Test proposal",
            debate_rounds=2,
            enable_moderator=True,
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_debate_voting_mechanisms(self):
        """Test different voting mechanisms."""
        agents = create_test_agents(3)
        orchestrator = DebateOrchestrator()

        mechanisms = ["majority", "weighted", "consensus"]

        for mechanism in mechanisms:
            result = await orchestrator.orchestrate(
                agents,
                "Test proposal",
                debate_rounds=1,
                voting_mechanism=mechanism,
                weights={"agent_0": 2.0, "agent_1": 1.0, "agent_2": 1.0},
            )

            assert result.success

    @pytest.mark.asyncio
    async def test_debate_convergence(self):
        """Test convergence detection."""
        agents = create_test_agents(3)
        orchestrator = DebateOrchestrator()

        result = await orchestrator.orchestrate(
            agents,
            "Test proposal",
            debate_rounds=5,
            convergence_threshold=0.8,
        )

        assert result.success


class TestConsensusOrchestrator:
    """Test consensus orchestration."""

    @pytest.mark.asyncio
    async def test_basic_consensus(self):
        """Test basic consensus building."""
        agents = create_test_agents(4)
        orchestrator = ConsensusOrchestrator()

        result = await orchestrator.orchestrate(
            agents, "Establish coding standards"
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_consensus_with_peer_review(self):
        """Test consensus with peer review."""
        agents = create_test_agents(3)
        orchestrator = ConsensusOrchestrator()

        result = await orchestrator.orchestrate(
            agents,
            "Test proposal",
            enable_peer_review=True,
            max_iterations=2,
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_consensus_threshold(self):
        """Test consensus threshold."""
        agents = create_test_agents(5)
        orchestrator = ConsensusOrchestrator()

        result = await orchestrator.orchestrate(
            agents,
            "Test proposal",
            consensus_threshold=0.9,
            max_iterations=3,
        )

        assert result.success


class TestSwarmOrchestrator:
    """Test swarm orchestration."""

    @pytest.mark.asyncio
    async def test_basic_swarm(self):
        """Test basic swarm execution."""
        agents = create_test_agents(6)
        orchestrator = SwarmOrchestrator()

        result = await orchestrator.orchestrate(
            agents, "Process large dataset"
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_swarm_scaling(self):
        """Test dynamic scaling."""
        agents = create_test_agents(10)
        orchestrator = SwarmOrchestrator()

        # Simple task - should use fewer agents
        result1 = await orchestrator.orchestrate(
            agents,
            "Simple task",
            complexity_threshold=100,
        )

        # Complex task - should use more agents
        result2 = await orchestrator.orchestrate(
            agents,
            "Complex task " * 50,  # Long task
            complexity_threshold=50,
        )

        assert result1.success
        assert result2.success

    @pytest.mark.asyncio
    async def test_swarm_work_stealing(self):
        """Test work stealing."""
        agents = create_test_agents(5)
        orchestrator = SwarmOrchestrator()

        result = await orchestrator.orchestrate(
            agents,
            "Test task",
            enable_work_stealing=True,
        )

        assert result.success


class TestGraphOrchestrator:
    """Test graph orchestration."""

    @pytest.mark.asyncio
    async def test_basic_graph(self):
        """Test basic graph execution."""
        agents = create_test_agents(4)
        orchestrator = GraphOrchestrator()

        # Build simple graph
        orchestrator.add_node("start", agents[0])
        orchestrator.add_node("middle", agents[1])
        orchestrator.add_node("end", agents[2])
        orchestrator.add_edge("start", "middle")
        orchestrator.add_edge("middle", "end")

        result = await orchestrator.orchestrate(
            agents, "Test task", start_node="start"
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_graph_parallel_paths(self):
        """Test parallel execution paths."""
        agents = create_test_agents(5)
        orchestrator = GraphOrchestrator()

        # Build graph with parallel paths
        orchestrator.add_node("start", agents[0])
        orchestrator.add_node("path1", agents[1])
        orchestrator.add_node("path2", agents[2])
        orchestrator.add_node("merge", agents[3], "merge")

        orchestrator.add_edge("start", "path1")
        orchestrator.add_edge("start", "path2")
        orchestrator.add_edge("path1", "merge")
        orchestrator.add_edge("path2", "merge")

        result = await orchestrator.orchestrate(
            agents, "Test task", start_node="start", max_parallel=2
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_graph_cycle_detection(self):
        """Test cycle detection."""
        agents = create_test_agents(3)
        orchestrator = GraphOrchestrator()

        orchestrator.add_node("a", agents[0])
        orchestrator.add_node("b", agents[1])
        orchestrator.add_node("c", agents[2])

        orchestrator.add_edge("a", "b")
        orchestrator.add_edge("b", "c")
        orchestrator.add_edge("c", "a")  # Creates cycle

        cycles = orchestrator.detect_cycles()
        assert len(cycles) > 0

    def test_graph_visualization(self):
        """Test graph visualization."""
        agents = create_test_agents(3)
        orchestrator = GraphOrchestrator()

        orchestrator.add_node("a", agents[0])
        orchestrator.add_node("b", agents[1])
        orchestrator.add_edge("a", "b")

        mermaid = orchestrator.visualize_graph("mermaid")
        assert "graph TD" in mermaid

        dot = orchestrator.visualize_graph("dot")
        assert "digraph G" in dot

    def test_graph_stats(self):
        """Test graph statistics."""
        agents = create_test_agents(4)
        orchestrator = GraphOrchestrator()

        orchestrator.add_node("a", agents[0])
        orchestrator.add_node("b", agents[1])
        orchestrator.add_node("c", agents[2])
        orchestrator.add_edge("a", "b")
        orchestrator.add_edge("b", "c")

        stats = orchestrator.get_graph_stats()
        assert stats["total_nodes"] == 3
        assert stats["total_edges"] == 2


class TestHybridOrchestrator:
    """Test hybrid orchestration."""

    @pytest.mark.asyncio
    async def test_sequential_integration(self):
        """Test sequential integration."""
        agents = create_test_agents(6)
        orchestrator = HybridOrchestrator(
            OrchestrationMode.SEQUENTIAL,
            OrchestrationMode.SWARM,
        )

        result = await orchestrator.orchestrate(
            agents,
            "Test task",
            integration_strategy="sequential",
            split_ratio=0.5,
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_parallel_integration(self):
        """Test parallel integration."""
        agents = create_test_agents(8)
        orchestrator = HybridOrchestrator(
            OrchestrationMode.DEBATE,
            OrchestrationMode.CONSENSUS,
        )

        result = await orchestrator.orchestrate(
            agents,
            "Test task",
            integration_strategy="parallel",
            split_ratio=0.5,
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_nested_integration(self):
        """Test nested integration."""
        agents = create_test_agents(6)
        orchestrator = HybridOrchestrator(
            OrchestrationMode.HIERARCHICAL,
            OrchestrationMode.SEQUENTIAL,
        )

        result = await orchestrator.orchestrate(
            agents,
            "Test task",
            integration_strategy="nested",
        )

        assert result.success


class TestFactoryAndUtilities:
    """Test factory functions and utilities."""

    def test_create_orchestrator(self):
        """Test orchestrator factory."""
        modes = [
            OrchestrationMode.SEQUENTIAL,
            OrchestrationMode.HIERARCHICAL,
            OrchestrationMode.DEBATE,
            OrchestrationMode.CONSENSUS,
            OrchestrationMode.SWARM,
            OrchestrationMode.GRAPH,
        ]

        for mode in modes:
            orchestrator = create_orchestrator(mode)
            assert orchestrator.get_mode() == mode

    def test_create_hybrid_orchestrator(self):
        """Test hybrid orchestrator creation."""
        orchestrator = create_orchestrator(
            OrchestrationMode.HYBRID,
            secondary_mode=OrchestrationMode.SWARM,
        )

        assert orchestrator.get_mode() == OrchestrationMode.HYBRID

    def test_create_orchestrator_invalid(self):
        """Test invalid mode."""
        with pytest.raises(ValueError):
            create_orchestrator("invalid_mode")

    def test_get_available_modes(self):
        """Test getting available modes."""
        modes = get_available_modes()
        assert len(modes) > 0
        assert "sequential" in modes
        assert "hierarchical" in modes

    def test_get_mode_description(self):
        """Test mode descriptions."""
        desc = get_mode_description(OrchestrationMode.SEQUENTIAL)
        assert len(desc) > 0
        assert "chain" in desc.lower() or "responsibility" in desc.lower()

    def test_recommend_mode(self):
        """Test mode recommendation."""
        # Small team, simple task
        mode1 = recommend_mode(num_agents=2, task_complexity="low")
        assert mode1 == OrchestrationMode.SEQUENTIAL

        # Consensus required
        mode2 = recommend_mode(num_agents=5, requires_consensus=True)
        assert mode2 == OrchestrationMode.CONSENSUS

        # Hierarchical structure
        mode3 = recommend_mode(num_agents=5, has_hierarchy=True)
        assert mode3 == OrchestrationMode.HIERARCHICAL

        # Large team, complex task
        mode4 = recommend_mode(num_agents=10, task_complexity="high")
        assert mode4 == OrchestrationMode.SWARM


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling."""
        agents = create_test_agents(2)
        orchestrator = SequentialOrchestrator()

        result = await orchestrator.orchestrate(
            agents,
            "Test task",
            timeout_per_agent=0.001,  # Very short timeout
        )

        # Should complete even with timeouts
        assert result is not None

    @pytest.mark.asyncio
    async def test_inactive_agents(self):
        """Test handling of inactive agents."""
        agents = create_test_agents(4)
        agents[1].deactivate()
        agents[2].deactivate()

        orchestrator = SequentialOrchestrator()
        result = await orchestrator.orchestrate(agents, "Test task")

        # Should handle inactive agents gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_empty_task(self):
        """Test with empty task."""
        agents = create_test_agents(2)
        orchestrator = SequentialOrchestrator()

        result = await orchestrator.orchestrate(agents, "")

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
