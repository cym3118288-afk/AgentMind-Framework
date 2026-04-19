"""Evaluator for running benchmarks and collecting results."""

import asyncio
from typing import Any, Dict, List, Optional

from ..core.mind import AgentMind
from .benchmark import BenchmarkResult, BenchmarkSuite


class Evaluator:
    """Evaluates AgentMind performance using benchmark suites.

    Example:
        >>> evaluator = Evaluator()
        >>> evaluator.add_suite(gaia_suite)
        >>> results = await evaluator.evaluate(mind)
        >>> evaluator.print_summary()
    """

    def __init__(self):
        """Initialize the evaluator."""
        self.suites: List[BenchmarkSuite] = []
        self.results: Dict[str, List[BenchmarkResult]] = {}

    def add_suite(self, suite: BenchmarkSuite) -> None:
        """Add a benchmark suite to evaluate.

        Args:
            suite: BenchmarkSuite to add
        """
        self.suites.append(suite)

    async def evaluate(
        self,
        mind: AgentMind,
        max_rounds: int = 3,
        parallel: bool = False,
    ) -> Dict[str, Any]:
        """Run all benchmark suites and collect results.

        Args:
            mind: AgentMind instance to evaluate
            max_rounds: Maximum collaboration rounds
            parallel: Whether to run benchmarks in parallel

        Returns:
            Dictionary with evaluation results
        """
        all_results = {}

        for suite in self.suites:
            print(f"\nRunning suite: {suite.name}")
            print(f"Description: {suite.description}")
            print(f"Benchmarks: {len(suite.benchmarks)}")
            print("-" * 60)

            results = await suite.run_all(mind, max_rounds, parallel)
            self.results[suite.name] = results

            summary = suite.get_summary(results)
            all_results[suite.name] = summary

            # Print progress
            print(f"Completed: {summary['successful']}/{summary['total_benchmarks']}")
            print(f"Success rate: {summary['success_rate']:.1%}")
            print(f"Total time: {summary['total_time']:.2f}s")

        return all_results

    def get_results(self, suite_name: Optional[str] = None) -> Dict[str, List[BenchmarkResult]]:
        """Get evaluation results.

        Args:
            suite_name: Optional suite name to filter results

        Returns:
            Dictionary of results by suite name
        """
        if suite_name:
            return {suite_name: self.results.get(suite_name, [])}
        return self.results

    def print_summary(self) -> None:
        """Print a summary of all evaluation results."""
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)

        total_benchmarks = 0
        total_successful = 0
        total_time = 0.0

        for suite_name, results in self.results.items():
            successful = sum(1 for r in results if r.success)
            suite_time = sum(r.execution_time for r in results)

            total_benchmarks += len(results)
            total_successful += successful
            total_time += suite_time

            print(f"\n{suite_name}:")
            print(f"  Benchmarks: {len(results)}")
            print(f"  Successful: {successful}")
            print(f"  Success rate: {successful/len(results):.1%}")
            print(f"  Total time: {suite_time:.2f}s")
            print(f"  Avg time: {suite_time/len(results):.2f}s")

        print(f"\nOVERALL:")
        print(f"  Total benchmarks: {total_benchmarks}")
        print(f"  Total successful: {total_successful}")
        print(f"  Overall success rate: {total_successful/total_benchmarks:.1%}")
        print(f"  Total time: {total_time:.2f}s")
        print("=" * 60)

    def print_detailed_results(self, suite_name: Optional[str] = None) -> None:
        """Print detailed results for each benchmark.

        Args:
            suite_name: Optional suite name to filter results
        """
        results_to_print = self.results
        if suite_name:
            results_to_print = {suite_name: self.results.get(suite_name, [])}

        for suite_name, results in results_to_print.items():
            print(f"\n{'=' * 60}")
            print(f"DETAILED RESULTS: {suite_name}")
            print("=" * 60)

            for result in results:
                status = "✓ PASS" if result.success else "✗ FAIL"
                print(f"\n{status} {result.benchmark_name}")
                print(f"Task: {result.task[:80]}...")
                print(f"Time: {result.execution_time:.2f}s")

                if result.error:
                    print(f"Error: {result.error}")
                else:
                    print(f"Response: {result.response[:200]}...")

                print("-" * 60)
