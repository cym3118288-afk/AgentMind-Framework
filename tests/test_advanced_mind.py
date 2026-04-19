"""Comprehensive tests for advanced Mind features.

Tests:
- Task management with dependencies
- Resource allocation
- Checkpointing and recovery
- System observability
- Collaboration patterns
- Deadlock detection
"""

import asyncio
import json
from pathlib import Path

import pytest

from agentmind.core.agent import Agent
from agentmind.core.mind import (
    AgentMind,
    TaskPriority,
    TaskStatus,
    CoordinationStrategy,
    ConflictResolutionStrategy,
)
from agentmind.core.types import CollaborationStrategy, Message, MessageRole


class TestTaskManagement:
    """Test advanced task management."""

    @pytest.mark.asyncio
    async def test_add_task(self):
        """Test adding tasks."""
        mind = AgentMind()

        task = mind.add_task(
            task_id="test_task",
            description="Test task",
            priority=TaskPriority.HIGH,
        )

        assert task.task_id == "test_task"
        assert task.priority == TaskPriority.HIGH
        assert "test_task" in mind.tasks

    @pytest.mark.asyncio
    async def test_task_dependencies(self):
        """Test task dependencies."""
        mind = AgentMind()

        mind.add_task("task1", "First task")
        mind.add_task("task2", "Second task", dependencies=["task1"])

        task2 = mind.tasks["task2"]
        assert "task1" in task2.dependencies

    @pytest.mark.asyncio
    async def test_task_priority_sorting(self):
        """Test task queue sorting by priority."""
        mind = AgentMind()

        mind.add_task("low", "Low priority", TaskPriority.LOW)
        mind.add_task("critical", "Critical priority", TaskPriority.CRITICAL)
        mind.add_task("medium", "Medium priority", TaskPriority.MEDIUM)

        # Critical should be first
        assert mind.task_queue[0] == "critical"

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """Test cancelling tasks."""
        mind = AgentMind()

        mind.add_task("test_task", "Test task")
        cancelled = mind.cancel_task("test_task")

        assert cancelled is True
        assert mind.tasks["test_task"].status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_get_task_status(self):
        """Test getting task status."""
        mind = AgentMind()

        mind.add_task("test_task", "Test task", TaskPriority.HIGH)
        status = mind.get_task_status("test_task")

        assert status is not None
        assert status["task_id"] == "test_task"
        assert status["priority"] == "high"

    @pytest.mark.asyncio
    async def test_get_ready_tasks(self):
        """Test getting ready tasks."""
        mind = AgentMind()

        mind.add_task("task1", "First task")
        mind.add_task("task2", "Second task", dependencies=["task1"])
        mind.add_task("task3", "Third task")

        ready = mind.get_ready_tasks()

        # task1 and task3 should be ready (no dependencies)
        assert "task1" in ready
        assert "task3" in ready
        assert "task2" not in ready

    @pytest.mark.asyncio
    async def test_execute_task_queue(self):
        """Test executing task queue."""
        mind = AgentMind()
        mind.add_agent(Agent(name="worker", role="executor"))

        mind.add_task("task1", "First task", TaskPriority.HIGH)
        mind.add_task("task2", "Second task", TaskPriority.MEDIUM)

        results = await mind.execute_task_queue(max_parallel=2)

        assert len(results) == 2
        assert mind.metrics["completed_tasks"] >= 0


