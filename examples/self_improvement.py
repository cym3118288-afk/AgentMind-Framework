"""Example: Self-improvement mechanisms."""

import asyncio

from agentmind.core import Agent, AgentMind
from agentmind.improvement import DebateImprover, FeedbackLoop, PromptOptimizer
from agentmind.llm import OllamaProvider


async def demo_prompt_optimization():
    """Demonstrate prompt optimization."""
    print("\n" + "=" * 60)
    print("PROMPT OPTIMIZATION DEMO")
    print("=" * 60)

    llm = OllamaProvider(model="llama3.2")
    optimizer = PromptOptimizer(llm)

    # Current prompt
    current_prompt = "You are a helpful assistant who answers questions."

    # Task examples
    task_examples = [
        {
            "task": "Explain quantum computing",
            "response": "Quantum computing uses quantum bits...",
        },
        {
            "task": "Write a Python function",
            "response": "Here's a function...",
        },
    ]

    # Feedback
    feedback = [
        "Be more technical and precise",
        "Include examples in explanations",
        "Structure responses better",
    ]

    print("\nCurrent Prompt:")
    print(current_prompt)

    print("\nOptimizing based on feedback...")
    optimized_prompt = await optimizer.optimize_prompt(
        current_prompt,
        task_examples,
        feedback,
    )

    print("\nOptimized Prompt:")
    print(optimized_prompt)


async def demo_debate_improvement():
    """Demonstrate debate-based improvement."""
    print("\n" + "=" * 60)
    print("DEBATE-BASED IMPROVEMENT DEMO")
    print("=" * 60)

    llm = OllamaProvider(model="llama3.2")

    # Create agents with different perspectives
    agents = [
        Agent(name="proponent", role="debater", llm_provider=llm),
        Agent(name="opponent", role="debater", llm_provider=llm),
        Agent(name="moderator", role="judge", llm_provider=llm),
    ]

    improver = DebateImprover(llm)

    # Run debate
    topic = "Should companies adopt a 4-day work week?"

    print(f"\nDebate Topic: {topic}")
    print("\nRunning debate with 2 rounds...")

    result = await improver.debate(
        topic=topic,
        agents=agents[:2],  # Use first two agents
        rounds=2,
        judge_agent=agents[2],  # Use third as judge
    )

    print(f"\nDebate completed with {len(result['transcript'])} exchanges")
    print(f"\nConsensus:")
    print(result['consensus'][:200] + "...")

    # Improve an output through criticism
    print("\n\nImproving output through iterative criticism...")

    original_output = "Remote work is good because people can work from home and save time on commuting."

    improvement_result = await improver.improve_output(
        original_output,
        critic_agents=agents,
        improvement_rounds=2,
    )

    print(f"\nOriginal Output:")
    print(original_output)

    print(f"\nImproved Output:")
    print(improvement_result['final'][:200] + "...")


async def demo_feedback_loop():
    """Demonstrate feedback loop mechanisms."""
    print("\n" + "=" * 60)
    print("FEEDBACK LOOP DEMO")
    print("=" * 60)

    llm = OllamaProvider(model="llama3.2")

    # Create agent
    agent = Agent(name="assistant", role="assistant", llm_provider=llm)

    # Set up feedback loop
    loop = FeedbackLoop()
    loop.add_agent(agent)

    # Simulate interactions
    print("\nRecording interactions...")

    interactions = [
        {
            "task": "Explain machine learning",
            "response": "ML is when computers learn from data...",
            "rating": 4.0,
            "success": True,
            "response_time": 2.5,
        },
        {
            "task": "Write a sorting algorithm",
            "response": "Here's a bubble sort...",
            "rating": 3.5,
            "success": True,
            "response_time": 3.0,
        },
        {
            "task": "Debug this code",
            "response": "I see the issue...",
            "rating": 4.5,
            "success": True,
            "response_time": 2.0,
        },
        {
            "task": "Optimize database query",
            "response": "Try adding an index...",
            "rating": 3.0,
            "success": False,
            "response_time": 4.0,
        },
    ]

    for interaction in interactions:
        loop.record_interaction(
            agent.name,
            interaction["task"],
            interaction["response"],
            rating=interaction["rating"],
            success=interaction["success"],
            response_time=interaction["response_time"],
        )

    # Get metrics
    metrics = loop.get_performance_metrics(agent.name)

    print(f"\nPerformance Metrics for {agent.name}:")
    print(f"  Total interactions: {metrics['total_interactions']}")
    print(f"  Average rating: {metrics['avg_rating']:.2f}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print(f"  Avg response time: {metrics['avg_response_time']:.2f}s")

    # Get improvement suggestions
    suggestions = loop.get_improvement_suggestions(agent.name)

    print(f"\nImprovement Suggestions:")
    for suggestion in suggestions:
        print(f"  - {suggestion}")


async def main():
    """Run all demos."""
    print("AgentMind Self-Improvement Mechanisms")
    print("=" * 60)

    await demo_prompt_optimization()
    await demo_debate_improvement()
    await demo_feedback_loop()

    print("\n" + "=" * 60)
    print("All demos completed!")


if __name__ == "__main__":
    asyncio.run(main())
