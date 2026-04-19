"""Metrics collection for evaluation."""

from collections import defaultdict
from typing import Any, Dict, List

from .benchmark import BenchmarkResult


class MetricsCollector:
    """Collects and analyzes metrics from benchmark results.

    Example:
        >>> collector = MetricsCollector()
        >>> collector.add_results(results)
        >>> metrics = collector.get_metrics()
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self.results: List[BenchmarkResult] = []
        self.metrics_by_suite: Dict[str, List[BenchmarkResult]] = defaultdict(list)

    def add_results(self, results: List[BenchmarkResult], suite_name: str = "default") -> None:
        """Add benchmark results for analysis.

        Args:
            results: List of BenchmarkResults
            suite_name: Name of the suite these results belong to
        """
        self.results.extend(results)
        self.metrics_by_suite[suite_name].extend(results)

    def get_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive metrics from all results.

        Returns:
            Dictionary of metrics
        """
        if not self.results:
            return {}

        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful

        execution_times = [r.execution_time for r in self.results]
        response_lengths = [r.metrics.get("response_length", 0) for r in self.results]

        return {
            "total_benchmarks": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total,
            "total_time": sum(execution_times),
            "avg_time": sum(execution_times) / total,
            "min_time": min(execution_times),
            "max_time": max(execution_times),
            "avg_response_length": sum(response_lengths) / total,
            "errors": [r.error for r in self.results if r.error],
        }

    def get_metrics_by_suite(self, suite_name: str) -> Dict[str, Any]:
        """Get metrics for a specific suite.

        Args:
            suite_name: Name of the suite

        Returns:
            Dictionary of metrics for the suite
        """
        results = self.metrics_by_suite.get(suite_name, [])
        if not results:
            return {}

        total = len(results)
        successful = sum(1 for r in results if r.success)
        execution_times = [r.execution_time for r in results]

        return {
            "suite_name": suite_name,
            "total_benchmarks": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total,
            "total_time": sum(execution_times),
            "avg_time": sum(execution_times) / total,
        }

    def get_comparative_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get comparative metrics across all suites.

        Returns:
            Dictionary mapping suite names to their metrics
        """
        return {
            suite_name: self.get_metrics_by_suite(suite_name)
            for suite_name in self.metrics_by_suite.keys()
        }

    def get_failure_analysis(self) -> Dict[str, Any]:
        """Analyze failures to identify patterns.

        Returns:
            Dictionary with failure analysis
        """
        failures = [r for r in self.results if not r.success]

        if not failures:
            return {"total_failures": 0, "failure_types": {}}

        failure_types = defaultdict(int)
        for failure in failures:
            if failure.error:
                if "Timeout" in failure.error:
                    failure_types["timeout"] += 1
                elif "Exception" in failure.error:
                    failure_types["exception"] += 1
                else:
                    failure_types["other"] += 1
            else:
                failure_types["evaluation_failed"] += 1

        return {
            "total_failures": len(failures),
            "failure_types": dict(failure_types),
            "failed_benchmarks": [f.benchmark_name for f in failures],
        }

    def get_performance_distribution(self) -> Dict[str, int]:
        """Get distribution of execution times.

        Returns:
            Dictionary with time buckets and counts
        """
        buckets = {
            "0-1s": 0,
            "1-5s": 0,
            "5-10s": 0,
            "10-30s": 0,
            "30s+": 0,
        }

        for result in self.results:
            time = result.execution_time
            if time < 1:
                buckets["0-1s"] += 1
            elif time < 5:
                buckets["1-5s"] += 1
            elif time < 10:
                buckets["5-10s"] += 1
            elif time < 30:
                buckets["10-30s"] += 1
            else:
                buckets["30s+"] += 1

        return buckets
