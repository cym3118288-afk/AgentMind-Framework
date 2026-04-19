"""AgentMind orchestration system for multi-agent collaboration.

This module provides the AgentMind class which manages multiple agents,
coordinates their communication, and orchestrates collaborative problem-solving.

Enhanced with:
- Global orchestration with multi-agent coordination strategies
- Checkpointing and recovery with crash recovery
- Advanced task management with DAG dependencies
- System observability with real-time metrics
- Collaboration patterns with conflict resolution
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum
from collections import defaultdict, deque

from ..llm.provider import LLMProvider
from .agent import Agent
from .types import CollaborationResult, CollaborationStrategy, Message, MessageRole


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class CoordinationStrategy(str, Enum):
    """Multi-agent coordination strategies."""

    CENTRALIZED = "centralized"  # Central coordinator
    DECENTRALIZED = "decentralized"  # Peer-to-peer
    AUCTION = "auction"  # Task bidding
    VOTING = "voting"  # Democratic decision
    CONSENSUS = "consensus"  # Require agreement


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving agent conflicts."""

    PRIORITY = "priority"  # Higher priority wins
    VOTING = "voting"  # Majority vote
    SUPERVISOR = "supervisor"  # Supervisor decides
    MERGE = "merge"  # Merge conflicting results


class Task:
    """Represents a task in the system with dependencies."""

    def __init__(
        self,
        task_id: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_agents: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        retry_policy: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.description = description
        self.priority = priority
        self.assigned_agents = assigned_agents or []
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.retry_policy = retry_policy or {"max_retries": 3, "backoff": 1.0}
        self.metadata = metadata or {}
        self.status = TaskStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.retry_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "priority": self.priority.value,
            "assigned_agents": self.assigned_agents,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
        }


class ResourceAllocation:
    """Manages resource allocation across agents."""

    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.allocated_resources: Dict[str, int] = {}
        self.resource_limits: Dict[str, int] = {}

    def allocate(self, agent_name: str, amount: int = 1) -> bool:
        """Allocate resources to an agent."""
        current = self.allocated_resources.get(agent_name, 0)
        limit = self.resource_limits.get(agent_name, self.max_concurrent_tasks)

        if current + amount <= limit:
            self.allocated_resources[agent_name] = current + amount
            return True
        return False

    def release(self, agent_name: str, amount: int = 1) -> None:
        """Release resources from an agent."""
        current = self.allocated_resources.get(agent_name, 0)
        self.allocated_resources[agent_name] = max(0, current - amount)

    def get_available(self, agent_name: str) -> int:
        """Get available resources for an agent."""
        current = self.allocated_resources.get(agent_name, 0)
        limit = self.resource_limits.get(agent_name, self.max_concurrent_tasks)
        return limit - current


