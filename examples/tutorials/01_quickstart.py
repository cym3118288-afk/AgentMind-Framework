"""
Tutorial 01: Quickstart - Hello World Agent

This tutorial introduces the basics of AgentMind:
- Creating a simple agent
- Processing messages
- Basic agent - to - agent communication

Estimated time: 10 minutes
Difficulty: Beginner
"""

import asyncio
from agentmind import Agent, AgentMind, Message
from agentmind.llm import OllamaProvider


async def example_1_single_agent():
    """Example 1: Create and use a single agent"""
    print("\n=== Example 1: Single Agent ===\n")

    # Create an LLM provider (using Ollama with local models)
    llm = OllamaProvider(model="llama3.2:3b")

    # Create a simple agent
    agent = Agent(name="assistant", role="assistant", llm_provider=llm)

    # Create a message
    message = Message(content="Hello! Please introduce yourself.", sender="user", role="user")

    # Process the message
    response = await agent.process_message(message)
    print(f"Agent: {response.content}\n")


async def example_2_two_agents():
    """Example 2: Two agents communicating"""
    print("\n=== Example 2: Two Agents Communicating ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create two agents with different roles
    analyst = Agent(name="analyst", role="analyst", llm_provider=llm)

    creative = Agent(name="creative", role="creative", llm_provider=llm)

    # Analyst analyzes a problem
    problem = Message(
        content="We need to increase user engagement on our platform.", sender="user", role="user"
    )

    analysis = await analyst.process_message(problem)
    print(f"Analyst: {analysis.content}\n")

    # Creative responds to the analysis
    creative_prompt = Message(
        content=f"Based on this analysis: {analysis.content}\n\nProvide creative solutions.",
        sender="analyst",
        role="user",
    )

    solution = await creative.process_message(creative_prompt)
    print(f"Creative: {solution.content}\n")


async def example_3_agentmind_orchestration():
    """Example 3: Using AgentMind for orchestration"""
    print("\n=== Example 3: AgentMind Orchestration ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create agents
    analyst = Agent(name="analyst", role="analyst", llm_provider=llm)
    creative = Agent(name="creative", role="creative", llm_provider=llm)
    coordinator = Agent(name="coordinator", role="coordinator", llm_provider=llm)

    # Create AgentMind orchestrator
    mind = AgentMind(strategy="round_robin")
    mind.add_agent(analyst)
    mind.add_agent(creative)
    mind.add_agent(coordinator)

    # Start collaboration
    result = await mind.start_collaboration(
        "How can we improve our mobile app's user experience?", max_rounds=3
    )

    print(f"Final Result:\n{result.final_output}\n")
    print(f"Total rounds: {len(result.conversation_history)}")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("AgentMind Tutorial 01: Quickstart")
    print("=" * 60)

    # Run examples
    await example_1_single_agent()
    await example_2_two_agents()
    await example_3_agentmind_orchestration()

    print("\n" + "=" * 60)
    print("Tutorial Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. Agents are created with a name, role, and LLM provider")
    print("2. Messages are processed using agent.process_message()")
    print("3. AgentMind orchestrates multi - agent collaboration")
    print("\nNext: Tutorial 02 - Memory Systems")


if __name__ == "__main__":
    asyncio.run(main())
