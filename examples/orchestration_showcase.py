"""Orchestration Showcase - Demonstrating all orchestration modes.

This example demonstrates all production - ready orchestration modes:
1. Sequential - Chain of responsibility
2. Hierarchical - 3 - tier architecture
3. Debate - Multi - round deliberation with voting
4. Consensus - Agreement - based decision making
5. Swarm - Dynamic scaling
6. Graph - DAG - based workflows
7. Hybrid - Combined modes

Each mode is demonstrated with realistic scenarios.
"""

import asyncio
import logging
from typing import List

from agentmind.core import Agent, AgentConfig
from agentmind.orchestration.advanced_modes import (
    OrchestrationMode,
    SequentialOrchestrator,
    HierarchicalOrchestrator,
    DebateOrchestrator,
    ConsensusOrchestrator,
    SwarmOrchestrator,
    GraphOrchestrator,
    HybridOrchestrator,
    recommend_mode,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def create_test_agents(num_agents: int, prefix: str = "agent") -> List[Agent]:
    """Create test agents for demonstrations."""
    agents = []
    roles = ["analyst", "creative", "critic", "researcher", "coordinator"]

    for i in range(num_agents):
        role = roles[i % len(roles)]
        agent = Agent(
            name=f"{prefix}_{i + 1}",
            role=role,
            config=AgentConfig(
                name=f"{prefix}_{i + 1}",
                role=role,
                temperature=0.7,
            ),
        )
        agents.append(agent)

    return agents


async def demo_sequential():
    """Demonstrate sequential orchestration."""
    print("\n" + "=" * 80)
    print("SEQUENTIAL ORCHESTRATION DEMO")
    print("=" * 80)
    print("Scenario: Document review pipeline")
    print()

    agents = create_test_agents(4, "reviewer")
    orchestrator = SequentialOrchestrator()

    task = """Review this product specification document:

Product: AI - powered task manager
Features: Natural language input, smart scheduling, team collaboration
Target: Small to medium businesses

Each reviewer should focus on their specialty and pass findings to the next."""

    result = await orchestrator.orchestrate(
        agents,
        task,
        early_termination=False,
        pass_full_history=True,
        max_retries=1,
    )

    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Rounds: {result.total_rounds}")
    print(f"Messages: {result.total_messages}")
    print(f"Duration: {result.metadata.get('duration', 0):.2f}s")
    print("\nAgent Contributions:")
    for agent, count in result.agent_contributions.items():
        print(f"  {agent}: {count} messages")


async def demo_hierarchical():
    """Demonstrate hierarchical orchestration."""
    print("\n" + "=" * 80)
    print("HIERARCHICAL ORCHESTRATION DEMO")
    print("=" * 80)
    print("Scenario: Software development project")
    print()

    # Manager, 3 workers, reviewer
    agents = [
        Agent("project_manager", "supervisor"),
        Agent("backend_dev", "executor"),
        Agent("frontend_dev", "executor"),
        Agent("qa_engineer", "executor"),
        Agent("tech_lead", "critic"),
    ]

    orchestrator = HierarchicalOrchestrator()

    task = """Develop a user authentication system with:
- Email / password login
- OAuth integration (Google, GitHub)
- Two - factor authentication
- Session management

Manager: Break down into tasks
Workers: Implement assigned components
Reviewer: Evaluate quality and integration"""

    result = await orchestrator.orchestrate(
        agents,
        task,
        quality_threshold=0.7,
        max_escalations=2,
        enable_load_balancing=True,
    )

    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Rounds: {result.total_rounds}")
    print(f"Messages: {result.total_messages}")
    print(
        f"Escalations: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('escalations', 0)}"
    )
    print(
        f"Final Quality: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('final_quality', 0):.2f}"
    )


async def demo_debate():
    """Demonstrate debate orchestration."""
    print("\n" + "=" * 80)
    print("DEBATE ORCHESTRATION DEMO")
    print("=" * 80)
    print("Scenario: Technology decision - Microservices vs Monolith")
    print()

    agents = [
        Agent("moderator", "coordinator"),
        Agent("architect_1", "analyst"),
        Agent("architect_2", "analyst"),
        Agent("ops_engineer", "executor"),
        Agent("product_manager", "coordinator"),
    ]

    orchestrator = DebateOrchestrator()

    task = """Should we adopt a microservices architecture for our new platform?

Consider:
- Team size and expertise
- Deployment complexity
- Scalability requirements
- Development velocity
- Operational overhead"""

    result = await orchestrator.orchestrate(
        agents,
        task,
        debate_rounds=3,
        voting_mechanism="weighted",
        convergence_threshold=0.75,
        enable_moderator=True,
        weights={
            "architect_1": 2.0,
            "architect_2": 2.0,
            "ops_engineer": 1.5,
            "product_manager": 1.0,
        },
    )

    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(
        f"Debate Rounds: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('debate_rounds', 0)}"
    )
    print(
        f"Final Convergence: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('final_convergence', 0):.2f}"  # noqa: E501
    )
    print(
        f"Vote Result: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('vote_result', {})}"
    )


async def demo_consensus():
    """Demonstrate consensus orchestration."""
    print("\n" + "=" * 80)
    print("CONSENSUS ORCHESTRATION DEMO")
    print("=" * 80)
    print("Scenario: Team agreement on coding standards")
    print()

    agents = create_test_agents(5, "developer")

    orchestrator = ConsensusOrchestrator()

    task = """Establish coding standards for our Python project:

Topics to decide:
- Line length limit
- Import organization
- Type hints policy
- Documentation requirements
- Testing coverage threshold

Reach consensus through iterative refinement."""

    result = await orchestrator.orchestrate(
        agents,
        task,
        consensus_threshold=0.8,
        max_iterations=3,
        enable_peer_review=True,
    )

    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(
        f"Iterations: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('iterations', 0)}"
    )
    print(
        f"Consensus Reached: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('consensus_reached', False)}"  # noqa: E501
    )
    print(
        f"Final Score: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('final_consensus_score', 0):.2f}"  # noqa: E501
    )


async def demo_swarm():
    """Demonstrate swarm orchestration."""
    print("\n" + "=" * 80)
    print("SWARM ORCHESTRATION DEMO")
    print("=" * 80)
    print("Scenario: Parallel data processing")
    print()

    agents = create_test_agents(8, "worker")

    orchestrator = SwarmOrchestrator()

    task = """Process customer feedback data:

Dataset: 10,000 customer reviews
Tasks:
- Sentiment analysis
- Topic extraction
- Issue categorization
- Priority scoring
- Trend identification

Swarm should dynamically scale based on workload."""

    result = await orchestrator.orchestrate(
        agents,
        task,
        max_agents=8,
        min_agents=3,
        complexity_threshold=50,
        enable_work_stealing=True,
    )

    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(
        f"Swarm Size: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('swarm_size', 0)}"
    )
    print(
        f"Task Complexity: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('task_complexity', 0)}"
    )
    print(
        f"Subtasks: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('subtasks', 0)}"
    )


async def demo_graph():
    """Demonstrate graph orchestration."""
    print("\n" + "=" * 80)
    print("GRAPH ORCHESTRATION DEMO")
    print("=" * 80)
    print("Scenario: CI / CD pipeline workflow")
    print()

    # Create agents for different pipeline stages
    agents = [
        Agent("code_checkout", "executor"),
        Agent("unit_tests", "executor"),
        Agent("integration_tests", "executor"),
        Agent("security_scan", "analyst"),
        Agent("build", "executor"),
        Agent("deploy_staging", "executor"),
        Agent("smoke_tests", "executor"),
        Agent("deploy_prod", "executor"),
    ]

    orchestrator = GraphOrchestrator()

    # Build pipeline graph
    orchestrator.add_node("checkout", agents[0], "agent")
    orchestrator.add_node("unit_test", agents[1], "agent")
    orchestrator.add_node("integration_test", agents[2], "agent")
    orchestrator.add_node("security", agents[3], "agent")
    orchestrator.add_node("build", agents[4], "agent")
    orchestrator.add_node("stage_deploy", agents[5], "agent")
    orchestrator.add_node("smoke_test", agents[6], "decision")
    orchestrator.add_node("prod_deploy", agents[7], "agent")

    # Define workflow
    orchestrator.add_edge("checkout", "unit_test")
    orchestrator.add_edge("checkout", "security")
    orchestrator.add_edge("unit_test", "integration_test")
    orchestrator.add_edge("integration_test", "build")
    orchestrator.add_edge("security", "build")
    orchestrator.add_edge("build", "stage_deploy")
    orchestrator.add_edge("stage_deploy", "smoke_test")
    orchestrator.add_edge("smoke_test", "prod_deploy")

    task = "Execute CI / CD pipeline for release v2.1.0"

    result = await orchestrator.orchestrate(
        agents,
        task,
        start_node="checkout",
        max_parallel=3,
    )

    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(
        f"Nodes Visited: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('nodes_visited', 0)}"
    )
    print(
        f"Execution Order: {result.metadata.get('metrics', {}).get('custom_metrics', {}).get('execution_order', [])}"
    )

    # Show graph visualization
    print("\nGraph Visualization (Mermaid):")
    print(orchestrator.visualize_graph())

    print("\nGraph Statistics:")
    stats = orchestrator.get_graph_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


async def demo_hybrid():
    """Demonstrate hybrid orchestration."""
    print("\n" + "=" * 80)
    print("HYBRID ORCHESTRATION DEMO")
    print("=" * 80)
    print("Scenario: Research project (Hierarchical + Swarm)")
    print()

    agents = create_test_agents(10, "researcher")

    orchestrator = HybridOrchestrator(
        OrchestrationMode.HIERARCHICAL,
        OrchestrationMode.SWARM,
    )

    task = """Conduct comprehensive market research:

Phase 1 (Hierarchical): Planning and coordination
- Manager defines research areas
- Workers assigned to domains
- Reviewer validates approach

Phase 2 (Swarm): Parallel data collection
- Swarm processes multiple data sources
- Dynamic scaling based on data volume
- Emergent synthesis of findings"""

    result = await orchestrator.orchestrate(
        agents,
        task,
        split_ratio=0.4,
        integration_strategy="sequential",
        phase_1_kwargs={"quality_threshold": 0.7},
        phase_2_kwargs={"enable_work_stealing": True},
    )

    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Total Rounds: {result.total_rounds}")
    print(f"Total Messages: {result.total_messages}")
    print(f"Hybrid Modes: {result.metadata.get('hybrid_modes', [])}")
    print(f"Integration: {result.metadata.get('integration_strategy', 'unknown')}")


async def demo_mode_recommendation():
    """Demonstrate mode recommendation system."""
    print("\n" + "=" * 80)
    print("MODE RECOMMENDATION DEMO")
    print("=" * 80)
    print()

    scenarios = [
        {
            "name": "Small team code review",
            "num_agents": 3,
            "complexity": "low",
            "requires_consensus": False,
            "has_hierarchy": False,
        },
        {
            "name": "Enterprise architecture decision",
            "num_agents": 8,
            "complexity": "high",
            "requires_consensus": True,
            "has_hierarchy": True,
        },
        {
            "name": "Large - scale data processing",
            "num_agents": 12,
            "complexity": "high",
            "requires_consensus": False,
            "has_hierarchy": False,
        },
        {
            "name": "Team policy agreement",
            "num_agents": 5,
            "complexity": "medium",
            "requires_consensus": True,
            "has_hierarchy": False,
        },
    ]

    for scenario in scenarios:
        recommended = recommend_mode(
            num_agents=scenario["num_agents"],
            task_complexity=scenario["complexity"],
            requires_consensus=scenario["requires_consensus"],
            has_hierarchy=scenario["has_hierarchy"],
        )

        print(f"\nScenario: {scenario['name']}")
        print(f"  Agents: {scenario['num_agents']}")
        print(f"  Complexity: {scenario['complexity']}")
        print(f"  Requires Consensus: {scenario['requires_consensus']}")
        print(f"  Has Hierarchy: {scenario['has_hierarchy']}")
        print(f"  → Recommended Mode: {recommended.value}")


async def main():
    """Run all orchestration demos."""
    print("=" * 80)
    print("AGENTMIND ORCHESTRATION SHOWCASE")
    print("Production - Ready Multi - Agent Orchestration Patterns")
    print("=" * 80)

    demos = [
        ("Sequential", demo_sequential),
        ("Hierarchical", demo_hierarchical),
        ("Debate", demo_debate),
        ("Consensus", demo_consensus),
        ("Swarm", demo_swarm),
        ("Graph", demo_graph),
        ("Hybrid", demo_hybrid),
        ("Recommendations", demo_mode_recommendation),
    ]

    for name, demo_func in demos:
        try:
            await demo_func()
        except Exception as e:
            print(f"\n❌ {name} demo failed: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("ALL DEMOS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
