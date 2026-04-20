"""
Tutorial 04: Multi - Agent Orchestration

This tutorial covers orchestration strategies:
- Round - robin coordination
- Broadcast communication
- Hierarchical structures
- Consensus mechanisms
- Dynamic task allocation

Estimated time: 25 minutes
Difficulty: Intermediate
"""

import asyncio
from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider


async def example_1_round_robin():
    """Example 1: Round - robin orchestration"""
    print("\n=== Example 1: Round - Robin Orchestration ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create agents
    researcher = Agent(name="researcher", role="researcher", llm_provider=llm)
    analyst = Agent(name="analyst", role="analyst", llm_provider=llm)
    writer = Agent(name="writer", role="writer", llm_provider=llm)

    # Round - robin: agents take turns in sequence
    mind = AgentMind(strategy="round_robin")
    mind.add_agent(researcher)
    mind.add_agent(analyst)
    mind.add_agent(writer)

    result = await mind.start_collaboration(
        "Research and write about quantum computing applications.", max_rounds=3
    )

    print(f"Result: {result.final_output[:300]}...\n")
    print("Agents participated in order: researcher → analyst → writer")


async def example_2_broadcast():
    """Example 2: Broadcast strategy"""
    print("\n=== Example 2: Broadcast Strategy ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create diverse agents
    optimist = Agent(name="optimist", role="creative", llm_provider=llm)
    pessimist = Agent(name="pessimist", role="critic", llm_provider=llm)
    realist = Agent(name="realist", role="analyst", llm_provider=llm)

    # Broadcast: all agents respond to the same prompt
    mind = AgentMind(strategy="broadcast")
    mind.add_agent(optimist)
    mind.add_agent(pessimist)
    mind.add_agent(realist)

    result = await mind.start_collaboration(
        "Should we invest in expanding to the Asian market?", max_rounds=1
    )

    print("All agents provided their perspectives simultaneously")
    print(f"Total responses: {len(result.conversation_history)}\n")


async def example_3_hierarchical():
    """Example 3: Hierarchical orchestration"""
    print("\n=== Example 3: Hierarchical Structure ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create hierarchy: manager coordinates subordinates
    manager = Agent(name="manager", role="coordinator", llm_provider=llm)
    dev1 = Agent(name="frontend_dev", role="developer", llm_provider=llm)
    dev2 = Agent(name="backend_dev", role="developer", llm_provider=llm)
    qa = Agent(name="qa_engineer", role="tester", llm_provider=llm)

    # Hierarchical: manager delegates to subordinates
    mind = AgentMind(strategy="hierarchical")
    mind.add_agent(manager)  # First agent is the manager
    mind.add_agent(dev1)
    mind.add_agent(dev2)
    mind.add_agent(qa)

    result = await mind.start_collaboration(
        "Design and plan a new user authentication system.", max_rounds=4
    )

    print("Manager coordinated the team:")
    print("- Frontend Developer")
    print("- Backend Developer")
    print("- QA Engineer")
    print(f"\nFinal plan: {result.final_output[:200]}...\n")


async def example_4_consensus():
    """Example 4: Consensus - based decision making"""
    print("\n=== Example 4: Consensus Mechanism ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create decision - making team
    expert1 = Agent(name="expert1", role="analyst", llm_provider=llm)
    expert2 = Agent(name="expert2", role="analyst", llm_provider=llm)
    expert3 = Agent(name="expert3", role="analyst", llm_provider=llm)

    mind = AgentMind(strategy="broadcast")
    mind.add_agent(expert1)
    mind.add_agent(expert2)
    mind.add_agent(expert3)

    # Simulate consensus building
    result = await mind.start_collaboration(
        "Should we adopt microservices architecture? Provide yes / no with reasoning.", max_rounds=1
    )

    print("Experts provided their opinions:")
    print("Consensus requires majority agreement")
    print(f"Responses collected: {len(result.conversation_history)}\n")


async def example_5_dynamic_allocation():
    """Example 5: Dynamic task allocation"""
    print("\n=== Example 5: Dynamic Task Allocation ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create specialized agents
    data_agent = Agent(name="data_specialist", role="analyst", llm_provider=llm)
    ml_agent = Agent(name="ml_specialist", role="researcher", llm_provider=llm)
    viz_agent = Agent(name="viz_specialist", role="creative", llm_provider=llm)

    mind = AgentMind(strategy="round_robin")
    mind.add_agent(data_agent)
    mind.add_agent(ml_agent)
    mind.add_agent(viz_agent)

    # Complex task requiring different skills
    result = await mind.start_collaboration(
        "Build a customer churn prediction system with visualization dashboard.", max_rounds=3
    )

    print("Task allocated based on agent specializations:")
    print("1. Data Specialist: Data preparation")
    print("2. ML Specialist: Model development")
    print("3. Viz Specialist: Dashboard design")
    print(f"\nCollaboration rounds: {len(result.conversation_history)}\n")


async def example_6_mixed_strategies():
    """Example 6: Combining orchestration strategies"""
    print("\n=== Example 6: Mixed Strategies ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Phase 1: Broadcast for brainstorming
    print("Phase 1: Brainstorming (Broadcast)")
    brainstorm_agents = [
        Agent(name=f"creative_{i}", role="creative", llm_provider=llm) for i in range(3)
    ]

    mind1 = AgentMind(strategy="broadcast")
    for agent in brainstorm_agents:
        mind1.add_agent(agent)

    ideas = await mind1.start_collaboration(
        "Generate innovative product ideas for remote work.", max_rounds=1
    )
    print(f"Generated {len(ideas.conversation_history)} ideas\n")

    # Phase 2: Round - robin for refinement
    print("Phase 2: Refinement (Round - Robin)")
    refine_agents = [
        Agent(name="analyst", role="analyst", llm_provider=llm),
        Agent(name="designer", role="creative", llm_provider=llm),
        Agent(name="engineer", role="developer", llm_provider=llm),
    ]

    mind2 = AgentMind(strategy="round_robin")
    for agent in refine_agents:
        mind2.add_agent(agent)

    refined = await mind2.start_collaboration(
        f"Refine these ideas: {ideas.final_output[:200]}", max_rounds=3
    )
    print(f"Refined through {len(refined.conversation_history)} rounds\n")


async def example_7_orchestration_comparison():
    """Example 7: Comparing orchestration strategies"""
    print("\n=== Example 7: Strategy Comparison ===\n")

    strategies = {
        "round_robin": "Sequential, ordered participation",
        "broadcast": "Parallel, simultaneous responses",
        "hierarchical": "Manager - subordinate delegation",
    }

    print("Orchestration Strategy Comparison:\n")
    for strategy, description in strategies.items():
        print(f"{strategy.upper()}:")
        print(f"  Description: {description}")
        print("  Best for: ", end="")

        if strategy == "round_robin":
            print("Sequential workflows, pipeline processing")
        elif strategy == "broadcast":
            print("Diverse perspectives, parallel analysis")
        elif strategy == "hierarchical":
            print("Complex coordination, task delegation")

        print()


async def main():
    """Run all examples"""
    print("=" * 60)
    print("AgentMind Tutorial 04: Multi - Agent Orchestration")
    print("=" * 60)

    await example_1_round_robin()
    await example_2_broadcast()
    await example_3_hierarchical()
    await example_4_consensus()
    await example_5_dynamic_allocation()
    await example_6_mixed_strategies()
    await example_7_orchestration_comparison()

    print("\n" + "=" * 60)
    print("Tutorial Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. Round - robin: Sequential agent participation")
    print("2. Broadcast: All agents respond simultaneously")
    print("3. Hierarchical: Manager coordinates subordinates")
    print("4. Choose strategy based on task requirements")
    print("5. Strategies can be combined for complex workflows")
    print("\nNext: Tutorial 05 - Plugin Development")


if __name__ == "__main__":
    asyncio.run(main())