class AgentMind:
    """Central orchestrator for multi-agent collaboration.

    AgentMind manages a collection of agents and coordinates their communication
    through various collaboration strategies (broadcast, round-robin, hierarchical, etc.).

    Enhanced Features:
    - Global orchestration with resource allocation and scheduling
    - Checkpointing and recovery with crash recovery
    - Advanced task management with DAG dependencies
    - System observability with real-time metrics
    - Collaboration patterns with conflict resolution
    - Deadlock detection and resolution

    Attributes:
        agents: List of agents in the system
        conversation_history: Complete history of all messages
        is_running: Whether a collaboration session is currently active
        strategy: The collaboration strategy being used
        tasks: Dictionary of tasks by ID
        metrics: System-wide performance metrics

    Example:
        >>> mind = AgentMind()
        >>> mind.add_agent(Agent(name="analyst", role="analyst"))
        >>> mind.add_agent(Agent(name="creative", role="creative"))
        >>> result = await mind.start_collaboration("Analyze this problem")
    """

    def __init__(
        self,
        strategy: CollaborationStrategy = CollaborationStrategy.BROADCAST,
        llm_provider: Optional[LLMProvider] = None,
        coordination_strategy: CoordinationStrategy = CoordinationStrategy.CENTRALIZED,
        enable_checkpointing: bool = True,
        checkpoint_dir: str = ".agentmind_checkpoints",
        max_concurrent_tasks: int = 10,
    ) -> None:
        """Initialize a new AgentMind orchestrator.

        Args:
            strategy: The collaboration strategy to use (default: broadcast)
            llm_provider: Optional LLM provider to use for all agents
            coordination_strategy: Multi-agent coordination strategy
            enable_checkpointing: Enable automatic checkpointing
            checkpoint_dir: Directory for checkpoint files
            max_concurrent_tasks: Maximum concurrent tasks
        """
        self.agents: List[Agent] = []
        self.conversation_history: List[Message] = []
        self.is_running = False
        self.strategy = strategy
        self.llm_provider = llm_provider
        self.coordination_strategy = coordination_strategy

        # Task management
        self.tasks: Dict[str, Task] = {}
        self.task_queue: deque = deque()
        self.running_tasks: Set[str] = set()
        self.task_graph: Dict[str, List[str]] = {}  # task_id -> dependent tasks

        # Resource management
        self.resource_allocation = ResourceAllocation(max_concurrent_tasks)

        # Checkpointing
        self.enable_checkpointing = enable_checkpointing
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.last_checkpoint: Optional[str] = None

        # Metrics and observability
        self.metrics = {
            "total_collaborations": 0,
            "successful_collaborations": 0,
            "failed_collaborations": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_messages": 0,
            "average_collaboration_time": 0.0,
            "deadlocks_detected": 0,
            "deadlocks_resolved": 0,
        }
        self.event_stream: List[Dict[str, Any]] = []
        self.performance_profiles: Dict[str, List[float]] = defaultdict(list)

        # Collaboration patterns
        self.shared_context: Dict[str, Any] = {}
        self.conflict_resolution = ConflictResolutionStrategy.PRIORITY
        self.consensus_threshold = 0.7  # 70% agreement for consensus

        # Observers and hooks
        self.observers: List[Callable] = []

        print("[AgentMind] Initialized - Multi-agent collaboration framework started!")
        print(
            f"[*] Coordination: {coordination_strategy.value}, Checkpointing: {enable_checkpointing}"
        )

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the collaboration system.

        Args:
            agent: The agent to add

        Raises:
            ValueError: If an agent with the same name already exists

        Example:
            >>> mind = AgentMind()
            >>> agent = Agent(name="analyst", role="analyst")
            >>> mind.add_agent(agent)
        """
        # Check for duplicate names
        if any(a.name == agent.name for a in self.agents):
            raise ValueError(f"Agent with name '{agent.name}' already exists")

        # Set LLM provider if not already set
        if self.llm_provider and not agent.llm_provider:
            agent.llm_provider = self.llm_provider

        self.agents.append(agent)
        print(f"[+] Added agent: {agent.name} ({agent.role})")

    # ==================== Advanced Task Management ====================

    def add_task(
        self,
        task_id: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_agents: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        retry_policy: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """Add a task with dependencies and priority.

        Args:
            task_id: Unique task identifier
            description: Task description
            priority: Task priority level
            assigned_agents: List of agent names to assign
            dependencies: List of task IDs this task depends on
            timeout: Task timeout in seconds
            retry_policy: Retry configuration

        Returns:
            Created task object
        """
        if task_id in self.tasks:
            raise ValueError(f"Task '{task_id}' already exists")

        task = Task(
            task_id=task_id,
            description=description,
            priority=priority,
            assigned_agents=assigned_agents,
            dependencies=dependencies or [],
            timeout=timeout,
            retry_policy=retry_policy,
        )

        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        self.metrics["total_tasks"] += 1

        # Build task graph for dependency tracking
        for dep_id in task.dependencies:
            if dep_id not in self.task_graph:
                self.task_graph[dep_id] = []
            self.task_graph[dep_id].append(task_id)

        # Sort queue by priority
        self._sort_task_queue()

        self._emit_event("task_added", {"task_id": task_id, "priority": priority.value})
        print(f"[Task] Added: {task_id} (priority: {priority.value})")

        return task

    def _sort_task_queue(self) -> None:
        """Sort task queue by priority."""
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }

        sorted_tasks = sorted(
            self.task_queue, key=lambda tid: priority_order.get(self.tasks[tid].priority, 99)
        )
        self.task_queue = deque(sorted_tasks)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled successfully
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()

        if task_id in self.task_queue:
            self.task_queue.remove(task_id)

        if task_id in self.running_tasks:
            self.running_tasks.remove(task_id)

        self._emit_event("task_cancelled", {"task_id": task_id})
        print(f"[Task] Cancelled: {task_id}")

        return True

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task.

        Args:
            task_id: Task ID

        Returns:
            Task status dictionary or None
        """
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        return task.to_dict()

    def get_ready_tasks(self) -> List[str]:
        """Get tasks that are ready to execute (dependencies met).

        Returns:
            List of ready task IDs
        """
        ready = []

        for task_id in self.task_queue:
            task = self.tasks[task_id]

            if task.status != TaskStatus.PENDING:
                continue

            # Check if all dependencies are completed
            deps_met = all(
                self.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
                if dep_id in self.tasks
            )

            if deps_met:
                ready.append(task_id)

        return ready

    async def execute_task_queue(
        self, max_parallel: int = 3, stop_on_error: bool = False
    ) -> List[CollaborationResult]:
        """Execute all tasks in the queue with dependency resolution.

        Args:
            max_parallel: Maximum parallel task execution
            stop_on_error: Stop execution if a task fails

        Returns:
            List of collaboration results
        """
        results = []
        self._emit_event("task_queue_execution_started", {"queue_size": len(self.task_queue)})

        while self.task_queue or self.running_tasks:
            # Get ready tasks
            ready_tasks = self.get_ready_tasks()

            # Check for deadlock
            if not ready_tasks and self.running_tasks:
                await asyncio.sleep(0.1)
                continue
            elif not ready_tasks and not self.running_tasks:
                # Possible deadlock
                if self.task_queue:
                    deadlock_resolved = await self._resolve_deadlock()
                    if not deadlock_resolved:
                        print("[!] Deadlock detected and could not be resolved")
                        break
                else:
                    break

            # Execute batch of ready tasks
            batch = ready_tasks[:max_parallel]

            if batch:
                batch_results = await asyncio.gather(
                    *[self._execute_single_task(task_id) for task_id in batch],
                    return_exceptions=True,
                )

                for result in batch_results:
                    if isinstance(result, CollaborationResult):
                        results.append(result)
                        if not result.success and stop_on_error:
                            print("[!] Task failed, stopping execution")
                            return results

        self._emit_event("task_queue_execution_completed", {"total_results": len(results)})
        return results

    async def _execute_single_task(self, task_id: str) -> CollaborationResult:
        """Execute a single task.

        Args:
            task_id: Task ID to execute

        Returns:
            Collaboration result
        """
        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self.running_tasks.add(task_id)

        # Remove from queue
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)

        self._emit_event("task_started", {"task_id": task_id})
        print(f"[Task] Executing: {task_id}")

        # Allocate resources
        for agent_name in task.assigned_agents:
            self.resource_allocation.allocate(agent_name)

        try:
            # Execute with timeout
            if task.timeout:
                result = await asyncio.wait_for(
                    self.start_collaboration(task.description, max_rounds=10, use_llm=True),
                    timeout=task.timeout,
                )
            else:
                result = await self.start_collaboration(
                    task.description, max_rounds=10, use_llm=True
                )

            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            self.metrics["completed_tasks"] += 1

            self._emit_event("task_completed", {"task_id": task_id, "success": result.success})

            return result

        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = "Task timeout"
            task.completed_at = datetime.now()
            self.metrics["failed_tasks"] += 1

            # Retry if policy allows
            if task.retry_count < task.retry_policy.get("max_retries", 0):
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                self.task_queue.append(task_id)
                print(f"[Task] Retrying {task_id} (attempt {task.retry_count})")

            self._emit_event("task_failed", {"task_id": task_id, "error": "timeout"})

            return CollaborationResult(
                success=False, error="Task timeout", total_rounds=0, total_messages=0
            )

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            self.metrics["failed_tasks"] += 1

            self._emit_event("task_failed", {"task_id": task_id, "error": str(e)})
            print(f"[!] Task {task_id} failed: {e}")

            return CollaborationResult(
                success=False, error=str(e), total_rounds=0, total_messages=0
            )

        finally:
            self.running_tasks.discard(task_id)

            # Release resources
            for agent_name in task.assigned_agents:
                self.resource_allocation.release(agent_name)

    async def _resolve_deadlock(self) -> bool:
        """Attempt to resolve a deadlock situation.

        Returns:
            True if deadlock was resolved
        """
        self.metrics["deadlocks_detected"] += 1
        print("[!] Deadlock detected, attempting resolution...")

        # Find tasks with unmet dependencies
        blocked_tasks = []
        for task_id in self.task_queue:
            task = self.tasks[task_id]
            if task.status == TaskStatus.PENDING:
                unmet_deps = [
                    dep_id
                    for dep_id in task.dependencies
                    if dep_id in self.tasks and self.tasks[dep_id].status != TaskStatus.COMPLETED
                ]
                if unmet_deps:
                    blocked_tasks.append((task_id, unmet_deps))

        if not blocked_tasks:
            return True

        # Strategy: Cancel lowest priority blocked task
        blocked_tasks.sort(key=lambda x: self.tasks[x[0]].priority.value, reverse=True)

        for task_id, unmet_deps in blocked_tasks:
            # Check if dependencies are failed or cancelled
            failed_deps = [
                dep_id
                for dep_id in unmet_deps
                if self.tasks[dep_id].status in [TaskStatus.FAILED, TaskStatus.CANCELLED]
            ]

            if failed_deps:
                # Cancel this task since its dependencies failed
                self.cancel_task(task_id)
                self.metrics["deadlocks_resolved"] += 1
                print(f"[*] Resolved deadlock by cancelling {task_id}")
                return True

        return False

    # ==================== Checkpointing & Recovery ====================

    def save_checkpoint(self, checkpoint_name: Optional[str] = None) -> str:
        """Save complete system state to checkpoint.

        Args:
            checkpoint_name: Optional checkpoint name (auto-generated if None)

        Returns:
            Path to checkpoint file
        """
        if checkpoint_name is None:
            checkpoint_name = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"

        checkpoint_data = {
            "checkpoint_name": checkpoint_name,
            "timestamp": datetime.now().isoformat(),
            "strategy": self.strategy.value,
            "coordination_strategy": self.coordination_strategy.value,
            "agents": [
                {
                    "name": agent.name,
                    "role": agent.role,
                    "config": agent.config.model_dump(),
                    "memory": [msg.model_dump(mode="json") for msg in agent.memory[-50:]],
                    "is_active": agent.is_active,
                    "state": agent.state.value if hasattr(agent, "state") else "idle",
                }
                for agent in self.agents
            ],
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "conversation_history": [
                msg.model_dump(mode="json") for msg in self.conversation_history[-100:]
            ],
            "metrics": self.metrics,
            "shared_context": self.shared_context,
        }

        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        self.last_checkpoint = str(checkpoint_file)
        print(f"[Checkpoint] Saved: {checkpoint_file}")

        return str(checkpoint_file)

    def restore_checkpoint(self, checkpoint_name: str) -> bool:
        """Restore system state from checkpoint.

        Args:
            checkpoint_name: Name of checkpoint to restore

        Returns:
            True if restored successfully
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"

        if not checkpoint_file.exists():
            print(f"[!] Checkpoint not found: {checkpoint_file}")
            return False

        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint_data = json.load(f)

            # Clear current state
            self.reset()

            # Restore configuration
            self.strategy = CollaborationStrategy(checkpoint_data["strategy"])
            self.coordination_strategy = CoordinationStrategy(
                checkpoint_data["coordination_strategy"]
            )

            # Restore agents
            from .types import AgentConfig

            for agent_data in checkpoint_data["agents"]:
                config = AgentConfig(**agent_data["config"])
                agent = Agent(
                    name=agent_data["name"],
                    role=agent_data["role"],
                    config=config,
                    llm_provider=self.llm_provider,
                )

                # Restore agent memory
                agent.memory = [Message(**msg_data) for msg_data in agent_data["memory"]]
                agent.is_active = agent_data["is_active"]

                self.agents.append(agent)

            # Restore tasks
            for task_id, task_data in checkpoint_data["tasks"].items():
                task = Task(
                    task_id=task_data["task_id"],
                    description=task_data["description"],
                    priority=TaskPriority(task_data["priority"]),
                    assigned_agents=task_data["assigned_agents"],
                    dependencies=task_data["dependencies"],
                )
                task.status = TaskStatus(task_data["status"])
                task.retry_count = task_data["retry_count"]
                self.tasks[task_id] = task

                if task.status == TaskStatus.PENDING:
                    self.task_queue.append(task_id)

            # Restore conversation history
            self.conversation_history = [
                Message(**msg_data) for msg_data in checkpoint_data["conversation_history"]
            ]

            # Restore metrics
            self.metrics = checkpoint_data["metrics"]

            # Restore shared context
            self.shared_context = checkpoint_data["shared_context"]

            print(f"[Checkpoint] Restored: {checkpoint_name}")
            print(f"  - Agents: {len(self.agents)}")
            print(f"  - Tasks: {len(self.tasks)}")
            print(f"  - Messages: {len(self.conversation_history)}")

            return True

        except Exception as e:
            print(f"[!] Failed to restore checkpoint: {e}")
            return False

    async def crash_recovery(self) -> bool:
        """Attempt to recover from a crash using last checkpoint.

        Returns:
            True if recovery successful
        """
        if not self.last_checkpoint:
            print("[!] No checkpoint available for crash recovery")
            return False

        print("[*] Attempting crash recovery...")

        checkpoint_name = Path(self.last_checkpoint).stem
        success = self.restore_checkpoint(checkpoint_name)

        if success:
            print("[*] Crash recovery successful")
            # Resume pending tasks
            if self.task_queue:
                print(f"[*] Resuming {len(self.task_queue)} pending tasks")
        else:
            print("[!] Crash recovery failed")

        return success

    # ==================== System Observability ====================

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics.

        Returns:
            Comprehensive metrics dictionary
        """
        return {
            "agents": {
                "total": len(self.agents),
                "active": len([a for a in self.agents if a.is_active]),
                "by_role": self._count_agents_by_role(),
            },
            "tasks": {
                "total": len(self.tasks),
                "pending": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                "running": len(self.running_tasks),
                "completed": self.metrics["completed_tasks"],
                "failed": self.metrics["failed_tasks"],
                "queue_size": len(self.task_queue),
            },
            "collaboration": {
                "total": self.metrics["total_collaborations"],
                "successful": self.metrics["successful_collaborations"],
                "failed": self.metrics["failed_collaborations"],
                "success_rate": self._calculate_success_rate(),
            },
            "messages": {
                "total": len(self.conversation_history),
                "recent": len(self.conversation_history[-100:]),
            },
            "performance": {
                "average_collaboration_time": self.metrics["average_collaboration_time"],
                "deadlocks_detected": self.metrics["deadlocks_detected"],
                "deadlocks_resolved": self.metrics["deadlocks_resolved"],
            },
            "resources": {
                "allocated": dict(self.resource_allocation.allocated_resources),
                "max_concurrent": self.resource_allocation.max_concurrent_tasks,
            },
        }

    def _count_agents_by_role(self) -> Dict[str, int]:
        """Count agents by role."""
        counts: Dict[str, int] = {}
        for agent in self.agents:
            counts[agent.role] = counts.get(agent.role, 0) + 1
        return counts

    def _calculate_success_rate(self) -> float:
        """Calculate collaboration success rate."""
        total = self.metrics["total_collaborations"]
        if total == 0:
            return 0.0
        return self.metrics["successful_collaborations"] / total

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to the event stream.

        Args:
            event_type: Type of event
            data: Event data
        """
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        self.event_stream.append(event)

        # Keep only recent events
        if len(self.event_stream) > 1000:
            self.event_stream = self.event_stream[-1000:]

        # Notify observers
        asyncio.create_task(self._notify_observers(event_type, data))

    def get_event_stream(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events from the event stream.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        return self.event_stream[-limit:]

    def profile_performance(self, operation: str, duration: float) -> None:
        """Record performance profile for an operation.

        Args:
            operation: Operation name
            duration: Duration in seconds
        """
        self.performance_profiles[operation].append(duration)

        # Keep only recent profiles
        if len(self.performance_profiles[operation]) > 100:
            self.performance_profiles[operation] = self.performance_profiles[operation][-100:]

    def get_performance_profile(self, operation: str) -> Dict[str, float]:
        """Get performance statistics for an operation.

        Args:
            operation: Operation name

        Returns:
            Performance statistics
        """
        if operation not in self.performance_profiles:
            return {}

        durations = self.performance_profiles[operation]

        return {
            "count": len(durations),
            "average": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
            "total": sum(durations),
        }

    def track_cost(self, agent_name: str, cost: float) -> None:
        """Track cost per agent/task.

        Args:
            agent_name: Agent name
            cost: Cost amount
        """
        if "costs" not in self.metrics:
            self.metrics["costs"] = {}

        if agent_name not in self.metrics["costs"]:
            self.metrics["costs"][agent_name] = 0.0

        self.metrics["costs"][agent_name] += cost

    def get_cost_summary(self) -> Dict[str, float]:
        """Get cost summary by agent.

        Returns:
            Cost summary dictionary
        """
        return self.metrics.get("costs", {})

    # ==================== Collaboration Patterns ====================

    def set_shared_context(self, key: str, value: Any) -> None:
        """Set shared context accessible to all agents.

        Args:
            key: Context key
            value: Context value
        """
        self.shared_context[key] = value
        self._emit_event("shared_context_updated", {"key": key})

    def get_shared_context(self, key: str) -> Optional[Any]:
        """Get shared context value.

        Args:
            key: Context key

        Returns:
            Context value or None
        """
        return self.shared_context.get(key)

    def resolve_conflict(
        self,
        conflicting_results: List[Tuple[str, Any]],
        strategy: Optional[ConflictResolutionStrategy] = None,
    ) -> Any:
        """Resolve conflicts between agent results.

        Args:
            conflicting_results: List of (agent_name, result) tuples
            strategy: Resolution strategy (uses default if None)

        Returns:
            Resolved result
        """
        if not conflicting_results:
            return None

        strategy = strategy or self.conflict_resolution

        if strategy == ConflictResolutionStrategy.PRIORITY:
            # Use result from highest priority agent
            # For now, use first result
            return conflicting_results[0][1]

        elif strategy == ConflictResolutionStrategy.VOTING:
            # Majority vote
            from collections import Counter

            results = [r[1] for r in conflicting_results]
            most_common = Counter(results).most_common(1)
            return most_common[0][0] if most_common else results[0]

        elif strategy == ConflictResolutionStrategy.SUPERVISOR:
            # Find supervisor agent
            supervisor = self.get_agent("supervisor")
            if supervisor:
                # Supervisor would decide (simplified)
                return conflicting_results[0][1]
            return conflicting_results[0][1]

        elif strategy == ConflictResolutionStrategy.MERGE:
            # Merge results (simplified - concatenate strings)
            merged = " | ".join(str(r[1]) for r in conflicting_results)
            return merged

        return conflicting_results[0][1]

    async def build_consensus(
        self, question: str, threshold: Optional[float] = None
    ) -> Optional[str]:
        """Build consensus among agents on a question.

        Args:
            question: Question to reach consensus on
            threshold: Agreement threshold (0.0-1.0)

        Returns:
            Consensus result or None
        """
        threshold = threshold or self.consensus_threshold

        if not self.agents:
            return None

        # Broadcast question to all agents
        message = Message(content=question, sender="system", role=MessageRole.SYSTEM)
        responses = await self.broadcast_message(message, exclude_sender=False, use_llm=True)

        if not responses:
            return None

        # Count similar responses
        from collections import Counter

        response_contents = [r.content for r in responses]
        counts = Counter(response_contents)
        most_common = counts.most_common(1)[0]

        agreement_rate = most_common[1] / len(responses)

        if agreement_rate >= threshold:
            print(f"[Consensus] Reached with {agreement_rate:.1%} agreement")
            return most_common[0]
        else:
            print(f"[Consensus] Not reached (only {agreement_rate:.1%} agreement)")
            return None

    def add_observer(self, observer: Callable) -> None:
        """Add an observer for system events.

        Args:
            observer: Observer callback function
        """
        self.observers.append(observer)

    async def _notify_observers(self, event_type: str, data: Any) -> None:
        """Notify all observers of an event.

        Args:
            event_type: Type of event
            data: Event data
        """
        for observer in self.observers:
            try:
                if asyncio.iscoroutinefunction(observer):
                    await observer(event_type, data)
                else:
                    observer(event_type, data)
            except Exception as e:
                print(f"[!] Observer error: {e}")

    # ==================== Original Methods (Enhanced) ====================

    def remove_agent(self, agent_name: str) -> bool:
        """Remove an agent from the system.

        Args:
            agent_name: Name of the agent to remove

        Returns:
            True if agent was removed, False if not found

        Example:
            >>> mind = AgentMind()
            >>> mind.add_agent(Agent(name="test", role="assistant"))
            >>> mind.remove_agent("test")
            True
        """
        for i, agent in enumerate(self.agents):
            if agent.name == agent_name:
                self.agents.pop(i)
                print(f"[-] Removed agent: {agent_name}")
                return True
        return False

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """Retrieve an agent by name.

        Args:
            agent_name: Name of the agent to find

        Returns:
            The agent if found, None otherwise

        Example:
            >>> mind = AgentMind()
            >>> mind.add_agent(Agent(name="test", role="assistant"))
            >>> agent = mind.get_agent("test")
            >>> print(agent.name)
            test
        """
        # Optimized: use next() with generator for early exit
        return next((agent for agent in self.agents if agent.name == agent_name), None)

    async def broadcast_message(
        self, message: Message, exclude_sender: bool = True, use_llm: bool = True
    ) -> List[Message]:
        """Broadcast a message to all agents and collect responses.

        Args:
            message: The message to broadcast
            exclude_sender: If True, don't send to the agent that sent the message
            use_llm: If True, use LLM-powered responses via think_and_respond

        Returns:
            List of response messages from agents

        Example:
            >>> mind = AgentMind()
            >>> mind.add_agent(Agent(name="agent1", role="analyst"))
            >>> msg = Message(content="Hello", sender="system")
            >>> responses = await mind.broadcast_message(msg)
        """
        responses: List[Message] = []
        self.conversation_history.append(message)

        # Create tasks for parallel processing
        tasks = []
        for agent in self.agents:
            if exclude_sender and agent.name == message.sender:
                continue

            # Use LLM-powered response if available and requested
            if use_llm and agent.llm_provider:
                tasks.append(agent.think_and_respond(message))
            else:
                tasks.append(agent.process_message(message))

        # Wait for all agents to respond
        agent_responses = await asyncio.gather(*tasks)

        # Collect non-None responses
        for response in agent_responses:
            if response:
                responses.append(response)
                self.conversation_history.append(response)

        return responses

    async def start_collaboration(
        self,
        initial_message: str,
        max_rounds: int = 10,
        stop_condition: Optional[Callable[[List[Message]], bool]] = None,
        use_llm: bool = True,
    ) -> CollaborationResult:
        """Start a multi-agent collaboration session.

        Args:
            initial_message: The initial task or question to discuss
            max_rounds: Maximum number of collaboration rounds
            stop_condition: Optional function to determine when to stop early.
                          Takes list of recent messages, returns True to stop.
            use_llm: If True, use LLM-powered intelligent responses

        Returns:
            CollaborationResult with success status and summary

        Example:
            >>> mind = AgentMind()
            >>> mind.add_agent(Agent(name="analyst", role="analyst"))
            >>> result = await mind.start_collaboration(
            ...     "Analyze this problem",
            ...     max_rounds=5
            ... )
            >>> print(result.success)
            True
        """
        if not self.agents:
            print("[!] No agents available, cannot start collaboration")
            return CollaborationResult(
                success=False,
                error="No agents available",
                total_rounds=0,
                total_messages=0,
            )

        start_time = datetime.now()
        self.metrics["total_collaborations"] += 1

        print(f"[*] Starting multi-agent collaboration: {initial_message}")
        print(f"[*] Strategy: {self.strategy.value}, LLM-powered: {use_llm}")
        self.is_running = True
        self._emit_event("collaboration_started", {"message": initial_message})

        # Create initial message
        init_msg = Message(
            content=initial_message,
            sender="system",
            role=MessageRole.SYSTEM,
        )

        # Track agent contributions
        agent_contributions: Dict[str, int] = {agent.name: 0 for agent in self.agents}

        try:
            if self.strategy == CollaborationStrategy.BROADCAST:
                # Broadcast strategy: all agents respond to initial message
                responses = await self.broadcast_message(
                    init_msg, exclude_sender=False, use_llm=use_llm
                )

                for response in responses:
                    agent_contributions[response.sender] = (
                        agent_contributions.get(response.sender, 0) + 1
                    )

                print(f"[>] Round 1: Received {len(responses)} responses")
                rounds_completed = 1

            elif self.strategy == CollaborationStrategy.ROUND_ROBIN:
                # Round-robin strategy: agents take turns
                responses = []
                rounds_completed = 0
                current_message = init_msg

                for round_num in range(min(max_rounds, len(self.agents))):
                    agent = self.agents[round_num % len(self.agents)]
                    if use_llm and agent.llm_provider:
                        response = await agent.think_and_respond(current_message)
                    else:
                        response = await agent.process_message(current_message)

                    if response:
                        responses.append(response)
                        self.conversation_history.append(response)
                        agent_contributions[response.sender] += 1
                        current_message = response

                    rounds_completed += 1
                    print(f"[>] Round {round_num + 1}: {agent.name} responded")

                    # Check stop condition
                    if stop_condition and stop_condition([response]):
                        print("[*] Stop condition met, ending collaboration")
                        break

            elif self.strategy == CollaborationStrategy.HIERARCHICAL:
                # Hierarchical strategy: supervisor coordinates sub-agents
                supervisor = None
                sub_agents = []

                for agent in self.agents:
                    if agent.role == "supervisor":
                        supervisor = agent
                    else:
                        sub_agents.append(agent)

                if not supervisor:
                    # Fall back to broadcast if no supervisor
                    responses = await self.broadcast_message(
                        init_msg, exclude_sender=False, use_llm=use_llm
                    )
                else:
                    # Supervisor delegates to sub-agents
                    responses = []
                    for agent in sub_agents:
                        if use_llm and agent.llm_provider:
                            response = await agent.think_and_respond(init_msg)
                        else:
                            response = await agent.process_message(init_msg)
                        if response:
                            responses.append(response)
                            self.conversation_history.append(response)
                            agent_contributions[response.sender] += 1

                    # Supervisor synthesizes
                    summary_msg = Message(
                        content=f"Synthesize these perspectives: {[r.content for r in responses]}",
                        sender="system",
                        role=MessageRole.SYSTEM,
                    )
                    if use_llm and supervisor.llm_provider:
                        supervisor_response = await supervisor.think_and_respond(summary_msg)
                    else:
                        supervisor_response = await supervisor.process_message(summary_msg)

                    if supervisor_response:
                        responses.append(supervisor_response)
                        self.conversation_history.append(supervisor_response)
                        agent_contributions[supervisor_response.sender] += 1

                rounds_completed = 1
                print(f"[>] Hierarchical collaboration: {len(responses)} responses")

            else:
                # Default to broadcast for other strategies
                responses = await self.broadcast_message(
                    init_msg, exclude_sender=False, use_llm=use_llm
                )
                rounds_completed = 1

            # Check stop condition
            if stop_condition and stop_condition(responses):
                print("[*] Stop condition met, ending collaboration")

            # Generate final output
            final_output = self._generate_final_output(responses)

            result = CollaborationResult(
                success=True,
                total_rounds=rounds_completed,
                total_messages=len(self.conversation_history),
                final_output=final_output,
                agent_contributions=agent_contributions,
            )

            # Update metrics
            self.metrics["successful_collaborations"] += 1
            duration = (datetime.now() - start_time).total_seconds()
            total_collab = self.metrics["total_collaborations"]
            current_avg = self.metrics["average_collaboration_time"]
            self.metrics["average_collaboration_time"] = (
                current_avg * (total_collab - 1) + duration
            ) / total_collab

            self.profile_performance("collaboration", duration)
            self._emit_event("collaboration_completed", {"success": True, "duration": duration})

            # Auto-checkpoint if enabled
            if self.enable_checkpointing:
                self.save_checkpoint()

            print("[*] Collaboration completed successfully")
            return result

        except Exception as e:
            print(f"[!] Collaboration failed: {str(e)}")
            self.metrics["failed_collaborations"] += 1
            self._emit_event("collaboration_failed", {"error": str(e)})

            return CollaborationResult(
                success=False,
                error=str(e),
                total_rounds=0,
                total_messages=len(self.conversation_history),
                agent_contributions=agent_contributions,
            )
        finally:
            self.is_running = False

    def _generate_final_output(self, responses: List[Message]) -> str:
        """Generate a final output summary from agent responses.

        Args:
            responses: List of agent responses

        Returns:
            Formatted summary string
        """
        if not responses:
            return "No responses generated"

        # Optimized: use list comprehension and join in one step
        output_lines = ["=== Collaboration Summary ==="] + [
            f"• {response.sender}: {response.content}" for response in responses
        ]
        return "\n".join(output_lines)

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation state.

        Returns:
            Dictionary with conversation statistics

        Example:
            >>> mind = AgentMind()
            >>> summary = mind.get_conversation_summary()
            >>> print(summary['total_messages'])
            0
        """
        return {
            "total_messages": len(self.conversation_history),
            "active_agents": len([a for a in self.agents if a.is_active]),
            "total_agents": len(self.agents),
            "recent_messages": [msg.content for msg in self.conversation_history[-5:]],
            "is_running": self.is_running,
        }

    def clear_history(self) -> None:
        """Clear the conversation history.

        This does not clear individual agent memories.
        """
        self.conversation_history.clear()
        print("[*] Conversation history cleared")

    def reset(self) -> None:
        """Reset the entire system, clearing all agents and history."""
        self.agents.clear()
        self.conversation_history.clear()
        self.is_running = False
        print("[*] AgentMind reset complete")

    def save_session(self, session_id: str, save_dir: str = ".agentmind_sessions") -> str:
        """Save the current session state to disk.

        Args:
            session_id: Unique identifier for this session
            save_dir: Directory to save session files (default: .agentmind_sessions)

        Returns:
            Path to the saved session file

        Example:
            >>> mind = AgentMind()
            >>> mind.add_agent(Agent(name="test", role="assistant"))
            >>> path = mind.save_session("my_session")
            >>> print(f"Session saved to {path}")
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        session_file = save_path / f"{session_id}.json"

        # Serialize session data
        session_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "strategy": self.strategy.value,
            "agents": [],
            "conversation_history": [],
        }

        # Serialize agents
        for agent in self.agents:
            agent_data = {
                "name": agent.name,
                "role": agent.role,
                "config": agent.config.model_dump(),
                "memory": [msg.model_dump(mode="json") for msg in agent.memory],
                "is_active": agent.is_active,
            }
            session_data["agents"].append(agent_data)

        # Serialize conversation history
        for msg in self.conversation_history:
            session_data["conversation_history"].append(msg.model_dump(mode="json"))

        # Write to file
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"[*] Session saved: {session_file}")
        return str(session_file)

    def load_session(self, session_id: str, save_dir: str = ".agentmind_sessions") -> bool:
        """Load a previously saved session from disk.

        Args:
            session_id: Unique identifier for the session to load
            save_dir: Directory where session files are stored

        Returns:
            True if session loaded successfully, False otherwise

        Example:
            >>> mind = AgentMind()
            >>> success = mind.load_session("my_session")
            >>> if success:
            ...     print("Session loaded successfully")
        """
        session_file = Path(save_dir) / f"{session_id}.json"

        if not session_file.exists():
            print(f"[!] Session file not found: {session_file}")
            return False

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Clear current state
            self.reset()

            # Restore strategy
            self.strategy = CollaborationStrategy(session_data["strategy"])

            # Restore agents
            for agent_data in session_data["agents"]:
                from .types import AgentConfig

                config = AgentConfig(**agent_data["config"])
                agent = Agent(
                    name=agent_data["name"],
                    role=agent_data["role"],
                    config=config,
                    llm_provider=self.llm_provider,
                )

                # Restore agent memory
                agent.memory = [Message(**msg_data) for msg_data in agent_data["memory"]]
                agent.is_active = agent_data["is_active"]

                self.agents.append(agent)

            # Restore conversation history
            self.conversation_history = [
                Message(**msg_data) for msg_data in session_data["conversation_history"]
            ]

            print(f"[*] Session loaded: {session_id}")
            print(f"    - Agents: {len(self.agents)}")
            print(f"    - Messages: {len(self.conversation_history)}")
            return True

        except Exception as e:
            print(f"[!] Failed to load session: {str(e)}")
            return False

    def list_sessions(self, save_dir: str = ".agentmind_sessions") -> List[Dict[str, Any]]:
        """List all saved sessions.

        Args:
            save_dir: Directory where session files are stored

        Returns:
            List of session info dictionaries

        Example:
            >>> mind = AgentMind()
            >>> sessions = mind.list_sessions()
            >>> for session in sessions:
            ...     print(f"{session['session_id']}: {session['timestamp']}")
        """
        save_path = Path(save_dir)
        if not save_path.exists():
            return []

        # Optimized: use list comprehension with inline error handling
        sessions = []
        for session_file in save_path.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append(
                        {
                            "session_id": data.get("session_id"),
                            "timestamp": data.get("timestamp"),
                            "num_agents": len(data.get("agents", [])),
                            "num_messages": len(data.get("conversation_history", [])),
                            "file_path": str(session_file),
                        }
                    )
            except Exception:
                continue

        # Optimized: use itemgetter for faster sorting
        from operator import itemgetter

        return sorted(sessions, key=itemgetter("timestamp"), reverse=True)

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return (
            f"AgentMind(agents={len(self.agents)}, "
            f"messages={len(self.conversation_history)}, "
            f"tasks={len(self.tasks)}, "
            f"running={self.is_running})"
        )

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"AgentMind with {len(self.agents)} agents"
