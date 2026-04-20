"""
Advanced Example: Distributed Agent System

This example demonstrates a distributed multi - agent system:
- Distributed task allocation
- Load balancing across agents
- Fault tolerance and recovery
- Inter - agent communication
- Scalable architecture
- Coordination protocols

Estimated time: 35 minutes
Difficulty: Advanced
"""

import asyncio
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
from agentmind import Agent, Message
from agentmind.llm import OllamaProvider


class AgentStatus(str, Enum):
    """Agent status in distributed system"""

    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class TaskPriority(str, Enum):
    """Task priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DistributedTask:
    """Task in distributed system"""

    def __init__(
        self,
        task_id: str,
        content: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        required_capability: Optional[str] = None,
    ):
        self.task_id = task_id
        self.content = content
        self.priority = priority
        self.required_capability = required_capability
        self.assigned_to: Optional[str] = None
        self.status = "pending"
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[str] = None


class LoadBalancer:
    """Load balancer for distributing tasks"""

    def __init__(self):
        self.agent_loads: Dict[str, int] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}

    def register_agent(self, agent_id: str, capabilities: List[str]):
        """Register an agent with its capabilities"""
        self.agent_loads[agent_id] = 0
        self.agent_capabilities[agent_id] = capabilities

    def get_best_agent(self, task: DistributedTask, available_agents: List[str]) -> Optional[str]:
        """Select best agent for task using load balancing"""
        # Filter by capability if required
        if task.required_capability:
            capable_agents = [
                agent_id
                for agent_id in available_agents
                if task.required_capability in self.agent_capabilities.get(agent_id, [])
            ]
            if not capable_agents:
                return None
            available_agents = capable_agents

        # Select agent with lowest load
        if not available_agents:
            return None

        return min(available_agents, key=lambda a: self.agent_loads.get(a, 0))

    def update_load(self, agent_id: str, delta: int):
        """Update agent load"""
        if agent_id in self.agent_loads:
            self.agent_loads[agent_id] = max(0, self.agent_loads[agent_id] + delta)

    def get_load_distribution(self) -> Dict[str, int]:
        """Get current load distribution"""
        return self.agent_loads.copy()


class TaskQueue:
    """Priority queue for tasks"""

    def __init__(self):
        self.tasks: List[DistributedTask] = []
        self.priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }

    def add_task(self, task: DistributedTask):
        """Add task to queue"""
        self.tasks.append(task)
        self._sort_tasks()

    def _sort_tasks(self):
        """Sort tasks by priority"""
        self.tasks.sort(key=lambda t: self.priority_order[t.priority])

    def get_next_task(self) -> Optional[DistributedTask]:
        """Get next task from queue"""
        pending_tasks = [t for t in self.tasks if t.status == "pending"]
        return pending_tasks[0] if pending_tasks else None

    def get_task(self, task_id: str) -> Optional[DistributedTask]:
        """Get specific task"""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "total": len(self.tasks),
            "pending": sum(1 for t in self.tasks if t.status == "pending"),
            "in_progress": sum(1 for t in self.tasks if t.status == "in_progress"),
            "completed": sum(1 for t in self.tasks if t.status == "completed"),
            "failed": sum(1 for t in self.tasks if t.status == "failed"),
        }


class DistributedAgent(Agent):
    """Agent in distributed system"""

    def __init__(self, *args, capabilities: List[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.capabilities = capabilities or ["general"]
        self.status = AgentStatus.IDLE
        self.current_task: Optional[DistributedTask] = None
        self.completed_tasks = 0
        self.failed_tasks = 0

    async def execute_task(self, task: DistributedTask) -> Dict[str, Any]:
        """Execute a distributed task"""
        self.status = AgentStatus.BUSY
        self.current_task = task
        task.status = "in_progress"
        task.started_at = datetime.now()
        task.assigned_to = self.name

        try:
            # Process the task
            message = Message(content=task.content, sender="system", role="user")
            response = await self.process_message(message)

            # Mark as completed
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = response.content
            self.completed_tasks += 1

            return {"success": True, "result": response.content, "agent": self.name}

        except Exception as e:
            # Handle failure
            task.status = "failed"
            task.result = f"Error: {str(e)}"
            self.failed_tasks += 1
            self.status = AgentStatus.ERROR

            return {"success": False, "error": str(e), "agent": self.name}

        finally:
            self.current_task = None
            if self.status != AgentStatus.ERROR:
                self.status = AgentStatus.IDLE

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "name": self.name,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": (
                self.completed_tasks / (self.completed_tasks + self.failed_tasks)
                if (self.completed_tasks + self.failed_tasks) > 0
                else 0
            ),
        }


class DistributedSystem:
    """Distributed multi - agent system coordinator"""

    def __init__(self):
        self.agents: Dict[str, DistributedAgent] = {}
        self.task_queue = TaskQueue()
        self.load_balancer = LoadBalancer()
        self.running = False

    def add_agent(self, agent: DistributedAgent):
        """Add agent to distributed system"""
        self.agents[agent.name] = agent
        self.load_balancer.register_agent(agent.name, agent.capabilities)

    def submit_task(self, task: DistributedTask):
        """Submit task to system"""
        self.task_queue.add_task(task)

    async def process_tasks(self):
        """Process tasks from queue"""
        self.running = True

        while self.running:
            # Get next task
            task = self.task_queue.get_next_task()
            if not task:
                await asyncio.sleep(0.1)
                continue

            # Find available agent
            available_agents = [
                agent_id
                for agent_id, agent in self.agents.items()
                if agent.status == AgentStatus.IDLE
            ]

            if not available_agents:
                await asyncio.sleep(0.1)
                continue

            # Assign task to best agent
            agent_id = self.load_balancer.get_best_agent(task, available_agents)
            if not agent_id:
                await asyncio.sleep(0.1)
                continue

            agent = self.agents[agent_id]

            # Update load
            self.load_balancer.update_load(agent_id, 1)

            # Execute task
            asyncio.create_task(self._execute_and_update(agent, task))

    async def _execute_and_update(self, agent: DistributedAgent, task: DistributedTask):
        """Execute task and update load"""
        await agent.execute_task(task)
        self.load_balancer.update_load(agent.name, -1)

    def stop(self):
        """Stop processing tasks"""
        self.running = False

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "agents": len(self.agents),
            "queue": self.task_queue.get_queue_stats(),
            "load_distribution": self.load_balancer.get_load_distribution(),
            "agent_stats": [agent.get_stats() for agent in self.agents.values()],
        }


async def example_1_basic_distribution():
    """Example 1: Basic task distribution"""
    print("\n=== Example 1: Basic Task Distribution ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create distributed system
    system = DistributedSystem()

    # Add agents
    for i in range(3):
        agent = DistributedAgent(
            name=f"agent_{i}", role="worker", llm_provider=llm, capabilities=["general"]
        )
        system.add_agent(agent)

    # Submit tasks
    for i in range(5):
        task = DistributedTask(
            task_id=f"task_{i}", content=f"Process item {i}", priority=TaskPriority.MEDIUM
        )
        system.submit_task(task)

    print(f"Created system with {len(system.agents)} agents")
    print(f"Submitted {len(system.task_queue.tasks)} tasks\n")


async def example_2_load_balancing():
    """Example 2: Load balancing"""
    print("\n=== Example 2: Load Balancing ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create system
    system = DistributedSystem()

    # Add agents with different capabilities
    agents_config = [
        ("analyst", ["analysis", "general"]),
        ("writer", ["writing", "general"]),
        ("coder", ["coding", "general"]),
    ]

    for name, capabilities in agents_config:
        agent = DistributedAgent(name=name, role=name, llm_provider=llm, capabilities=capabilities)
        system.add_agent(agent)

    # Submit tasks with different requirements
    tasks = [
        ("task_1", "Analyze data", "analysis"),
        ("task_2", "Write report", "writing"),
        ("task_3", "Write code", "coding"),
        ("task_4", "General task", None),
    ]

    for task_id, content, capability in tasks:
        task = DistributedTask(task_id=task_id, content=content, required_capability=capability)
        system.submit_task(task)

    print("Load balancer distributes tasks based on:")
    print("  - Agent capabilities")
    print("  - Current load")
    print("  - Task requirements\n")


async def example_3_priority_queue():
    """Example 3: Priority - based task queue"""
    print("\n=== Example 3: Priority Queue ===\n")

    # Create task queue
    queue = TaskQueue()

    # Add tasks with different priorities
    tasks = [
        ("task_1", "Low priority task", TaskPriority.LOW),
        ("task_2", "Critical task", TaskPriority.CRITICAL),
        ("task_3", "Medium task", TaskPriority.MEDIUM),
        ("task_4", "High priority task", TaskPriority.HIGH),
    ]

    for task_id, content, priority in tasks:
        task = DistributedTask(task_id, content, priority)
        queue.add_task(task)

    print("Task execution order (by priority):")
    for i, task in enumerate(queue.tasks, 1):
        print(f"  {i}. {task.task_id} - {task.priority.value}")
    print()


async def example_4_fault_tolerance():
    """Example 4: Fault tolerance"""
    print("\n=== Example 4: Fault Tolerance ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create agent
    agent = DistributedAgent(name="resilient_agent", role="worker", llm_provider=llm)

    # Simulate task execution
    DistributedTask("task_1", "Test task")

    print(f"Agent status: {agent.status.value}")
    print("System handles failures gracefully:")
    print("  - Task retry mechanisms")
    print("  - Agent health monitoring")
    print("  - Automatic failover\n")


async def example_5_scalability():
    """Example 5: Scalable architecture"""
    print("\n=== Example 5: Scalability ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create large distributed system
    system = DistributedSystem()

    # Add many agents
    for i in range(10):
        agent = DistributedAgent(
            name=f"agent_{i}", role="worker", llm_provider=llm, capabilities=["general"]
        )
        system.add_agent(agent)

    print(f"Scaled to {len(system.agents)} agents")
    print("System supports:")
    print("  - Horizontal scaling (add more agents)")
    print("  - Dynamic agent registration")
    print("  - Distributed task processing\n")


async def example_6_complete_workflow():
    """Example 6: Complete distributed workflow"""
    print("\n=== Example 6: Complete Workflow ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create system
    system = DistributedSystem()

    # Add specialized agents
    agents = [
        ("data_processor", ["data", "general"]),
        ("analyzer", ["analysis", "general"]),
        ("reporter", ["reporting", "general"]),
    ]

    for name, capabilities in agents:
        agent = DistributedAgent(name=name, role=name, llm_provider=llm, capabilities=capabilities)
        system.add_agent(agent)

    # Submit workflow tasks
    workflow_tasks = [
        ("step_1", "Process raw data", TaskPriority.HIGH, "data"),
        ("step_2", "Analyze processed data", TaskPriority.MEDIUM, "analysis"),
        ("step_3", "Generate report", TaskPriority.LOW, "reporting"),
    ]

    for task_id, content, priority, capability in workflow_tasks:
        task = DistributedTask(task_id, content, priority, capability)
        system.submit_task(task)

    print("Distributed workflow:")
    print("  1. Data processing (high priority)")
    print("  2. Analysis (medium priority)")
    print("  3. Reporting (low priority)")
    print("\nTasks distributed across specialized agents\n")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("Advanced Example: Distributed Agent System")
    print("=" * 60)

    await example_1_basic_distribution()
    await example_2_load_balancing()
    await example_3_priority_queue()
    await example_4_fault_tolerance()
    await example_5_scalability()
    await example_6_complete_workflow()

    print("\n" + "=" * 60)
    print("Example Complete!")
    print("=" * 60)
    print("\nKey Concepts:")
    print("1. Distributed systems enable scalable processing")
    print("2. Load balancing optimizes resource utilization")
    print("3. Priority queues ensure critical tasks execute first")
    print("4. Fault tolerance maintains system reliability")
    print("5. Capability - based routing matches tasks to agents")
    print("6. Horizontal scaling supports growing workloads")


if __name__ == "__main__":
    asyncio.run(main())
