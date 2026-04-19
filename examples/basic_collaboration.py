import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agentmind.core.agent import Agent, Message
from agentmind.core.mind import AgentMind

async def main():
    # Create AgentMind instance
    mind = AgentMind()

    # Create several agents
    alice = Agent("Alice", "analyst")
    bob = Agent("Bob", "creative")
    charlie = Agent("Charlie", "coordinator")

    # Add to AgentMind
    mind.add_agent(alice)
    mind.add_agent(bob)
    mind.add_agent(charlie)

    # Start collaboration
    await mind.start_collaboration("We need to come up with a name for a new product")

    # View collaboration summary
    summary = mind.get_conversation_summary()
    print(f"\n[Summary] Collaboration summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())