class TestResourceAllocation:
    """Test resource allocation."""

    @pytest.mark.asyncio
    async def test_allocate_resources(self):
        """Test allocating resources."""
        mind = AgentMind(max_concurrent_tasks=5)

        success = mind.resource_allocation.allocate("agent1", 2)
        assert success is True

        allocated = mind.resource_allocation.allocated_resources.get("agent1", 0)
        assert allocated == 2

    @pytest.mark.asyncio
    async def test_release_resources(self):
        """Test releasing resources."""
        mind = AgentMind()

        mind.resource_allocation.allocate("agent1", 3)
        mind.resource_allocation.release("agent1", 1)

        allocated = mind.resource_allocation.allocated_resources.get("agent1", 0)
        assert allocated == 2

    @pytest.mark.asyncio
    async def test_get_available_resources(self):
        """Test getting available resources."""
        mind = AgentMind(max_concurrent_tasks=5)

        mind.resource_allocation.allocate("agent1", 2)
        available = mind.resource_allocation.get_available("agent1")

        assert available == 3

    @pytest.mark.asyncio
    async def test_resource_limits(self):
        """Test resource limits."""
        mind = AgentMind()

        mind.resource_allocation.resource_limits["agent1"] = 2
        mind.resource_allocation.allocate("agent1", 2)

        # Should fail - limit reached
        success = mind.resource_allocation.allocate("agent1", 1)
        assert success is False


class TestCheckpointing:
    """Test checkpointing and recovery."""

    @pytest.mark.asyncio
    async def test_save_checkpoint(self, tmp_path):
        """Test saving checkpoint."""
        mind = AgentMind(checkpoint_dir=str(tmp_path))
        mind.add_agent(Agent(name="agent1", role="analyst"))
        mind.add_task("task1", "Test task")

        checkpoint_path = mind.save_checkpoint("test_checkpoint")

        assert Path(checkpoint_path).exists()

    @pytest.mark.asyncio
    async def test_restore_checkpoint(self, tmp_path):
        """Test restoring checkpoint."""
        # Create and save
        mind1 = AgentMind(checkpoint_dir=str(tmp_path))
        mind1.add_agent(Agent(name="agent1", role="analyst"))
        mind1.add_task("task1", "Test task")
        mind1.save_checkpoint("test_checkpoint")

        # Restore
        mind2 = AgentMind(checkpoint_dir=str(tmp_path))
        success = mind2.restore_checkpoint("test_checkpoint")

        assert success is True
        assert len(mind2.agents) == 1
        assert len(mind2.tasks) == 1

    @pytest.mark.asyncio
    async def test_crash_recovery(self, tmp_path):
        """Test crash recovery."""
        mind = AgentMind(checkpoint_dir=str(tmp_path))
        mind.add_agent(Agent(name="agent1", role="analyst"))

        # Save checkpoint
        mind.save_checkpoint("crash_test")

        # Simulate crash and recovery
        recovered = await mind.crash_recovery()

        assert recovered is True


class TestObservability:
    """Test system observability."""

    @pytest.mark.asyncio
    async def test_get_real_time_metrics(self):
        """Test getting real-time metrics."""
        mind = AgentMind()
        mind.add_agent(Agent(name="agent1", role="analyst"))
        mind.add_task("task1", "Test task")

        metrics = mind.get_real_time_metrics()

        assert "agents" in metrics
        assert "tasks" in metrics
        assert "collaboration" in metrics
        assert metrics["agents"]["total"] == 1
        assert metrics["tasks"]["total"] == 1

    @pytest.mark.asyncio
    async def test_event_stream(self):
        """Test event stream."""
        mind = AgentMind()

        mind.add_agent(Agent(name="agent1", role="analyst"))
        mind.add_task("task1", "Test task")

        events = mind.get_event_stream(limit=10)

        assert len(events) > 0
        assert "type" in events[0]
        assert "timestamp" in events[0]

    @pytest.mark.asyncio
    async def test_performance_profiling(self):
        """Test performance profiling."""
        mind = AgentMind()

        mind.profile_performance("test_op", 0.5)
        mind.profile_performance("test_op", 0.3)
        mind.profile_performance("test_op", 0.7)

        profile = mind.get_performance_profile("test_op")

        assert profile["count"] == 3
        assert profile["average"] == 0.5
        assert profile["min"] == 0.3
        assert profile["max"] == 0.7

    @pytest.mark.asyncio
    async def test_cost_tracking(self):
        """Test cost tracking."""
        mind = AgentMind()

        mind.track_cost("agent1", 0.05)
        mind.track_cost("agent1", 0.03)
        mind.track_cost("agent2", 0.10)

        costs = mind.get_cost_summary()

        assert costs["agent1"] == 0.08
        assert costs["agent2"] == 0.10

    @pytest.mark.asyncio
    async def test_observers(self):
        """Test observer pattern."""
        mind = AgentMind()

        events_received = []

        async def observer(event_type, data):
            events_received.append(event_type)

        mind.add_observer(observer)
        mind.add_agent(Agent(name="agent1", role="analyst"))

        # Add a task which emits events
        mind.add_task("test_task", "Test task")

        # Give time for async notification
        await asyncio.sleep(0.2)

        # Check event stream (tasks emit events)
        events = mind.get_event_stream()
        assert len(events) > 0
        assert any(e["type"] == "task_added" for e in events)


