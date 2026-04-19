"""Example: Advanced orchestration patterns.

Demonstrates sophisticated multi-agent coordination techniques including
consensus mechanisms, parallel task decomposition, dynamic agent spawning,
and skill-based agent matching.

Difficulty: ADVANCED
Prerequisites: Strong understanding of multi-agent systems, async programming
Estimated time: 30-45 minutes

What you'll learn:
- Implementing consensus mechanisms (majority, unanimous, weighted voting)
- Parallel task decomposition for complex workflows
- Dynamic agent spawning based on workload
- Skill-based agent matching and specialization
- Advanced orchestration patterns for production systems

Expected Output:
- Consensus demo: Agents vote on proposals with different mechanisms
- Parallel decomposition: Complex tasks split into concurrent subtasks
- Dynamic spawning: Agents created on-demand for workload
- Skill matching: Agents selected based on capabilities
- Demonstrates enterprise-grade orchestration patterns
"""

import asyncio

from agentmind.core import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.orchestration.advanced import (
    ConsensusOrchestrator,
    DynamicAgentSpawner,
    ParallelTaskDecomposer,
    SkillMatcher,
    SpecializationEngine,
    VotingMechanism,
)


async def demo_consensus():
    """Demonstrate consensus mechanisms."""
    print("\n" + "=" * 60)
    print("CONSENSUS ORCHESTRATION DEMO")
    print("=" * 60)

    llm = OllamaProvider(model="llama3.2")

    # Create agents with different perspectives
    agents = [
        Agent(name="optimist", role="analyst", llm_provider=llm),
        Agent(name="pessimist", role="analyst", llm_provider=llm),
        Agent(name="realist", role="analyst", llm_provider=llm),
    ]

    orchestrator = ConsensusOrchestrator(agents)

    # Reach consensus on a proposal
    result = await orchestrator.reach_consensus(
        "Should we invest in developing a new AI feature?",
        mechanism=VotingMechanism.MAJORITY,
        threshold=0.6,
    )

    print("\nConsensus Result:")
    print(f"Proposal: {result['proposal']}")
    print(f"Mechanism: {result['mechanism']}")
    print(f"Consensus: {result['result'].get('consensus')}")
    print(f"Decision: {result['result'].get('decision')}")

    print("\nVotes:")
    for agent_name, vote_data in result["votes"].items():
        print(f"  {agent_name}: {vote_data['vote']} (confidence: {vote_data['confidence']})")
        print(f"    Reasoning: {vote_data['reasoning'][:80]}...")


async def demo_parallel_decomposition():
    """Demonstrate parallel task decomposition."""
    print("\n" + "=" * 60)
    print("PARALLEL TASK DECOMPOSITION DEMO")
    print("=" * 60)

    llm = OllamaProvider(model="llama3.2")

    decomposer = ParallelTaskDecomposer(llm)

    # Decompose a complex task
    task = "Research, design, and implement a recommendation system for an e-commerce platform"
    subtasks = await decomposer.decompose(task, max_subtasks=4)

    print(f"\nOriginal Task: {task}")
    print(f"\nDecomposed into {len(subtasks)} subtasks:")

    for i, subtask in enumerate(subtasks, 1):
        print(f"\n{i}. {subtask['description']}")
        print(f"   Complexity: {subtask['complexity']}")
        print(f"   Dependencies: {subtask['dependencies'] or 'None'}")

    # Execute in parallel
    agents = [Agent(name=f"worker_{i}", role="worker", llm_provider=llm) for i in range(3)]

    print("\nExecuting subtasks in parallel...")
    results = await decomposer.execute_parallel(subtasks, agents, timeout=30.0)

    print(f"\nExecution Results:")
    print(f"  Completed: {results['completed']}/{results['total_subtasks']}")
    print(f"  Failed: {results['failed']}")


