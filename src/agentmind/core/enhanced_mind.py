"""Enhanced AgentMind with state machine and advanced orchestration.

This module extends AgentMind with:
- Global state machine (Planning → Execution → Reflection → Adaptation)
- Checkpoint/restore capabilities
- Parallel task scheduler
- Advanced orchestration modes
"""

from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from datetime import datetime
import asyncio
import json
from pathlib import Path

from .mind import AgentMind as BaseAgentMind
from .types import CollaborationResult, CollaborationStrategy
from ..llm.provider import LLMProvider


class SystemState(str, Enum):
    """Global system states."""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    ADAPTING = "adapting"
    PAUSED = "paused"
    ERROR = "error"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task:
    """Represents a task in the system."""

    def __init__(
        self,
        task_id: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_agents: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.description = description
        self.priority = priority
        self.assigned_agents = assigned_agents or []
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self.status = "pending"
        self.result: Optional[Any] = None
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None


class EnhancedAgentMind(BaseAgentMind):
    """Enhanced AgentMind with state machine and advanced features."""

    def __init__(
        self,
        strategy: CollaborationStrategy = CollaborationStrategy.BROADCAST,
        llm_provider: Optional[LLMProvider] = None,
        enable_state_machine: bool = True,
        checkpoint_dir: str = ".agentmind_checkpoints",
    ) -> None:
        """Initialize enhanced AgentMind.

        Args:
            strategy: Collaboration strategy
            llm_provider: LLM provider
            enable_state_machine: Enable state machine
            checkpoint_dir: Directory for checkpoints
        """
        super().__init__(strategy, llm_provider)

        self.enable_state_machine = enable_state_machine
        self.system_state = SystemState.IDLE
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Task management
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []

        # State machine history
        self.state_history: List[Dict[str, Any]] = []

        # Observers
        self.observers: List[Callable] = []

        print(f"[EnhancedAgentMind] Initialized with state machine: {enable_state_machine}")

    def transition_state(self, new_state: SystemState) -> None:
        """Transition to a new system state.

        Args:
            new_state: New state to transition to
        """
        if not self.enable_state_machine:
            return

        old_state = self.system_state
        self.system_state = new_state

        # Record transition
        transition = {
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.now().isoformat(),
        }
        self.state_history.append(transition)

        print(f"[State] {old_state.value} -> {new_state.value}")

        # Notify observers
        asyncio.create_task(self._notify_observers("state_change", transition))

    async def start_collaboration_with_state_machine(
        self,
        initial_message: str,
        max_rounds: int = 10,
        use_llm: bool = True,
    ) -> CollaborationResult:
        """Start collaboration with state machine.

        Args:
            initial_message: Initial task
            max_rounds: Maximum rounds
            use_llm: Use LLM

        Returns:
            Collaboration result
        """
        if not self.enable_state_machine:
            return await self.start_collaboration(initial_message, max_rounds, use_llm=use_llm)

        try:
            # Planning phase
            self.transition_state(SystemState.PLANNING)
            plan = await self._plan_collaboration(initial_message)

            # Execution phase
            self.transition_state(SystemState.EXECUTING)
            result = await self.start_collaboration(
                initial_message,
                max_rounds=max_rounds,
                use_llm=use_llm,
            )

            # Reflection phase
            self.transition_state(SystemState.REFLECTING)
            reflection = await self._reflect_on_result(result)

            # Adaptation phase
            self.transition_state(SystemState.ADAPTING)
            await self._adapt_based_on_reflection(reflection)

            # Return to idle
            self.transition_state(SystemState.IDLE)

            # Add state machine metadata to result
            result.metadata["state_machine"] = {
                "plan": plan,
                "reflection": reflection,
                "state_history": self.state_history[-4:],
            }

            return result

        except Exception as e:
            self.transition_state(SystemState.ERROR)
            print(f"[!] State machine error: {e}")
            self.transition_state(SystemState.IDLE)
            raise

    async def _plan_collaboration(self, task: str) -> Dict[str, Any]:
        """Plan the collaboration strategy.

        Args:
            task: Task description

        Returns:
            Plan dict
        """
        plan = {
            "task": task,
            "agents": [a.name for a in self.agents],
            "strategy": self.strategy.value,
            "estimated_rounds": min(len(self.agents), 5),
        }

        print(f"[Planning] Task: {task}")
        print(f"[Planning] Agents: {len(self.agents)}, Strategy: {self.strategy.value}")

        return plan

    async def _reflect_on_result(self, result: CollaborationResult) -> Dict[str, Any]:
        """Reflect on collaboration result.

        Args:
            result: Collaboration result

        Returns:
            Reflection dict
        """
        reflection = {
            "success": result.success,
            "total_messages": result.total_messages,
            "agent_participation": result.agent_contributions,
            "efficiency": result.total_messages / max(result.total_rounds, 1),
        }

        print(f"[Reflection] Success: {result.success}, Messages: {result.total_messages}")

        return reflection

    async def _adapt_based_on_reflection(self, reflection: Dict[str, Any]) -> None:
        """Adapt system based on reflection.

        Args:
            reflection: Reflection data
        """
        # Simple adaptation: adjust strategy if efficiency is low
        if reflection.get("efficiency", 0) > 5:
            print("[Adaptation] High message count, consider optimizing")

        # Could adjust agent parameters, strategy, etc.
        print("[Adaptation] System adapted based on reflection")

    def add_task(
        self,
        task_id: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_agents: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> Task:
        """Add a task to the queue.

        Args:
            task_id: Unique task ID
            description: Task description
            priority: Task priority
            assigned_agents: List of agent names
            dependencies: List of task IDs this depends on

        Returns:
            Created task
        """
        task = Task(
            task_id=task_id,
            description=description,
            priority=priority,
            assigned_agents=assigned_agents,
            dependencies=dependencies,
        )

        self.tasks[task_id] = task
        self.task_queue.append(task_id)

        # Sort queue by priority
        self.task_queue.sort(
            key=lambda tid: ["low", "medium", "high", "critical"].index(
                self.tasks[tid].priority.value
            ),
            reverse=True,
        )

        print(f"[Task] Added: {task_id} (priority: {priority.value})")
        return task

    async def execute_task_queue(self, max_parallel: int = 3) -> List[CollaborationResult]:
        """Execute tasks in the queue.

        Args:
            max_parallel: Maximum parallel tasks

        Returns:
            List of results
        """
        results = []

        while self.task_queue:
            # Get next batch of tasks
            batch = []
            for _ in range(min(max_parallel, len(self.task_queue))):
                if not self.task_queue:
                    break

                task_id = self.task_queue[0]
                task = self.tasks[task_id]

                # Check dependencies
                deps_met = all(
                    self.tasks[dep_id].status == "completed"
                    for dep_id in task.dependencies
                    if dep_id in self.tasks
                )

                if deps_met:
                    self.task_queue.pop(0)
                    batch.append(task)
                else:
                    # Move to end of queue
                    self.task_queue.append(self.task_queue.pop(0))

            if not batch:
                break

            # Execute batch in parallel
            batch_results = await asyncio.gather(
                *[self._execute_single_task(task) for task in batch]
            )

            results.extend(batch_results)

        return results

    async def _execute_single_task(self, task: Task) -> CollaborationResult:
        """Execute a single task.

        Args:
            task: Task to execute

        Returns:
            Collaboration result
        """
        print(f"[Task] Executing: {task.task_id}")
        task.status = "running"

        try:
            result = await self.start_collaboration_with_state_machine(
                task.description,
                max_rounds=10,
            )

            task.status = "completed"
            task.result = result
            task.completed_at = datetime.now()

            return result

        except Exception as e:
            task.status = "failed"
            print(f"[!] Task {task.task_id} failed: {e}")
            return CollaborationResult(
                success=False,
                error=str(e),
                total_rounds=0,
                total_messages=0,
            )

    def save_checkpoint(self, checkpoint_name: str) -> str:
        """Save system checkpoint.

        Args:
            checkpoint_name: Name for checkpoint

        Returns:
            Path to checkpoint file
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"

        checkpoint_data = {
            "checkpoint_name": checkpoint_name,
            "timestamp": datetime.now().isoformat(),
            "system_state": self.system_state.value,
            "strategy": self.strategy.value,
            "agents": [
                {
                    "name": agent.name,
                    "role": agent.role,
                    "config": agent.config.model_dump(),
                    "memory_size": len(agent.memory),
                }
                for agent in self.agents
            ],
            "tasks": {
                task_id: {
                    "task_id": task.task_id,
                    "description": task.description,
                    "priority": task.priority.value,
                    "status": task.status,
                    "assigned_agents": task.assigned_agents,
                }
                for task_id, task in self.tasks.items()
            },
            "state_history": self.state_history[-10:],
            "conversation_size": len(self.conversation_history),
        }

        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        print(f"[Checkpoint] Saved: {checkpoint_file}")
        return str(checkpoint_file)

    def restore_checkpoint(self, checkpoint_name: str) -> bool:
        """Restore from checkpoint.

        Args:
            checkpoint_name: Name of checkpoint

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

            # Restore state
            self.system_state = SystemState(checkpoint_data["system_state"])
            self.strategy = CollaborationStrategy(checkpoint_data["strategy"])

            print(f"[Checkpoint] Restored: {checkpoint_name}")
            print(f"  - State: {self.system_state.value}")
            print(f"  - Agents: {len(checkpoint_data['agents'])}")
            print(f"  - Tasks: {len(checkpoint_data['tasks'])}")

            return True

        except Exception as e:
            print(f"[!] Failed to restore checkpoint: {e}")
            return False

    def add_observer(self, observer: Callable) -> None:
        """Add an observer for system events.

        Args:
            observer: Observer callback
        """
        self.observers.append(observer)
        print("[Observer] Added observer")

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

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status.

        Returns:
            Status dict
        """
        return {
            "state": self.system_state.value,
            "agents": len(self.agents),
            "active_agents": len([a for a in self.agents if a.is_active]),
            "tasks": {
                "total": len(self.tasks),
                "pending": len([t for t in self.tasks.values() if t.status == "pending"]),
                "running": len([t for t in self.tasks.values() if t.status == "running"]),
                "completed": len([t for t in self.tasks.values() if t.status == "completed"]),
                "failed": len([t for t in self.tasks.values() if t.status == "failed"]),
            },
            "conversation_messages": len(self.conversation_history),
            "state_transitions": len(self.state_history),
            "observers": len(self.observers),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"EnhancedAgentMind(state={self.system_state.value}, "
            f"agents={len(self.agents)}, tasks={len(self.tasks)})"
        )
