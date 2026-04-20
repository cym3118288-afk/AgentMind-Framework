"""Example: Running benchmarks and generating reports."""

import asyncio

from agentmind.core import Agent, AgentMind
from agentmind.evaluation import Evaluator, MarkdownReporter
from agentmind.evaluation.benchmark import (
    create_agent_bench_subset,
    create_custom_suite,
    create_gaia_subset,
)
from agentmind.llm import OllamaProvider


async def main():
    """Run benchmarks and generate evaluation report."""
    print("AgentMind Evaluation Suite")
    print("=" * 60)

    # Initialize LLM provider
    llm = OllamaProvider(model="llama3.2")

    # Create a multi - agent system
    mind = AgentMind(llm_provider=llm)

    # Add agents
    mind.add_agent(
        Agent(
            name="analyst",
            role="analyst",
            llm_provider=llm,
        )
    )
    mind.add_agent(
        Agent(
            name="creative",
            role="creative",
            llm_provider=llm,
        )
    )
    mind.add_agent(
        Agent(
            name="synthesizer",
            role="synthesizer",
            llm_provider=llm,
        )
    )

    # Create evaluator
    evaluator = Evaluator()

    # Add benchmark suites
    print("\nLoading benchmark suites...")
    evaluator.add_suite(create_gaia_subset())
    evaluator.add_suite(create_agent_bench_subset())
    evaluator.add_suite(create_custom_suite())

    # Run evaluation
    print("\nRunning evaluation...")
    print("This may take several minutes...\n")

    _results = await evaluator.evaluate(
        mind,
        max_rounds=3,
        parallel=False,  # Set to True for faster execution
    )

    # Print summary
    evaluator.print_summary()

    # Print detailed results
    print("\n" + "=" * 60)
    print("Would you like to see detailed results? (y / n)")
    # evaluator.print_detailed_results()

    # Generate Markdown report
    print("\nGenerating Markdown report...")
    reporter = MarkdownReporter()

    for suite_name, suite_results in evaluator.get_results().items():
        reporter.add_results(suite_results, suite_name)

    reporter.generate_report("benchmarks / evaluation_report.md")

    print("\nEvaluation complete!")
    print("Report saved to: benchmarks / evaluation_report.md")


if __name__ == "__main__":
    asyncio.run(main())
