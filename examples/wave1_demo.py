"""Example demonstrating Wave 1 Core Architecture features.

This example showcases:
- EnhancedAgent with multi-modal support and sub-agents
- EnhancedAgentMind with state machine
- Advanced orchestration modes
- Hybrid memory backend
- Advanced tool system
- Plugin discovery
"""

import asyncio
from agentmind import Agent
from agentmind.core.enhanced_agent import EnhancedAgent, AgentState
from agentmind.core.enhanced_mind import EnhancedAgentMind, SystemState, TaskPriority
from agentmind.orchestration.advanced_modes import (
    create_orchestrator,
    OrchestrationMode,
    GraphOrchestrator,
)
from agentmind.memory.hybrid_backend import HybridMemoryBackend
from agentmind.tools.advanced import create_advanced_registry, ToolPermission
from agentmind.core.types import Message, MessageRole


async def demo_enhanced_agent():
    """Demonstrate EnhancedAgent features."""
    print("\n=== Enhanced Agent Demo ===\n")

    # Create enhanced agent with human-in-the-loop
    def human_approval(agent_name: str, message: Message) -> bool:
        print(f"[Human] Approve action from {agent_name}? (auto-approved)")
        return True

    agent = EnhancedAgent(
        name="manager",
        role="coordinator",
        human_in_loop=True,
        human_callback=human_approval,
    )

    # Add sub-agents
    analyst = Agent(name="analyst", role="analyst")
    executor = Agent(name="executor", role="executor")

    agent.add_sub_agent(analyst)
    agent.add_sub_agent(executor)

    print(f"Agent: {agent}")
    print(f"Sub-agents: {[a.name for a in agent.sub_agents]}")

    # Process message
    msg = Message(content="Analyze market trends", sender="user", role=MessageRole.USER)
    response = await agent.process_multimodal_message(msg)
    print(f"Response: {response.content}")

    # Delegate to sub-agent
    task = Message(content="Execute analysis", sender="manager", role=MessageRole.AGENT)
    result = await agent.delegate_to_sub_agent("analyst", task)
    print(f"Delegation result: {result.content if result else 'None'}")

    # Dynamic role switching
    agent.switch_role("supervisor")
    print(f"New role: {agent.role}")

    # Get execution summary
    summary = agent.get_execution_summary()
    print(f"Execution summary: {summary}")


async def demo_enhanced_mind():
    """Demonstrate EnhancedAgentMind with state machine."""
    print("\n=== Enhanced AgentMind Demo ===\n")

    # Create enhanced mind
    mind = EnhancedAgentMind(enable_state_machine=True)

    # Add agents
    mind.add_agent(Agent(name="planner", role="analyst"))
    mind.add_agent(Agent(name="executor", role="executor"))
    mind.add_agent(Agent(name="reviewer", role="critic"))

    print(f"System state: {mind.system_state.value}")

    # Add tasks with priorities
    mind.add_task(
        "task1",
        "Analyze requirements",
        priority=TaskPriority.HIGH,
        assigned_agents=["planner"],
    )

    mind.add_task(
        "task2",
        "Implement solution",
        priority=TaskPriority.MEDIUM,
        assigned_agents=["executor"],
        dependencies=["task1"],
    )

    mind.add_task(
        "task3",
        "Review implementation",
        priority=TaskPriority.HIGH,
        assigned_agents=["reviewer"],
        dependencies=["task2"],
    )

    print(f"Tasks queued: {len(mind.tasks)}")

    # Start collaboration with state machine
    result = await mind.start_collaboration_with_state_machine(
        "Build a recommendation system",
        max_rounds=3,
    )

    print(f"Success: {result.success}")
    print(f"State history: {[s['to'] for s in mind.state_history[-5:]]}")

    # Save checkpoint
    checkpoint_path = mind.save_checkpoint("demo_checkpoint")
    print(f"Checkpoint saved: {checkpoint_path}")

    # Get system status
    status = mind.get_system_status()
    print(f"System status: {status}")


