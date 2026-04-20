"""Advanced debate example with hierarchical orchestration.

This example demonstrates hierarchical collaboration where a supervisor
coordinates multiple specialized agents to reach a consensus.

Difficulty: INTERMEDIATE
Prerequisites: Understanding of basic collaboration patterns
Estimated time: 15 minutes

What you'll learn:
- Implementing hierarchical collaboration strategies
- Creating supervisor - subordinate agent relationships
- Coordinating specialized agents for decision - making
- Using different collaboration strategies

Expected Output:
- Supervisor (CEO) coordinates the decision - making process
- DataAnalyst provides quantitative insights
- MarketResearcher offers market intelligence
- RiskManager identifies potential risks
- Final decision synthesizes all expert inputs
- Demonstrates hierarchical message flow and coordination
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from agentmind import Agent, AgentMind, AgentRole, CollaborationStrategy
from agentmind.llm import OllamaProvider


async def hierarchical_debate() -> None:
    """Run a hierarchical debate with supervisor coordination."""
    print("=" * 60)
    print("AgentMind - Hierarchical Debate Example")
    print("=" * 60)

    # Try to use Ollama, fall back to template mode
    try:
        provider = OllamaProvider(model="llama3.2", temperature=0.7)
        if not await provider.check_model_available():
            print("[!] Ollama not available, using template - based responses")
            provider = None
    except Exception:
        print("[!] Using template - based responses")
        provider = None

    # Create AgentMind with hierarchical strategy
    mind = AgentMind(strategy=CollaborationStrategy.HIERARCHICAL, llm_provider=provider)

    # Create supervisor
    supervisor = Agent(name="CEO", role=AgentRole.SUPERVISOR.value, llm_provider=provider)

    # Create specialized sub - agents
    analyst = Agent(name="DataAnalyst", role=AgentRole.ANALYST.value, llm_provider=provider)

    researcher = Agent(
        name="MarketResearcher", role=AgentRole.RESEARCHER.value, llm_provider=provider
    )

    critic = Agent(name="RiskManager", role=AgentRole.CRITIC.value, llm_provider=provider)

    # Add agents (supervisor first)
    mind.add_agent(supervisor)
    mind.add_agent(analyst)
    mind.add_agent(researcher)
    mind.add_agent(critic)

    print(f"\n[+] Created hierarchical team with {len(mind.agents)} agents")
    print(f"  - {supervisor.name} (Supervisor) - Coordinates and synthesizes")
    print(f"  - {analyst.name} (Analyst) - Provides data analysis")
    print(f"  - {researcher.name} (Researcher) - Provides market research")
    print(f"  - {critic.name} (Critic) - Identifies risks")

    # Start collaboration
    print("\n" + "=" * 60)
    print("Starting Hierarchical Collaboration")
    print("=" * 60)

    topic = "Should we launch a new product line in Q3?"
    print(f"\nDecision: {topic}\n")

    result = await mind.start_collaboration(topic, max_rounds=5, use_llm=provider is not None)

    # Display results
    print("\n" + "=" * 60)
    print("Collaboration Results")
    print("=" * 60)

    print(f"\nSuccess: {result.success}")
    print(f"Strategy: {mind.strategy.value}")
    print(f"Total Rounds: {result.total_rounds}")
    print(f"Total Messages: {result.total_messages}")

    print("\nAgent Contributions:")
    for agent_name, count in result.agent_contributions.items():
        print(f"  - {agent_name}: {count} messages")

    print("\n" + "=" * 60)
    print("Final Decision")
    print("=" * 60)
    print(f"\n{result.final_output}")

    print("\n" + "=" * 60)
    print("Collaboration Complete!")
    print("=" * 60)

    # Cleanup
    if provider and hasattr(provider, "close"):
        await provider.close()


if __name__ == "__main__":
    asyncio.run(hierarchical_debate())