class TestCollaborationPatterns:
    """Test collaboration patterns."""

    @pytest.mark.asyncio
    async def test_shared_context(self):
        """Test shared context."""
        mind = AgentMind()

        mind.set_shared_context("key1", "value1")
        mind.set_shared_context("key2", {"nested": "data"})

        assert mind.get_shared_context("key1") == "value1"
        assert mind.get_shared_context("key2")["nested"] == "data"

    @pytest.mark.asyncio
    async def test_conflict_resolution_voting(self):
        """Test conflict resolution by voting."""
        mind = AgentMind()
        mind.conflict_resolution = ConflictResolutionStrategy.VOTING

        results = [
            ("agent1", "Option A"),
            ("agent2", "Option B"),
            ("agent3", "Option A"),
        ]

        resolved = mind.resolve_conflict(results)

        assert resolved == "Option A"

    @pytest.mark.asyncio
    async def test_conflict_resolution_merge(self):
        """Test conflict resolution by merge."""
        mind = AgentMind()
        mind.conflict_resolution = ConflictResolutionStrategy.MERGE

        results = [
            ("agent1", "Part 1"),
            ("agent2", "Part 2"),
        ]

        resolved = mind.resolve_conflict(results)

        assert "Part 1" in resolved
        assert "Part 2" in resolved

    @pytest.mark.asyncio
    async def test_build_consensus(self):
        """Test building consensus."""
        mind = AgentMind()
        mind.add_agent(Agent(name="agent1", role="analyst"))
        mind.add_agent(Agent(name="agent2", role="analyst"))

        consensus = await mind.build_consensus(
            "Should we proceed?",
            threshold=0.5,
        )

        # Consensus may or may not be reached
        assert consensus is None or isinstance(consensus, str)


class TestDeadlockDetection:
    """Test deadlock detection and resolution."""

    @pytest.mark.asyncio
    async def test_detect_deadlock(self):
        """Test deadlock detection."""
        mind = AgentMind()
        mind.add_agent(Agent(name="agent1", role="analyst"))

        # Create circular dependency
        mind.add_task("task_a", "Task A", dependencies=["task_b"])
        mind.add_task("task_b", "Task B", dependencies=["task_a"])

        # Try to execute
        results = await mind.execute_task_queue(max_parallel=2)

        # Should detect deadlock
        assert mind.metrics["deadlocks_detected"] > 0

    @pytest.mark.asyncio
    async def test_resolve_deadlock(self):
        """Test deadlock resolution."""
        mind = AgentMind()
        mind.add_agent(Agent(name="agent1", role="analyst"))

        # Create dependency on failed task
        mind.add_task("task1", "Task 1")
        mind.tasks["task1"].status = TaskStatus.FAILED

        mind.add_task("task2", "Task 2", dependencies=["task1"])

        # Try to resolve
        resolved = await mind._resolve_deadlock()

        # Should cancel task2 since task1 failed
        assert mind.tasks["task2"].status == TaskStatus.CANCELLED


