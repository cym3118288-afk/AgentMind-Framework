"""Multi-agent debate example with LLM-powered intelligence.

This example demonstrates how agents with different perspectives can debate
a topic and reach conclusions through collaboration using real LLM reasoning.

Difficulty: BEGINNER
Prerequisites: Optional - Ollama installed with llama3.2 model for LLM responses
Estimated time: 10 minutes

What you'll learn:
- Configuring LLM providers (Ollama or LiteLLM)
- Creating agents with contrasting perspectives
- Running multi-round debates
- Analyzing debate outcomes and statistics

Expected Output:
- Optimist presents positive perspectives on AI investment
- Pessimist provides critical analysis and risk assessment
- Moderator synthesizes viewpoints and facilitates discussion
- Final summary includes balanced conclusion from all perspectives
- Works with or without LLM (falls back to template responses)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentmind import Agent, AgentMind, AgentRole
from agentmind.llm import OllamaProvider, LiteLLMProvider


async def debate_example() -> None:
    """Run a debate between agents with different perspectives."""
    print("=" * 60)
    print("AgentMind - Multi-Agent Debate Example")
    print("=" * 60)

    # Configure LLM provider
    # Option 1: Use Ollama for local inference (requires Ollama running)
    # provider = OllamaProvider(model="llama3.2", temperature=0.8)

    # Option 2: Use LiteLLM for cloud models (requires API key)
    # Uncomment and set your API key:
    # os.environ["OPENAI_API_KEY"] = "your-key-here"
    # provider = LiteLLMProvider(model="gpt-3.5-turbo", temperature=0.8)

    # For this demo, we'll try Ollama first, fall back to template mode
    try:
        provider = OllamaProvider(model="llama3.2", temperature=0.8)
        # Test if Ollama is available
        if not await provider.check_model_available():
            print("[!] Ollama not available, using template-based responses")
            provider = None
    except Exception as e:
        print(f"[!] Could not connect to Ollama: {e}")
        print("[!] Using template-based responses")
        provider = None

    # Create AgentMind instance with LLM provider
    mind = AgentMind(llm_provider=provider)

    # Create agents with different perspectives
    optimist = Agent(name="Optimist", role=AgentRole.CREATIVE.value, llm_provider=provider)

    pessimist = Agent(name="Pessimist", role=AgentRole.CRITIC.value, llm_provider=provider)

    moderator = Agent(name="Moderator", role=AgentRole.COORDINATOR.value, llm_provider=provider)

    # Add agents to the mind
    mind.add_agent(optimist)
    mind.add_agent(pessimist)
    mind.add_agent(moderator)

    print(f"\n[+] Created debate team with {len(mind.agents)} agents")
    print(f"  - {optimist.name} ({optimist.role}) - Will present positive perspectives")
    print(f"  - {pessimist.name} ({pessimist.role}) - Will present critical analysis")
    print(f"  - {moderator.name} ({moderator.role}) - Will coordinate the discussion")

    if provider:
        print(f"\n[*] Using LLM: {provider.model}")
    else:
        print("\n[*] Using template-based responses (no LLM)")

    # Start debate
    print("\n" + "=" * 60)
    print("Starting Debate")
    print("=" * 60)

    topic = "Should our company invest heavily in AI technology for the next year?"
    print(f"\nTopic: {topic}\n")

    result = await mind.start_collaboration(topic, max_rounds=3, use_llm=provider is not None)

    # Display results
    print("\n" + "=" * 60)
    print("Debate Results")
    print("=" * 60)

    print(f"\nSuccess: {result.success}")
    print(f"Total Rounds: {result.total_rounds}")
    print(f"Total Messages: {result.total_messages}")

    print("\nParticipant Contributions:")
    for agent_name, count in result.agent_contributions.items():
        print(f"  - {agent_name}: {count} messages")

    print("\n" + "=" * 60)
    print("Debate Summary")
    print("=" * 60)
    print(f"\n{result.final_output}")

    # Get conversation summary
    summary = mind.get_conversation_summary()
    print("\n" + "=" * 60)
    print("Conversation Statistics")
    print("=" * 60)
    print(f"Total messages exchanged: {summary['total_messages']}")
    print(f"Active agents: {summary['active_agents']}/{summary['total_agents']}")

    # Show recent messages
    if summary["recent_messages"]:
        print("\nRecent messages:")
        for msg in summary["recent_messages"][-3:]:
            preview = msg[:100] + "..." if len(msg) > 100 else msg
            print(f"  • {preview}")

    print("\n" + "=" * 60)
    print("Debate Complete!")
    print("=" * 60)

    # Cleanup
    if provider and hasattr(provider, "close"):
        await provider.close()


if __name__ == "__main__":
    asyncio.run(debate_example())
