"""Advanced Mind Features Example.

Demonstrates:
- Global orchestration with resource allocation
- Checkpointing and recovery
- Advanced task management with DAG dependencies
- System observability with real - time metrics
- Collaboration patterns with conflict resolution
"""

import asyncio

from agentmind.core.agent import Agent
from agentmind.core.mind import (
    AgentMind,
    TaskPriority,
    CoordinationStrategy,
    ConflictResolutionStrategy,
)
from agentmind.core.types import CollaborationStrategy


# Observer callback
def system_observer(event_type, data):
    """Observe system events."""
    print(f"[OBSERVER] {event_type}: {data}")


async def demo_task_management():
    """Demonstrate advanced task management with dependencies."""
    print("\n" + "=" * 60)
    print("DEMO 1: Advanced Task Management")
    print("=" * 60)

    mind = AgentMind(
        strategy=CollaborationStrategy.BROADCAST,
        coordination_strategy=CoordinationStrategy.CENTRALIZED,
    )

    # Add agents
    mind.add_agent(Agent(name="analyst", role="analyst"))
    mind.add_agent(Agent(name="researcher", role="researcher"))
    mind.add_agent(Agent(name="writer", role="creative"))

    # Add tasks with dependencies (DAG)
    # Task 1: Research (no dependencies)
    mind.add_task(
        task_id="research",
        description="Research the topic",
        priority=TaskPriority.HIGH,
        assigned_agents=["researcher"],
    )

    # Task 2: Analyze (depends on research)
    mind.add_task(
        task_id="analyze",
        description="Analyze the research findings",
        priority=TaskPriority.HIGH,
        assigned_agents=["analyst"],
        dependencies=["research"],
    )

    # Task 3: Write report (depends on analysis)
    mind.add_task(
        task_id="write",
        description="Write a comprehensive report",
        priority=TaskPriority.MEDIUM,
        assigned_agents=["writer"],
        dependencies=["analyze"],
    )

    # Task 4: Independent task
    mind.add_task(
        task_id="summary",
        description="Create a quick summary",
        priority=TaskPriority.CRITICAL,
        assigned_agents=["writer"],
    )

    print(f"\nAdded {len(mind.tasks)} tasks")

    # Check task status
    for task_id in ["research", "analyze", "write", "summary"]:
        status = mind.get_task_status(task_id)
        print(f"  {task_id}: {status['status']}")

    # Get ready tasks
    ready = mind.get_ready_tasks()
    print(f"\nReady tasks: {ready}")

    # Execute task queue
    print("\nExecuting task queue...")
    results = await mind.execute_task_queue(max_parallel=2)

    print(f"\nCompleted {len(results)} tasks")
    for i, result in enumerate(results):
        print(f"  Task {i + 1}: Success={result.success}")


async def demo_resource_allocation():
    """Demonstrate resource allocation and scheduling."""
    print("\n" + "=" * 60)
    print("DEMO 2: Resource Allocation")
    print("=" * 60)

    mind = AgentMind(max_concurrent_tasks=3)

    # Add agents
    for i in range(5):
        mind.add_agent(Agent(name=f"agent_{i}", role="assistant"))

    # Set resource limits
    mind.resource_allocation.resource_limits["agent_0"] = 2
    mind.resource_allocation.resource_limits["agent_1"] = 1

    # Allocate resources
    print("\nAllocating resources:")
    for i in range(3):
        success = mind.resource_allocation.allocate(f"agent_{i}", 1)
        print(f"  agent_{i}: {'allocated' if success else 'failed'}")

    # Check available resources
    print("\nAvailable resources:")
    for i in range(3):
        available = mind.resource_allocation.get_available(f"agent_{i}")
        print(f"  agent_{i}: {available}")

    # Release resources
    mind.resource_allocation.release("agent_0", 1)
    print("\nReleased resources from agent_0")

    available = mind.resource_allocation.get_available("agent_0")
    print(f"  agent_0 now has {available} available")


