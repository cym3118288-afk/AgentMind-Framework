"""
Tutorial 02: Memory Systems

This tutorial covers AgentMind's memory capabilities:
- Short - term memory (conversation history)
- Long - term memory (persistent storage)
- Memory retrieval and context
- Memory management strategies

Estimated time: 15 minutes
Difficulty: Beginner
"""

import asyncio
from agentmind import Agent, AgentMind, Message
from agentmind.llm import OllamaProvider


async def example_1_short_term_memory():
    """Example 1: Agent with short - term memory"""
    print("\n=== Example 1: Short - term Memory ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = Agent(name="assistant", role="assistant", llm_provider=llm)

    # First interaction
    msg1 = Message(content="My name is Alice.", sender="user", role="user")
    response1 = await agent.process_message(msg1)
    print("User: My name is Alice.")
    print(f"Agent: {response1.content}\n")

    # Second interaction - agent should remember
    msg2 = Message(content="What's my name?", sender="user", role="user")
    response2 = await agent.process_message(msg2)
    print("User: What's my name?")
    print(f"Agent: {response2.content}\n")

    # Check memory
    print(f"Memory size: {len(agent.memory)} messages")


async def example_2_memory_context():
    """Example 2: Using memory for context"""
    print("\n=== Example 2: Memory Context ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = Agent(name="analyst", role="analyst", llm_provider=llm)

    # Build context over multiple messages
    messages = [
        "Our Q1 revenue was $1M.",
        "Q2 revenue increased to $1.5M.",
        "Q3 revenue reached $2M.",
        "What's the revenue growth trend?",
    ]

    for msg_content in messages:
        msg = Message(content=msg_content, sender="user", role="user")
        response = await agent.process_message(msg)
        print(f"User: {msg_content}")
        if msg_content == messages[-1]:
            print(f"Agent: {response.content}\n")

    print(f"Agent used {len(agent.memory)} messages for context")


async def example_3_memory_management():
    """Example 3: Managing memory size"""
    print("\n=== Example 3: Memory Management ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Agent with memory limit
    agent = Agent(
        name="assistant",
        role="assistant",
        llm_provider=llm,
        config={"max_memory_size": 5},  # Keep only last 5 messages
    )

    # Add many messages
    for i in range(10):
        msg = Message(content=f"Message number {i + 1}", sender="user", role="user")
        await agent.process_message(msg)

    print(f"Sent 10 messages, memory contains: {len(agent.memory)} messages")
    print("Memory management keeps only recent context\n")


async def example_4_shared_memory():
    """Example 4: Agents with shared context"""
    print("\n=== Example 4: Shared Memory Context ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create agents
    researcher = Agent(name="researcher", role="researcher", llm_provider=llm)
    writer = Agent(name="writer", role="writer", llm_provider=llm)

    # Researcher gathers information
    research_msg = Message(
        content="Research the benefits of renewable energy.", sender="user", role="user"
    )
    research_result = await researcher.process_message(research_msg)
    print(f"Researcher: {research_result.content[:200]}...\n")

    # Writer uses researcher's findings
    write_msg = Message(
        content=f"Based on this research: {research_result.content}\n\nWrite a brief summary.",
        sender="researcher",
        role="user",
    )
    article = await writer.process_message(write_msg)
    print(f"Writer: {article.content}\n")


async def example_5_memory_in_collaboration():
    """Example 5: Memory in multi - agent collaboration"""
    print("\n=== Example 5: Memory in Collaboration ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create team
    analyst = Agent(name="analyst", role="analyst", llm_provider=llm)
    strategist = Agent(name="strategist", role="strategist", llm_provider=llm)

    mind = AgentMind(strategy="round_robin")
    mind.add_agent(analyst)
    mind.add_agent(strategist)

    # Collaboration builds shared context
    result = await mind.start_collaboration(
        "Develop a strategy to enter the European market.", max_rounds=2
    )

    print(f"Collaboration result:\n{result.final_output}\n")
    print(f"Conversation history: {len(result.conversation_history)} exchanges")

    # Each agent maintains their own memory
    print(f"Analyst memory: {len(analyst.memory)} messages")
    print(f"Strategist memory: {len(strategist.memory)} messages")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("AgentMind Tutorial 02: Memory Systems")
    print("=" * 60)

    await example_1_short_term_memory()
    await example_2_memory_context()
    await example_3_memory_management()
    await example_4_shared_memory()
    await example_5_memory_in_collaboration()

    print("\n" + "=" * 60)
    print("Tutorial Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. Agents automatically maintain conversation history")
    print("2. Memory provides context for better responses")
    print("3. Memory size can be managed to control context window")
    print("4. Each agent has independent memory in collaborations")
    print("\nNext: Tutorial 03 - Creating Custom Tools")


if __name__ == "__main__":
    asyncio.run(main())