async def demo_dynamic_spawning():
    """Demonstrate dynamic agent spawning."""
    print("\n" + "=" * 60)
    print("DYNAMIC AGENT SPAWNING DEMO")
    print("=" * 60)

    llm = OllamaProvider(model="llama3.2")
    spawner = DynamicAgentSpawner(llm)

    # Spawn agents for a task
    task = "Build a secure web application with user authentication, data analytics, and real-time notifications"

    print(f"\nTask: {task}")
    print("\nAnalyzing task and spawning appropriate agents...")

    agents = await spawner.spawn_for_task(task, max_agents=4)

    print(f"\nSpawned {len(agents)} agents:")
    for agent in agents:
        print(f"  - {agent.name} ({agent.role})")

    # Show spawn history
    history = spawner.get_spawn_history()
    if history:
        last_spawn = history[-1]
        print(f"\nTask Requirements:")
        print(f"  Domain: {last_spawn['requirements'].get('domain')}")
        print(f"  Complexity: {last_spawn['requirements'].get('complexity')}")
        print(f"  Skills: {', '.join(last_spawn['requirements'].get('skills', []))}")


async def demo_skill_matching():
    """Demonstrate skill matching and specialization."""
    print("\n" + "=" * 60)
    print("SKILL MATCHING & SPECIALIZATION DEMO")
    print("=" * 60)

    llm = OllamaProvider(model="llama3.2")

    # Create agents
    agents = [
        Agent(name="alice", role="developer", llm_provider=llm),
        Agent(name="bob", role="designer", llm_provider=llm),
        Agent(name="charlie", role="analyst", llm_provider=llm),
    ]

    # Set up specialization
    engine = SpecializationEngine()

    # Add skills to agents
    engine.add_agent_skill(agents[0], "python", 0.9, "Python programming")
    engine.add_agent_skill(agents[0], "testing", 0.7, "Software testing")
    engine.add_agent_skill(agents[1], "ui_design", 0.8, "UI/UX design")
    engine.add_agent_skill(agents[1], "prototyping", 0.6, "Rapid prototyping")
    engine.add_agent_skill(agents[2], "data_analysis", 0.85, "Data analysis")
    engine.add_agent_skill(agents[2], "statistics", 0.75, "Statistical analysis")

    # Show agent specializations
    print("\nAgent Specializations:")
    for agent in agents:
        summary = engine.get_specialization_summary(agent)
        print(f"\n{summary['agent']}:")
        print(f"  Primary: {summary['specialization']} ({summary['primary_proficiency']:.2f})")
        print(f"  Skills:")
        for skill in summary["skills"]:
            print(f"    - {skill['name']}: {skill['proficiency']:.2f}")

    # Match agents to tasks
    matcher = SkillMatcher(engine)

    tasks = [
        {"description": "Implement API endpoints", "required_skills": ["python", "testing"]},
        {"description": "Design user interface", "required_skills": ["ui_design", "prototyping"]},
        {"description": "Analyze user data", "required_skills": ["data_analysis", "statistics"]},
    ]

    print("\n\nTask Assignments:")
    assignments = matcher.match_agents_to_tasks(agents, tasks)

    for task_desc, assigned_agent in assignments.items():
        agent_name = assigned_agent.name if assigned_agent else "None"
        print(f"  {task_desc[:40]}... -> {agent_name}")

    # Skill coverage analysis
    print("\n\nSkill Coverage Analysis:")
    required_skills = ["python", "ui_design", "data_analysis", "machine_learning"]
    coverage = matcher.get_skill_coverage(agents, required_skills)

    for skill, info in coverage.items():
        status = "✓" if info["covered"] else "✗"
        print(f"  {status} {skill}: {info['max_proficiency']:.2f}")


async def main():
    """Run all demos."""
    print("AgentMind Advanced Orchestration Patterns")
    print("=" * 60)

    await demo_consensus()
    await demo_parallel_decomposition()
    await demo_dynamic_spawning()
    await demo_skill_matching()

    print("\n" + "=" * 60)
    print("All demos completed!")


if __name__ == "__main__":
    asyncio.run(main())