async def demo_checkpointing():
    """Demonstrate checkpointing and recovery."""
    print("\n" + "=" * 60)
    print("DEMO 3: Checkpointing & Recovery")
    print("=" * 60)

    mind = AgentMind(enable_checkpointing=True)

    # Add agents
    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    # Add some tasks
    mind.add_task("task1", "First task", TaskPriority.HIGH)
    mind.add_task("task2", "Second task", TaskPriority.MEDIUM)

    # Run a collaboration
    result = await mind.start_collaboration("Solve this problem", max_rounds=2)

    print(f"\nCollaboration completed: {result.success}")
    print(f"Messages: {result.total_messages}")

    # Save checkpoint
    checkpoint_path = mind.save_checkpoint("demo_checkpoint")
    print(f"\nCheckpoint saved: {checkpoint_path}")

    # Create new mind and restore
    new_mind = AgentMind()
    success = new_mind.restore_checkpoint("demo_checkpoint")

    print(f"\nCheckpoint restored: {success}")
    print(f"  Agents: {len(new_mind.agents)}")
    print(f"  Tasks: {len(new_mind.tasks)}")
    print(f"  Messages: {len(new_mind.conversation_history)}")

    # Demonstrate crash recovery
    print("\nSimulating crash recovery...")
    recovered = await new_mind.crash_recovery()
    print(f"Crash recovery: {recovered}")


async def demo_observability():
    """Demonstrate system observability."""
    print("\n" + "=" * 60)
    print("DEMO 4: System Observability")
    print("=" * 60)

    mind = AgentMind()

    # Add observer
    mind.add_observer(system_observer)

    # Add agents
    mind.add_agent(Agent(name="observer_agent", role="analyst"))

    # Add task (will trigger events)
    mind.add_task("observed_task", "Task to observe", TaskPriority.HIGH)

    # Get real - time metrics
    metrics = mind.get_real_time_metrics()
    print("\nReal - time Metrics:")
    print(f"  Agents: {metrics['agents']}")
    print(f"  Tasks: {metrics['tasks']}")
    print(f"  Collaboration: {metrics['collaboration']}")

    # Run collaboration to generate events
    await mind.start_collaboration("Test collaboration", max_rounds=1)

    # Get event stream
    events = mind.get_event_stream(limit=10)
    print(f"\nRecent events: {len(events)}")
    for event in events[-3:]:
        print(f"  {event['type']} at {event['timestamp']}")

    # Profile performance
    mind.profile_performance("test_operation", 0.5)
    mind.profile_performance("test_operation", 0.3)
    mind.profile_performance("test_operation", 0.7)

    profile = mind.get_performance_profile("test_operation")
    print("\nPerformance profile for 'test_operation':")
    print(f"  Count: {profile['count']}")
    print(f"  Average: {profile['average']:.3f}s")
    print(f"  Min: {profile['min']:.3f}s")
    print(f"  Max: {profile['max']:.3f}s")

    # Track costs
    mind.track_cost("observer_agent", 0.05)
    mind.track_cost("observer_agent", 0.03)

    costs = mind.get_cost_summary()
    print("\nCost summary:")
    for agent, cost in costs.items():
        print(f"  {agent}: ${cost:.4f}")


async def demo_collaboration_patterns():
    """Demonstrate collaboration patterns."""
    print("\n" + "=" * 60)
    print("DEMO 5: Collaboration Patterns")
    print("=" * 60)

    mind = AgentMind(coordination_strategy=CoordinationStrategy.DECENTRALIZED)

    # Add agents
    mind.add_agent(Agent(name="agent_a", role="analyst"))
    mind.add_agent(Agent(name="agent_b", role="creative"))
    mind.add_agent(Agent(name="agent_c", role="critic"))

    # Shared context
    mind.set_shared_context("project_goal", "Build an AI system")
    mind.set_shared_context("deadline", "2024 - 12 - 31")

    goal = mind.get_shared_context("project_goal")
    print(f"\nShared context - Project goal: {goal}")

    # Conflict resolution
    conflicting_results = [
        ("agent_a", "Approach A is best"),
        ("agent_b", "Approach B is best"),
        ("agent_c", "Approach A is best"),
    ]

    # Resolve by voting
    mind.conflict_resolution = ConflictResolutionStrategy.VOTING
    resolved = mind.resolve_conflict(conflicting_results)
    print(f"\nConflict resolved by voting: {resolved}")

    # Resolve by merge
    mind.conflict_resolution = ConflictResolutionStrategy.MERGE
    resolved = mind.resolve_conflict(conflicting_results)
    print(f"Conflict resolved by merge: {resolved}")

    # Build consensus
    print("\nBuilding consensus...")
    consensus = await mind.build_consensus(
        "Should we use approach A or B?",
        threshold=0.6,
    )
    print(f"Consensus result: {consensus}")


