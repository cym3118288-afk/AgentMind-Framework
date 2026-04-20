"""Basic multi - agent collaboration example.

This example demonstrates how to create multiple agents with different roles
and have them collaborate on a task.

Difficulty: BEGINNER
Prerequisites: None
Estimated time: 5 minutes

What you'll learn:
- Creating agents with different roles
- Adding agents to AgentMind
- Starting a basic collaboration
- Viewing collaboration results

Expected Output:
- Agents will discuss and propose names for an AI productivity app
- Each agent contributes based on their role (analyst, creative, coordinator)
- Final output includes consensus on app name suggestions
- Statistics show agent participation and message counts
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from agentmind import Agent, AgentMind, AgentRole  # noqa: E402


async def main() -> None:
    """Run a basic collaboration between multiple agents.

    This function demonstrates the core workflow:
    1. Create AgentMind instance
    2. Create agents with specific roles
    3. Add agents to the mind
    4. Start collaboration with a task
    5. Review results and statistics
    """
    print("=" * 60)
    print("AgentMind - Basic Collaboration Example")
    print("=" * 60)

    # Step 1: Create AgentMind instance
    # This is the central coordinator for all agent interactions
    mind = AgentMind()

    # Step 2: Create agents with different roles
    # Each role brings unique perspectives to the collaboration
    # ANALYST: Focuses on data - driven insights and logical analysis
    alice = Agent(name="Alice", role=AgentRole.ANALYST.value)

    # CREATIVE: Generates innovative ideas and creative solutions
    bob = Agent(name="Bob", role=AgentRole.CREATIVE.value)

    # COORDINATOR: Facilitates discussion and synthesizes viewpoints
    charlie = Agent(name="Charlie", role=AgentRole.COORDINATOR.value)

    # Step 3: Add agents to the mind
    # This registers them for participation in collaborations
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

    # Step 4: Define the task and start collaboration
    # The agents will discuss and work together to complete this task
    task = "We need to come up with a name for a new AI - powered productivity app"
    result = await mind.start_collaboration(task)

    # Step 5: Display results
    # The result object contains comprehensive information about the collaboration
    print("\n" + "=" * 60)
    print("Collaboration Results")
    print("=" * 60)

    # Success indicates if the collaboration completed without errors
    print(f"\nSuccess: {result.success}")
    # Total rounds shows how many discussion cycles occurred
    print(f"Total Rounds: {result.total_rounds}")
    # Total messages counts all communications between agents
    print(f"Total Messages: {result.total_messages}")

    # Agent contributions show participation levels
    print("\nAgent Contributions:")
    for agent_name, count in result.agent_contributions.items():
        print(f"  - {agent_name}: {count} messages")

    print("\n" + "=" * 60)
    print("Final Output")
    print("=" * 60)
    # The final output is the synthesized result of the collaboration
    print(f"\n{result.final_output}")

    # View conversation summary for additional insights
    summary = mind.get_conversation_summary()
    print("\n" + "=" * 60)
    print("Conversation Summary")
    print("=" * 60)
    print(f"Total messages: {summary['total_messages']}")
    print(f"Active agents: {summary['active_agents']}/{summary['total_agents']}")


if __name__ == "__main__":
    asyncio.run(main())
