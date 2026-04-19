"""Markdown report generator for evaluation results."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .benchmark import BenchmarkResult
from .metrics import MetricsCollector


class MarkdownReporter:
    """Generates Markdown reports from evaluation results.

    Example:
        >>> reporter = MarkdownReporter()
        >>> reporter.add_results(results, "GAIA Subset")
        >>> reporter.generate_report("benchmarks/report.md")
    """

    def __init__(self):
        """Initialize the reporter."""
        self.collector = MetricsCollector()
        self.suite_names: List[str] = []

    def add_results(self, results: List[BenchmarkResult], suite_name: str) -> None:
        """Add results for a benchmark suite.

        Args:
            results: List of BenchmarkResults
            suite_name: Name of the suite
        """
        self.collector.add_results(results, suite_name)
        if suite_name not in self.suite_names:
            self.suite_names.append(suite_name)

    def generate_report(self, output_path: str) -> None:
        """Generate a Markdown report and save to file.

        Args:
            output_path: Path to save the report
        """
        report = self._build_report()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(report, encoding="utf-8")

        print(f"Report generated: {output_path}")

    def _build_report(self) -> str:
        """Build the Markdown report content."""
        lines = []

        # Header
        lines.append("# AgentMind Evaluation Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Overall metrics
        lines.append("## Overall Performance")
        lines.append("")
        overall_metrics = self.collector.get_metrics()
        lines.append(f"- **Total Benchmarks:** {overall_metrics.get('total_benchmarks', 0)}")
        lines.append(f"- **Successful:** {overall_metrics.get('successful', 0)}")
        lines.append(f"- **Failed:** {overall_metrics.get('failed', 0)}")
        lines.append(f"- **Success Rate:** {overall_metrics.get('success_rate', 0):.1%}")
        lines.append(f"- **Total Time:** {overall_metrics.get('total_time', 0):.2f}s")
        lines.append(f"- **Average Time:** {overall_metrics.get('avg_time', 0):.2f}s")
        lines.append("")

        # Performance distribution
        lines.append("## Performance Distribution")
        lines.append("")
        distribution = self.collector.get_performance_distribution()
        lines.append("| Time Range | Count |")
        lines.append("|------------|-------|")
        for bucket, count in distribution.items():
            lines.append(f"| {bucket} | {count} |")
        lines.append("")

        # Suite-by-suite results
        lines.append("## Results by Suite")
        lines.append("")

        comparative = self.collector.get_comparative_metrics()
        for suite_name in self.suite_names:
            metrics = comparative.get(suite_name, {})
            lines.append(f"### {suite_name}")
            lines.append("")
            lines.append(f"- **Benchmarks:** {metrics.get('total_benchmarks', 0)}")
            lines.append(f"- **Successful:** {metrics.get('successful', 0)}")
            lines.append(f"- **Success Rate:** {metrics.get('success_rate', 0):.1%}")
            lines.append(f"- **Total Time:** {metrics.get('total_time', 0):.2f}s")
            lines.append(f"- **Average Time:** {metrics.get('avg_time', 0):.2f}s")
            lines.append("")

        # Failure analysis
        lines.append("## Failure Analysis")
        lines.append("")
        failure_analysis = self.collector.get_failure_analysis()
        lines.append(f"**Total Failures:** {failure_analysis.get('total_failures', 0)}")
        lines.append("")

        if failure_analysis.get("failure_types"):
            lines.append("### Failure Types")
            lines.append("")
            lines.append("| Type | Count |")
            lines.append("|------|-------|")
            for ftype, count in failure_analysis["failure_types"].items():
                lines.append(f"| {ftype} | {count} |")
            lines.append("")

        if failure_analysis.get("failed_benchmarks"):
            lines.append("### Failed Benchmarks")
            lines.append("")
            for benchmark in failure_analysis["failed_benchmarks"]:
                lines.append(f"- {benchmark}")
            lines.append("")

        # Detailed results
        lines.append("## Detailed Results")
        lines.append("")

        for suite_name in self.suite_names:
            results = self.collector.metrics_by_suite.get(suite_name, [])
            lines.append(f"### {suite_name}")
            lines.append("")
            lines.append("| Benchmark | Status | Time | Response Length |")
            lines.append("|-----------|--------|------|-----------------|")

            for result in results:
                status = "✓ Pass" if result.success else "✗ Fail"
                time_str = f"{result.execution_time:.2f}s"
                length = result.metrics.get("response_length", 0)
                lines.append(f"| {result.benchmark_name} | {status} | {time_str} | {length} |")

            lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        lines.extend(self._generate_recommendations(overall_metrics, failure_analysis))
        lines.append("")

        return "\n".join(lines)

    def _generate_recommendations(
        self,
        metrics: Dict[str, Any],
        failure_analysis: Dict[str, Any],
    ) -> List[str]:
        """Generate recommendations based on results."""
        recommendations = []

        success_rate = metrics.get("success_rate", 0)
        avg_time = metrics.get("avg_time", 0)
        failure_types = failure_analysis.get("failure_types", {})

        if success_rate < 0.7:
            recommendations.append("- **Low success rate detected.** Consider:")
            recommendations.append("  - Reviewing agent prompts and roles")
            recommendations.append("  - Increasing max_rounds for collaboration")
            recommendations.append("  - Adding more specialized agents")

        if avg_time > 10:
            recommendations.append("- **High average execution time.** Consider:")
            recommendations.append("  - Using faster LLM models")
            recommendations.append("  - Optimizing collaboration strategy")
            recommendations.append("  - Implementing caching")

        if failure_types.get("timeout", 0) > 0:
            recommendations.append("- **Timeouts detected.** Consider:")
            recommendations.append("  - Increasing timeout values")
            recommendations.append("  - Simplifying complex tasks")
            recommendations.append("  - Using streaming for long responses")

        if not recommendations:
            recommendations.append("- Performance is good. Continue current approach.")
            recommendations.append("- Consider adding more challenging benchmarks.")

        return recommendations

    def print_report(self) -> None:
        """Print the report to console."""
        print(self._build_report())
