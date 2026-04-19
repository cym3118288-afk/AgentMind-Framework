"""Benchmark definitions and execution."""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from ..core.mind import AgentMind


@dataclass
class BenchmarkResult:
    """Result from running a benchmark."""

    benchmark_name: str
    task: str
    response: str
    success: bool
    execution_time: float
    metrics: Dict[str, Any]
    error: Optional[str] = None


class Benchmark:
    """A single benchmark test case."""

    def __init__(
        self,
        name: str,
        task: str,
        expected_output: Optional[str] = None,
        evaluation_fn: Optional[Callable] = None,
        timeout: float = 60.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a benchmark.

        Args:
            name: Benchmark name
            task: Task description for agents
            expected_output: Optional expected output for comparison
            evaluation_fn: Optional custom evaluation function
            timeout: Timeout in seconds
            metadata: Optional metadata
        """
        self.name = name
        self.task = task
        self.expected_output = expected_output
        self.evaluation_fn = evaluation_fn
        self.timeout = timeout
        self.metadata = metadata or {}

    async def run(self, mind: AgentMind, max_rounds: int = 3) -> BenchmarkResult:
        """Run the benchmark on an AgentMind instance.

        Args:
            mind: AgentMind instance to test
            max_rounds: Maximum collaboration rounds

        Returns:
            BenchmarkResult with execution details
        """
        start_time = time.time()
        error = None
        response = ""
        success = False

        try:
            # Run with timeout
            response = await asyncio.wait_for(
                mind.collaborate(self.task, max_rounds=max_rounds),
                timeout=self.timeout,
            )

            # Evaluate success
            if self.evaluation_fn:
                success = self.evaluation_fn(response, self.expected_output)
            elif self.expected_output:
                success = self._default_evaluation(response, self.expected_output)
            else:
                success = bool(response and len(response) > 0)

        except asyncio.TimeoutError:
            error = f"Timeout after {self.timeout}s"
            success = False
        except Exception as e:
            error = str(e)
            success = False

        execution_time = time.time() - start_time

        return BenchmarkResult(
            benchmark_name=self.name,
            task=self.task,
            response=response,
            success=success,
            execution_time=execution_time,
            metrics={
                "response_length": len(response),
                "timeout": self.timeout,
                "max_rounds": max_rounds,
            },
            error=error,
        )

    def _default_evaluation(self, response: str, expected: str) -> bool:
        """Default evaluation: check if key terms from expected are in response."""
        if not response or not expected:
            return False

        # Simple keyword matching
        expected_keywords = set(expected.lower().split())
        response_lower = response.lower()

        matches = sum(1 for keyword in expected_keywords if keyword in response_lower)
        return matches / len(expected_keywords) > 0.5


class BenchmarkSuite:
    """Collection of benchmarks for comprehensive evaluation."""

    def __init__(self, name: str, description: str = ""):
        """Initialize a benchmark suite.

        Args:
            name: Suite name
            description: Suite description
        """
        self.name = name
        self.description = description
        self.benchmarks: List[Benchmark] = []

    def add_benchmark(self, benchmark: Benchmark) -> None:
        """Add a benchmark to the suite.

        Args:
            benchmark: Benchmark to add
        """
        self.benchmarks.append(benchmark)

    async def run_all(
        self,
        mind: AgentMind,
        max_rounds: int = 3,
        parallel: bool = False,
    ) -> List[BenchmarkResult]:
        """Run all benchmarks in the suite.

        Args:
            mind: AgentMind instance to test
            max_rounds: Maximum collaboration rounds
            parallel: Whether to run benchmarks in parallel

        Returns:
            List of BenchmarkResults
        """
        if parallel:
            tasks = [b.run(mind, max_rounds) for b in self.benchmarks]
            return await asyncio.gather(*tasks)
        else:
            results = []
            for benchmark in self.benchmarks:
                result = await benchmark.run(mind, max_rounds)
                results.append(result)
            return results

    def get_summary(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Get summary statistics from results.

        Args:
            results: List of benchmark results

        Returns:
            Summary statistics dictionary
        """
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        total_time = sum(r.execution_time for r in results)
        avg_time = total_time / total if total > 0 else 0

        return {
            "suite_name": self.name,
            "total_benchmarks": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "total_time": total_time,
            "avg_time": avg_time,
            "results": results,
        }


def create_gaia_subset() -> BenchmarkSuite:
    """Create a subset of GAIA-inspired benchmarks.

    Returns:
        BenchmarkSuite with GAIA-style tasks
    """
    suite = BenchmarkSuite(
        name="GAIA Subset",
        description="General AI Assistant benchmarks inspired by GAIA",
    )

    # Reasoning tasks
    suite.add_benchmark(Benchmark(
        name="logical_reasoning",
        task="If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly? Explain your reasoning.",
        expected_output="cannot conclude logic reasoning",
    ))

    # Math tasks
    suite.add_benchmark(Benchmark(
        name="math_problem",
        task="A train travels 120 km in 2 hours. If it maintains the same speed, how far will it travel in 5 hours?",
        expected_output="300 km speed distance",
    ))

    # Information retrieval
    suite.add_benchmark(Benchmark(
        name="information_synthesis",
        task="Explain the difference between machine learning and deep learning in simple terms.",
        expected_output="neural networks layers data learning",
    ))

    # Multi-step reasoning
    suite.add_benchmark(Benchmark(
        name="multi_step_reasoning",
        task="If a store offers 20% off on all items and then an additional 10% off the discounted price, what is the total discount percentage?",
        expected_output="28% discount calculation",
    ))

    # Creative problem solving
    suite.add_benchmark(Benchmark(
        name="creative_problem",
        task="Design a simple system to help elderly people remember to take their medication on time.",
        expected_output="reminder notification schedule medication",
    ))

    return suite


def create_agent_bench_subset() -> BenchmarkSuite:
    """Create a subset of AgentBench-inspired benchmarks.

    Returns:
        BenchmarkSuite with AgentBench-style tasks
    """
    suite = BenchmarkSuite(
        name="AgentBench Subset",
        description="Agent capability benchmarks inspired by AgentBench",
    )

    # Code generation
    suite.add_benchmark(Benchmark(
        name="code_generation",
        task="Write a Python function that finds the longest common subsequence of two strings.",
        expected_output="def function string subsequence",
    ))

    # Planning
    suite.add_benchmark(Benchmark(
        name="planning_task",
        task="Create a step-by-step plan to organize a small team hackathon event.",
        expected_output="plan steps team venue schedule",
    ))

    # Decision making
    suite.add_benchmark(Benchmark(
        name="decision_making",
        task="You have $10,000 to invest. Compare the pros and cons of investing in stocks vs. bonds vs. real estate.",
        expected_output="risk return liquidity investment",
    ))

    # Tool use simulation
    suite.add_benchmark(Benchmark(
        name="tool_use",
        task="Describe the steps you would take to analyze a CSV file containing sales data and create a summary report.",
        expected_output="read data analyze calculate report",
    ))

    # Collaboration
    suite.add_benchmark(Benchmark(
        name="collaboration",
        task="How would you coordinate a team of 3 people to research, write, and edit a technical blog post?",
        expected_output="assign roles coordinate review workflow",
    ))

    return suite


def create_custom_suite() -> BenchmarkSuite:
    """Create a custom benchmark suite for AgentMind-specific features.

    Returns:
        BenchmarkSuite with custom tasks
    """
    suite = BenchmarkSuite(
        name="AgentMind Custom",
        description="Custom benchmarks for AgentMind features",
    )

    # Multi-agent collaboration
    suite.add_benchmark(Benchmark(
        name="multi_agent_synthesis",
        task="Analyze the pros and cons of remote work from multiple perspectives: employee, employer, and society.",
        expected_output="perspective advantages disadvantages balance",
    ))

    # Debate and consensus
    suite.add_benchmark(Benchmark(
        name="debate_consensus",
        task="Should AI development be regulated? Present arguments for and against, then reach a balanced conclusion.",
        expected_output="regulation safety innovation balance conclusion",
    ))

    # Complex reasoning
    suite.add_benchmark(Benchmark(
        name="complex_reasoning",
        task="A company's revenue increased by 50% but profits decreased by 10%. What could explain this situation?",
        expected_output="costs expenses margins efficiency",
    ))

    # Creative synthesis
    suite.add_benchmark(Benchmark(
        name="creative_synthesis",
        task="Combine concepts from biology and computer science to propose an innovative solution for data storage.",
        expected_output="DNA biological storage innovation",
    ))

    # Iterative improvement
    suite.add_benchmark(Benchmark(
        name="iterative_improvement",
        task="Write a product description for a smart water bottle, then critique it and provide an improved version.",
        expected_output="features benefits improved version",
    ))

    return suite
