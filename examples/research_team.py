"""Research Team Example - Multi-agent collaboration for research and writing.

This example demonstrates a team of agents working together:
- Researcher: Searches for information and gathers data
- Critic: Reviews findings and provides feedback
- Writer: Synthesizes information into a coherent report

The team collaborates to produce a research report with citations.
"""

import asyncio
from agentmind.core import Agent, AgentMind, AgentConfig, Message, MessageRole
from agentmind.core.types import CollaborationStrategy
from agentmind.tools import WebSearch, Calculator, get_global_registry


async def main():
    """Run the research team collaboration example."""

    print("=" * 60)
    print("Research Team Example - Multi-Agent Collaboration")
    print("=" * 60)
    print()

    # Register tools
    registry = get_global_registry()
    web_search = WebSearch()
    calculator = Calculator()
    registry.register(web_search)
    registry.register(calculator)

    # Create agent configurations
    researcher_config = AgentConfig(
        name="researcher",
        role="researcher",
        backstory="Expert researcher skilled at finding and analyzing information from multiple sources.",
        temperature=0.7,
        max_tokens=500,
        tools=["web_search", "calculator"]
    )

    critic_config = AgentConfig(
        name="critic",
        role="critic",
        backstory="Critical thinker who evaluates arguments, identifies gaps, and ensures quality.",
        temperature=0.6,
        max_tokens=400,
        tools=[]
    )

    writer_config = AgentConfig(
        name="writer",
        role="assistant",
        backstory="Professional writer who synthesizes information into clear, well-structured reports.",
        temperature=0.8,
        max_tokens=600,
        tools=[]
    )

    # Create agents (without LLM for this demo - using template responses)
    researcher = Agent(name="researcher", role="researcher", config=researcher_config)
    critic = Agent(name="critic", role="critic", config=critic_config)
    writer = Agent(name="writer", role="assistant", config=writer_config)

    # Create AgentMind with hierarchical strategy
    mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN)
    mind.add_agent(researcher)
    mind.add_agent(critic)
    mind.add_agent(writer)

    print("\n[*] Team assembled:")
    print(f"    - {researcher.name}: {researcher.config.backstory}")
    print(f"    - {critic.name}: {critic.config.backstory}")
    print(f"    - {writer.name}: {writer.config.backstory}")
    print()

    # Research topic
    topic = "The impact of artificial intelligence on software development productivity"

    print(f"[*] Research Topic: {topic}")
    print()

    # Phase 1: Research
    print("[Phase 1] Research Phase")
    print("-" * 60)
    research_msg = Message(
        content=f"Research the following topic and gather key findings: {topic}",
        sender="system",
        role=MessageRole.SYSTEM
    )
    research_response = await researcher.process_message(research_msg)
    print(f"{research_response.sender}: {research_response.content}")
    print()

    # Simulate tool usage
    print("[*] Researcher uses web_search tool...")
    search_result = await web_search.execute(
        query="AI impact on software development productivity",
        max_results=3
    )
    if search_result.success:
        print(f"[Tool Result] Found {search_result.metadata.get('num_results', 0)} results")
        print(f"Preview: {search_result.output[:200]}...")
    print()

    # Phase 2: Critique
    print("[Phase 2] Critique Phase")
    print("-" * 60)
    critique_msg = Message(
        content=f"Review the research findings and identify any gaps or concerns: {research_response.content}",
        sender="system",
        role=MessageRole.SYSTEM
    )
    critique_response = await critic.process_message(critique_msg)
    print(f"{critique_response.sender}: {critique_response.content}")
    print()

    # Phase 3: Writing
    print("[Phase 3] Writing Phase")
    print("-" * 60)
    write_msg = Message(
        content=f"Write a comprehensive report based on the research and critique. Research: {research_response.content}. Critique: {critique_response.content}",
        sender="system",
        role=MessageRole.SYSTEM
    )
    write_response = await writer.process_message(write_msg)
    print(f"{write_response.sender}: {write_response.content}")
    print()

    # Full collaboration using AgentMind
    print("\n" + "=" * 60)
    print("[*] Running full team collaboration...")
    print("=" * 60)
    print()

    result = await mind.start_collaboration(
        initial_message=f"Collaborate to produce a research report on: {topic}",
        max_rounds=3,
        use_llm=False  # Using template responses for demo
    )

    print()
    print("[*] Collaboration Results:")
    print(f"    - Success: {result.success}")
    print(f"    - Total Rounds: {result.total_rounds}")
    print(f"    - Total Messages: {result.total_messages}")
    print(f"    - Agent Contributions: {result.agent_contributions}")
    print()

    # Save session
    print("[*] Saving session...")
    session_path = mind.save_session("research_team_demo")
    print(f"    Session saved to: {session_path}")
    print()

    # Display final output
    print("=" * 60)
    print("Final Output")
    print("=" * 60)
    print(result.final_output)
    print()

    # Show conversation summary
    summary = mind.get_conversation_summary()
    print("[*] Conversation Summary:")
    print(f"    - Total messages: {summary['total_messages']}")
    print(f"    - Active agents: {summary['active_agents']}/{summary['total_agents']}")
    print()

    # Demonstrate session loading
    print("[*] Testing session load...")
    new_mind = AgentMind()
    if new_mind.load_session("research_team_demo"):
        print("    Session loaded successfully!")
        print(f"    Restored {len(new_mind.agents)} agents and {len(new_mind.conversation_history)} messages")
    print()

    print("=" * 60)
    print("Research Team Example Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