async def demo_deadlock_detection():
    """Demonstrate deadlock detection and resolution."""
    print("\n" + "=" * 60)
    print("DEMO 6: Deadlock Detection")
    print("=" * 60)

    mind = AgentMind()

    # Add agents
    mind.add_agent(Agent(name="agent1", role="analyst"))

    # Create circular dependency (will cause deadlock)
    mind.add_task("task_a", "Task A", dependencies=["task_b"])
    mind.add_task("task_b", "Task B", dependencies=["task_c"])
    mind.add_task("task_c", "Task C", dependencies=["task_a"])

    print("\nCreated tasks with circular dependencies")
    print("Tasks: task_a -> task_b -> task_c -> task_a")

    # Try to execute (will detect deadlock)
    print("\nAttempting to execute tasks...")
    results = await mind.execute_task_queue(max_parallel=2)

    print(f"\nExecution completed with {len(results)} results")
    print(f"Deadlocks detected: {mind.metrics['deadlocks_detected']}")
    print(f"Deadlocks resolved: {mind.metrics['deadlocks_resolved']}")


async def demo_priority_scheduling():
    """Demonstrate priority - based task scheduling."""
    print("\n" + "=" * 60)
    print("DEMO 7: Priority Scheduling")
    print("=" * 60)

    mind = AgentMind()

    # Add agents
    mind.add_agent(Agent(name="worker", role="executor"))

    # Add tasks with different priorities
    mind.add_task("low_task", "Low priority task", TaskPriority.LOW)
    mind.add_task("critical_task", "Critical task", TaskPriority.CRITICAL)
    mind.add_task("medium_task", "Medium priority task", TaskPriority.MEDIUM)
    mind.add_task("high_task", "High priority task", TaskPriority.HIGH)

    print("\nTask queue order (by priority):")
    for task_id in mind.task_queue:
        task = mind.tasks[task_id]
        print(f"  {task_id}: {task.priority.value}")

    # Execute tasks
    print("\nExecuting tasks...")
    results = await mind.execute_task_queue(max_parallel=1)

    print(f"\nCompleted {len(results)} tasks in priority order")


async def demo_task_cancellation():
    """Demonstrate task cancellation and timeout."""
    print("\n" + "=" * 60)
    print("DEMO 8: Task Cancellation & Timeout")
    print("=" * 60)

    mind = AgentMind()

    # Add agents
    mind.add_agent(Agent(name="agent", role="assistant"))

    # Add tasks
    mind.add_task("task1", "Task 1", TaskPriority.HIGH)
    mind.add_task("task2", "Task 2", TaskPriority.MEDIUM)
    mind.add_task("task3", "Task 3 with timeout", TaskPriority.LOW, timeout=0.1)

    print(f"\nAdded {len(mind.tasks)} tasks")

    # Cancel a task
    cancelled = mind.cancel_task("task2")
    print(f"\nCancelled task2: {cancelled}")

    # Check status
    status = mind.get_task_status("task2")
    print(f"task2 status: {status['status']}")

    # Execute remaining tasks
    print("\nExecuting tasks...")
    results = await mind.execute_task_queue()

    print(f"\nCompleted {len(results)} tasks")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("ADVANCED MIND FEATURES DEMONSTRATION")
    print("=" * 60)

    await demo_task_management()
    await demo_resource_allocation()
    await demo_checkpointing()
    await demo_observability()
    await demo_collaboration_patterns()
    await demo_deadlock_detection()
    await demo_priority_scheduling()
    await demo_task_cancellation()

    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
