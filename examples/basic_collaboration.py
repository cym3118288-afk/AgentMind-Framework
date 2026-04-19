"""Basic multi-agent collaboration example.

This example demonstrates how to create multiple agents with different roles
and have them collaborate on a task.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentmind import Agent, AgentMind, AgentRole


async def main() -> None:
    """Run a basic collaboration between multiple agents."""
    print("=" * 60)
    print("AgentMind - Basic Collaboration Example")
    print("=" * 60)

    # Create AgentMind instance
    mind = AgentMind()

    # Create agents with different roles
    alice = Agent(name="Alice", role=AgentRole.ANALYST.value)
    bob = Agent(name="Bob", role=AgentRole.CREATIVE.value)
    charlie = Agent(name="Charlie", role=AgentRole.COORDINATOR.value)

    # Add agents to the mind
    mind.add_agent(alice)
    mind.add_agent(bob)
    mind.add_agent(charlie)

    print(f"\n[+] Created {len(mind.agents)} agents")
    print(f"  - {alice.name} ({alice.role})")
    print(f"  - {bob.name} ({bob.role})")
    print(f"  - {charlie.name} ({charlie.role})")

    # Start collaboration
    print("\n" + "=" * 60)
    print("Starting Collaboration")
    print("=" * 60)

    task = "We need to come up with a name for a new AI-powered productivity app"
    result = await mind.start_collaboration(task)

    # Display results
    print("\n" + "=" * 60)
    print("Collaboration Results")
    print("=" * 60)

    print(f"\nSuccess: {result.success}")
    print(f"Total Rounds: {result.total_rounds}")
    print(f"Total Messages: {result.total_messages}")

    print("\nAgent Contributions:")
    for agent_name, count in result.agent_contributions.items():
        print(f"  - {agent_name}: {count} messages")

    print("\n" + "=" * 60)
    print("Final Output")
    print("=" * 60)
    print(f"\n{result.final_output}")

    # View conversation summary
    summary = mind.get_conversation_summary()
    print("\n" + "=" * 60)
    print("Conversation Summary")
    print("=" * 60)
    print(f"Total messages: {summary['total_messages']}")
    print(f"Active agents: {summary['active_agents']}/{summary['total_agents']}")


if __name__ == "__main__":
    asyncio.run(main())