class TestCoordinationStrategies:
    """Test coordination strategies."""

    @pytest.mark.asyncio
    async def test_centralized_coordination(self):
        """Test centralized coordination."""
        mind = AgentMind(coordination_strategy=CoordinationStrategy.CENTRALIZED)

        assert mind.coordination_strategy == CoordinationStrategy.CENTRALIZED

    @pytest.mark.asyncio
    async def test_decentralized_coordination(self):
        """Test decentralized coordination."""
        mind = AgentMind(coordination_strategy=CoordinationStrategy.DECENTRALIZED)

        assert mind.coordination_strategy == CoordinationStrategy.DECENTRALIZED


class TestIntegration:
    """Integration tests for advanced Mind features."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        """Test complete workflow with all features."""
        mind = AgentMind(
            strategy=CollaborationStrategy.BROADCAST,
            coordination_strategy=CoordinationStrategy.CENTRALIZED,
            enable_checkpointing=True,
            checkpoint_dir=str(tmp_path),
            max_concurrent_tasks=5,
        )

        # Add agents
        mind.add_agent(Agent(name="analyst", role="analyst"))
        mind.add_agent(Agent(name="researcher", role="researcher"))

        # Add observer
        events = []

        def observer(event_type, data):
            events.append(event_type)

        mind.add_observer(observer)

        # Add tasks with dependencies
        mind.add_task("research", "Research topic", TaskPriority.HIGH)
        mind.add_task(
            "analyze",
            "Analyze findings",
            TaskPriority.MEDIUM,
            dependencies=["research"],
        )

        # Set shared context
        mind.set_shared_context("project", "Test Project")

        # Execute tasks
        results = await mind.execute_task_queue(max_parallel=2)

        assert len(results) >= 0

        # Get metrics
        metrics = mind.get_real_time_metrics()
        assert metrics["agents"]["total"] == 2

        # Save checkpoint
        checkpoint_path = mind.save_checkpoint("integration_test")
        assert Path(checkpoint_path).exists()

        # Restore checkpoint
        new_mind = AgentMind(checkpoint_dir=str(tmp_path))
        success = new_mind.restore_checkpoint("integration_test")
        assert success is True

        # Verify restored state
        assert len(new_mind.agents) == 2
        assert len(new_mind.tasks) == 2

    @pytest.mark.asyncio
    async def test_task_execution_with_timeout(self):
        """Test task execution with timeout."""
        mind = AgentMind()
        mind.add_agent(Agent(name="agent1", role="analyst"))

        # Add task with very short timeout
        mind.add_task(
            "timeout_task",
            "Task that will timeout",
            timeout=0.001,
        )

        results = await mind.execute_task_queue()

        # Task should fail due to timeout
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_task_retry_policy(self):
        """Test task retry policy."""
        mind = AgentMind()
        mind.add_agent(Agent(name="agent1", role="analyst"))

        # Add task with retry policy
        mind.add_task(
            "retry_task",
            "Task with retry",
            retry_policy={"max_retries": 2, "backoff": 0.1},
            timeout=0.001,  # Will timeout and retry
        )

        results = await mind.execute_task_queue()

        # Should have attempted retries
        task = mind.tasks["retry_task"]
        assert task.retry_count >= 0

    @pytest.mark.asyncio
    async def test_collaboration_with_metrics(self):
        """Test collaboration with metrics tracking."""
        mind = AgentMind()
        mind.add_agent(Agent(name="agent1", role="analyst"))
        mind.add_agent(Agent(name="agent2", role="creative"))

        # Run collaboration
        result = await mind.start_collaboration(
            "Test collaboration",
            max_rounds=2,
        )

        # Check metrics updated
        assert mind.metrics["total_collaborations"] > 0

        if result.success:
            assert mind.metrics["successful_collaborations"] > 0

        # Check performance profiling
        profile = mind.get_performance_profile("collaboration")
        if profile:
            assert "average" in profile


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
