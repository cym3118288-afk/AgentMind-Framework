"""Developer tools for debugging and profiling AgentMind.

Provides interactive debugging, profiling utilities, and development helpers.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.types import Message
from ..core.agent import Agent
from ..core.mind import AgentMind


@dataclass
class DebugEvent:
    """Debug event for tracking agent behavior."""

    timestamp: datetime
    event_type: str
    agent_name: str
    data: Dict[str, Any]
    duration: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class DebugMode:
    """Debug mode for detailed logging and inspection."""

    def __init__(self, enabled: bool = True):
        """Initialize debug mode.

        Args:
            enabled: Whether debug mode is enabled
        """
        self.enabled = enabled
        self.events: List[DebugEvent] = []
        self._start_times: Dict[str, float] = {}

    def log_event(
        self,
        event_type: str,
        agent_name: str,
        data: Dict[str, Any],
        duration: Optional[float] = None,
    ) -> None:
        """Log a debug event.

        Args:
            event_type: Type of event (message, tool_call, etc.)
            agent_name: Name of the agent
            data: Event data
            duration: Optional duration in seconds
        """
        if not self.enabled:
            return

        event = DebugEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            agent_name=agent_name,
            data=data,
            duration=duration,
        )
        self.events.append(event)

    def start_timer(self, key: str) -> None:
        """Start a timer for an operation."""
        if self.enabled:
            self._start_times[key] = time.time()

    def end_timer(self, key: str) -> Optional[float]:
        """End a timer and return duration."""
        if not self.enabled or key not in self._start_times:
            return None

        duration = time.time() - self._start_times[key]
        del self._start_times[key]
        return duration

    def get_events(
        self,
        event_type: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> List[DebugEvent]:
        """Get filtered debug events.

        Args:
            event_type: Filter by event type
            agent_name: Filter by agent name

        Returns:
            List of matching events
        """
        events = self.events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]

        return events

    def export_events(self, filepath: str) -> None:
        """Export events to JSON file.

        Args:
            filepath: Path to output file
        """
        with open(filepath, 'w') as f:
            json.dump([e.to_dict() for e in self.events], f, indent=2)

    def clear(self) -> None:
        """Clear all events."""
        self.events.clear()
        self._start_times.clear()

    def print_summary(self) -> None:
        """Print summary of debug events."""
        if not self.events:
            print("No debug events recorded.")
            return

        print("\n=== Debug Summary ===")
        print(f"Total events: {len(self.events)}")

        # Group by event type
        by_type = {}
        for event in self.events:
            by_type.setdefault(event.event_type, []).append(event)

        print("\nEvents by type:")
        for event_type, events in by_type.items():
            print(f"  {event_type}: {len(events)}")

        # Group by agent
        by_agent = {}
        for event in self.events:
            by_agent.setdefault(event.agent_name, []).append(event)

        print("\nEvents by agent:")
        for agent_name, events in by_agent.items():
            print(f"  {agent_name}: {len(events)}")

        # Duration stats
        timed_events = [e for e in self.events if e.duration is not None]
        if timed_events:
            total_duration = sum(e.duration for e in timed_events)
            avg_duration = total_duration / len(timed_events)
            print(f"\nTiming:")
            print(f"  Total duration: {total_duration:.3f}s")
            print(f"  Average duration: {avg_duration:.3f}s")

        print("=" * 30 + "\n")


class InteractiveDebugger:
    """Interactive debugger for agent conversations."""

    def __init__(self, agent_mind: AgentMind):
        """Initialize interactive debugger.

        Args:
            agent_mind: AgentMind instance to debug
        """
        self.mind = agent_mind
        self.debug_mode = DebugMode(enabled=True)
        self.breakpoints: List[Callable] = []

    def add_breakpoint(self, condition: Callable[[Message], bool]) -> None:
        """Add a breakpoint condition.

        Args:
            condition: Function that returns True to break

        Example:
            >>> debugger.add_breakpoint(lambda msg: "error" in msg.content.lower())
        """
        self.breakpoints.append(condition)

    def should_break(self, message: Message) -> bool:
        """Check if any breakpoint condition is met."""
        return any(bp(message) for bp in self.breakpoints)

    async def step_through(
        self,
        task: str,
        max_rounds: int = 10,
    ) -> None:
        """Step through collaboration interactively.

        Args:
            task: Task to collaborate on
            max_rounds: Maximum collaboration rounds
        """
        print(f"\n=== Interactive Debug Session ===")
        print(f"Task: {task}")
        print(f"Agents: {[a.name for a in self.mind.agents]}")
        print("Commands: (c)ontinue, (s)tep, (i)nspect, (q)uit\n")

        round_num = 0
        while round_num < max_rounds:
            print(f"\n--- Round {round_num + 1} ---")

            # Get user input
            command = input("Debug> ").strip().lower()

            if command == 'q':
                print("Exiting debug session.")
                break
            elif command == 'i':
                self._inspect_state()
                continue
            elif command == 's' or command == 'c':
                # Execute one round
                # Note: This is simplified - actual implementation would need
                # to integrate with AgentMind's collaboration loop
                print("Executing round...")
                round_num += 1
            else:
                print("Unknown command. Use (c)ontinue, (s)tep, (i)nspect, or (q)uit")

    def _inspect_state(self) -> None:
        """Inspect current state of agents."""
        print("\n=== Current State ===")
        for agent in self.mind.agents:
            print(f"\nAgent: {agent.name}")
            print(f"  Role: {agent.role}")
            print(f"  Active: {agent.is_active}")
            print(f"  Memory size: {len(agent.memory)}")
            if agent.memory:
                print(f"  Last message: {agent.memory[-1].content[:50]}...")


class BenchmarkRunner:
    """Run benchmarks on agent performance."""

    def __init__(self):
        """Initialize benchmark runner."""
        self.results: List[Dict[str, Any]] = []

    async def benchmark_agent(
        self,
        agent: Agent,
        messages: List[Message],
        iterations: int = 10,
    ) -> Dict[str, Any]:
        """Benchmark agent performance.

        Args:
            agent: Agent to benchmark
            messages: Messages to process
            iterations: Number of iterations

        Returns:
            Benchmark results
        """
        durations = []

        for i in range(iterations):
            start_time = time.time()

            for message in messages:
                await agent.process_message(message)

            duration = time.time() - start_time
            durations.append(duration)

        results = {
            "agent_name": agent.name,
            "iterations": iterations,
            "messages_per_iteration": len(messages),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_duration": sum(durations),
        }

        self.results.append(results)
        return results

    async def benchmark_collaboration(
        self,
        mind: AgentMind,
        task: str,
        iterations: int = 5,
        max_rounds: int = 3,
    ) -> Dict[str, Any]:
        """Benchmark collaboration performance.

        Args:
            mind: AgentMind instance
            task: Task to collaborate on
            iterations: Number of iterations
            max_rounds: Max rounds per iteration

        Returns:
            Benchmark results
        """
        durations = []
        round_counts = []

        for i in range(iterations):
            start_time = time.time()

            result = await mind.collaborate(task, max_rounds=max_rounds)

            duration = time.time() - start_time
            durations.append(duration)

            # Count actual rounds (simplified)
            round_counts.append(max_rounds)

        results = {
            "task": task,
            "iterations": iterations,
            "max_rounds": max_rounds,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "avg_rounds": sum(round_counts) / len(round_counts),
        }

        self.results.append(results)
        return results

    def print_results(self) -> None:
        """Print benchmark results."""
        if not self.results:
            print("No benchmark results available.")
            return

        print("\n=== Benchmark Results ===\n")

        for i, result in enumerate(self.results, 1):
            print(f"Benchmark {i}:")
            for key, value in result.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")
            print()

    def export_results(self, filepath: str) -> None:
        """Export results to JSON file.

        Args:
            filepath: Path to output file
        """
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)


class MemoryLeakDetector:
    """Detect memory leaks in agent systems."""

    def __init__(self):
        """Initialize memory leak detector."""
        self.snapshots: List[Dict[str, Any]] = []

    def take_snapshot(self, label: str, agents: List[Agent]) -> None:
        """Take a memory snapshot.

        Args:
            label: Label for this snapshot
            agents: List of agents to snapshot
        """
        import sys

        snapshot = {
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "agents": {},
        }

        for agent in agents:
            snapshot["agents"][agent.name] = {
                "memory_size": len(agent.memory),
                "memory_bytes": sum(
                    sys.getsizeof(m.content) for m in agent.memory
                ),
                "is_active": agent.is_active,
            }

        self.snapshots.append(snapshot)

    def analyze(self) -> Dict[str, Any]:
        """Analyze snapshots for memory leaks.

        Returns:
            Analysis results
        """
        if len(self.snapshots) < 2:
            return {"error": "Need at least 2 snapshots to analyze"}

        analysis = {
            "snapshots": len(self.snapshots),
            "agents": {},
        }

        # Get all agent names
        all_agents = set()
        for snapshot in self.snapshots:
            all_agents.update(snapshot["agents"].keys())

        # Analyze each agent
        for agent_name in all_agents:
            memory_sizes = []
            memory_bytes = []

            for snapshot in self.snapshots:
                if agent_name in snapshot["agents"]:
                    agent_data = snapshot["agents"][agent_name]
                    memory_sizes.append(agent_data["memory_size"])
                    memory_bytes.append(agent_data["memory_bytes"])

            if memory_sizes:
                analysis["agents"][agent_name] = {
                    "memory_growth": memory_sizes[-1] - memory_sizes[0],
                    "bytes_growth": memory_bytes[-1] - memory_bytes[0],
                    "avg_memory_size": sum(memory_sizes) / len(memory_sizes),
                    "potential_leak": memory_sizes[-1] > memory_sizes[0] * 2,
                }

        return analysis

    def print_analysis(self) -> None:
        """Print memory leak analysis."""
        analysis = self.analyze()

        if "error" in analysis:
            print(f"Error: {analysis['error']}")
            return

        print("\n=== Memory Leak Analysis ===\n")
        print(f"Snapshots analyzed: {analysis['snapshots']}\n")

        for agent_name, data in analysis["agents"].items():
            print(f"Agent: {agent_name}")
            print(f"  Memory growth: {data['memory_growth']} messages")
            print(f"  Bytes growth: {data['bytes_growth']} bytes")
            print(f"  Average memory: {data['avg_memory_size']:.1f} messages")

            if data["potential_leak"]:
                print("  ⚠️  POTENTIAL MEMORY LEAK DETECTED")
            print()


def setup_development_environment() -> Dict[str, Any]:
    """Setup development environment with debugging tools.

    Returns:
        Dictionary of development tools
    """
    print("Setting up AgentMind development environment...")

    tools = {
        "debug_mode": DebugMode(enabled=True),
        "benchmark_runner": BenchmarkRunner(),
        "memory_detector": MemoryLeakDetector(),
    }

    print("✓ Debug mode enabled")
    print("✓ Benchmark runner ready")
    print("✓ Memory leak detector ready")
    print("\nDevelopment environment ready!")

    return tools