async def demo_orchestration_modes():
    """Demonstrate advanced orchestration modes."""
    print("\n=== Advanced Orchestration Demo ===\n")

    # Create agents
    agents = [
        Agent(name="agent1", role="analyst"),
        Agent(name="agent2", role="creative"),
        Agent(name="agent3", role="critic"),
    ]

    # Sequential orchestration
    print("--- Sequential Mode ---")
    sequential = create_orchestrator(OrchestrationMode.SEQUENTIAL)
    result = await sequential.orchestrate(agents, "Analyze this problem")
    print(f"Result: {result.final_output}")

    # Hierarchical orchestration
    print("\n--- Hierarchical Mode ---")
    hierarchical = create_orchestrator(OrchestrationMode.HIERARCHICAL)
    result = await hierarchical.orchestrate(agents, "Design a solution")
    print(f"Result: {result.final_output}")

    # Debate orchestration
    print("\n--- Debate Mode ---")
    debate = create_orchestrator(OrchestrationMode.DEBATE)
    result = await debate.orchestrate(
        agents,
        "What's the best approach?",
        debate_rounds=2,
        voting_enabled=True,
    )
    print(f"Result: {result.final_output}")

    # Swarm orchestration
    print("\n--- Swarm Mode ---")
    swarm = create_orchestrator(OrchestrationMode.SWARM)
    result = await swarm.orchestrate(
        agents,
        "Complex task requiring multiple perspectives",
        max_agents=5,
    )
    print(f"Result: {result.final_output}")

    # Graph orchestration
    print("\n--- Graph Mode ---")
    graph = GraphOrchestrator()
    graph.add_node("start", agents[0])
    graph.add_node("middle", agents[1])
    graph.add_node("end", agents[2])
    graph.add_edge("start", "middle")
    graph.add_edge("middle", "end")

    result = await graph.orchestrate(agents, "Process through graph", start_node="start")
    print(f"Result: {result.final_output}")
    print(f"Graph visualization:\n{graph.visualize_graph()}")


async def demo_hybrid_memory():
    """Demonstrate hybrid memory backend."""
    print("\n=== Hybrid Memory Demo ===\n")

    # Create hybrid memory
    memory = HybridMemoryBackend(
        db_path=".demo_memory/hybrid.db",
        enable_vector=False,  # Disable for demo (requires chromadb)
        enable_compression=True,
    )

    # Add memories
    from agentmind.core.types import MemoryEntry

    entry1 = MemoryEntry(
        message=Message(
            content="Python is a programming language",
            sender="system",
            role=MessageRole.SYSTEM,
        ),
        importance=0.8,
    )

    entry2 = MemoryEntry(
        message=Message(
            content="Machine learning uses Python",
            sender="system",
            role=MessageRole.SYSTEM,
        ),
        importance=0.9,
    )

    await memory.add(entry1)
    await memory.add(entry2)

    # Add knowledge graph triple
    await memory.add_knowledge_triple(
        subject="Python",
        predicate="is_used_for",
        obj="Machine Learning",
        confidence=0.95,
    )

    # Query knowledge graph
    triples = await memory.query_knowledge_graph(subject="Python")
    print(f"Knowledge graph: {triples}")

    # Get recent memories
    recent = await memory.get_recent(limit=5)
    print(f"Recent memories: {len(recent)}")

    # Get statistics
    stats = memory.get_stats()
    print(f"Memory stats: {stats}")


async def demo_advanced_tools():
    """Demonstrate advanced tool system."""
    print("\n=== Advanced Tools Demo ===\n")

    # Create advanced registry with security
    registry = create_advanced_registry(
        allowed_permissions=[
            ToolPermission.READ,
            ToolPermission.EXECUTE,
        ],
        enable_docker=False,
    )

    # Register a simple tool
    from agentmind.tools.base import Tool, ToolResult

    class CalculatorTool(Tool):
        """Simple calculator tool."""

        async def execute(self, expression: str) -> ToolResult:
            try:
                result = eval(expression)
                return ToolResult(success=True, output=str(result))
            except Exception as e:
                return ToolResult(success=False, error=str(e))

    calculator = CalculatorTool()
    registry.register(calculator)

    # Execute tool
    result = await registry.execute("CalculatorTool", expression="2 + 2")
    print(f"Calculator result: {result.output}")

    # Get registry stats
    stats = registry.get_registry_stats()
    print(f"Registry stats: {stats}")


async def demo_plugin_discovery():
    """Demonstrate plugin discovery."""
    print("\n=== Plugin Discovery Demo ===\n")

    try:
        from agentmind import discover_plugins, list_plugins

        # Discover all plugins
        plugins = discover_plugins()
        print(f"Discovered plugins: {plugins}")

        # List installed plugins
        installed = list_plugins()
        print(f"Installed plugins: {len(installed)}")

    except ImportError:
        print("Plugin system not available (optional dependency)")


async def main():
    """Run all demos."""
    print("=" * 60)
    print("AgentMind Wave 1: Core Architecture Upgrade Demo")
    print("=" * 60)

    await demo_enhanced_agent()
    await demo_enhanced_mind()
    await demo_orchestration_modes()
    await demo_hybrid_memory()
    await demo_advanced_tools()
    await demo_plugin_discovery()

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
