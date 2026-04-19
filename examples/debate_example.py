import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agentmind.core.agent import Agent, Message
from agentmind.core.mind import AgentMind

async def debate_example():
    """
    Example: Multiple agents debate a topic
    """
    print("=" * 60)
    print("Multi-Agent Debate Example")
    print("=" * 60)

    # Create AgentMind instance
    mind = AgentMind()

    # Create agents with different perspectives
    optimist = Agent("Optimist", "creative")
    pessimist = Agent("Pessimist", "analyst")
    moderator = Agent("Moderator", "coordinator")

    # Add agents
    mind.add_agent(optimist)
    mind.add_agent(pessimist)
    mind.add_agent(moderator)

    # Start debate
    topic = "Should we invest in AI technology?"
    await mind.start_collaboration(topic)

    # Get summary
    summary = mind.get_conversation_summary()
    print(f"\n[Summary]")
    print(f"  Total messages: {summary['total_messages']}")
    print(f"  Active agents: {summary['active_agents']}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(debate_example())
