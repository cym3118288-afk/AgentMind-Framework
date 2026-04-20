"""Profiling script for core modules to identify optimization opportunities."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import asyncio  # noqa: E402
import cProfile  # noqa: E402
import io  # noqa: E402
import pstats  # noqa: E402
import time  # noqa: E402

from agentmind import Agent, AgentMind, Message  # noqa: E402
from agentmind.core.types import CollaborationStrategy  # noqa: E402


def profile_agent_creation():
    """Profile agent creation."""
    for i in range(100):
        Agent(name=f"agent_{i}", role="analyst")


def profile_message_processing():
    """Profile message processing."""
    agent = Agent(name="test_agent", role="analyst")

    async def process_messages():
        for i in range(50):
            msg = Message(content=f"Message {i}", sender="user")
            await agent.process_message(msg)

    asyncio.run(process_messages())


def profile_memory_operations():
    """Profile memory operations."""
    agent = Agent(name="test_agent", role="analyst")

    # Add many messages
    for i in range(100):
        agent.memory.append(Message(content=f"Message {i}", sender="user"))

    # Retrieve recent memory multiple times
    for _ in range(100):
        agent.get_recent_memory(limit=10)


def profile_agentmind_collaboration():
    """Profile multi - agent collaboration."""

    async def run_collaboration():
        mind = AgentMind(strategy=CollaborationStrategy.BROADCAST)

        # Add multiple agents
        for i in range(5):
            agent = Agent(name=f"agent_{i}", role="analyst")
            mind.add_agent(agent)

        # Run collaboration
        result = await mind.start_collaboration("Test task", max_rounds=3)
        return result

    asyncio.run(run_collaboration())


def profile_broadcast():
    """Profile message broadcasting."""

    async def run_broadcast():
        mind = AgentMind()

        # Add agents
        for i in range(10):
            agent = Agent(name=f"agent_{i}", role="analyst")
            mind.add_agent(agent)

        # Broadcast messages
        for i in range(10):
            msg = Message(content=f"Broadcast {i}", sender="system")
            await mind.broadcast_message(msg, exclude_sender=False)

    asyncio.run(run_broadcast())


def profile_session_save_load():
    """Profile session save / load operations."""
    import tempfile

    mind = AgentMind()
    for i in range(5):
        agent = Agent(name=f"agent_{i}", role="analyst")
        mind.add_agent(agent)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save session
        for i in range(10):
            mind.save_session(f"session_{i}", save_dir=tmpdir)

        # Load sessions
        for i in range(10):
            mind.load_session(f"session_{i}", save_dir=tmpdir)

        # List sessions
        for _ in range(10):
            mind.list_sessions(save_dir=tmpdir)


def run_profile(func, name):
    """Run profiling on a function."""
    print(f"\n{'=' * 60}")
    print(f"Profiling: {name}")
    print("=" * 60)

    profiler = cProfile.Profile()

    start_time = time.time()
    profiler.enable()
    func()
    profiler.disable()
    end_time = time.time()

    # Print stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(20)  # Top 20 functions

    print(s.getvalue())
    print(f"\nTotal execution time: {end_time - start_time:.4f} seconds")


def benchmark_operations():
    """Benchmark key operations."""
    print("\n" + "=" * 60)
    print("BENCHMARKING KEY OPERATIONS")
    print("=" * 60)

    # Agent creation
    start = time.time()
    for i in range(1000):
        Agent(name=f"agent_{i}", role="analyst")
    agent_creation_time = time.time() - start
    print(
        f"Agent creation (1000x): {agent_creation_time:.4f}s ({agent_creation_time / 1000 * 1000:.2f}ms each)"
    )

    # Message creation
    start = time.time()
    for i in range(1000):
        Message(content=f"Message {i}", sender="user")
    message_creation_time = time.time() - start
    print(
        f"Message creation (1000x): {message_creation_time:.4f}s ({message_creation_time / 1000 * 1000:.2f}ms each)"
    )

    # Memory retrieval
    agent = Agent(name="test", role="analyst")
    for i in range(100):
        agent.memory.append(Message(content=f"Msg {i}", sender="user"))

    start = time.time()
    for _ in range(1000):
        agent.get_recent_memory(limit=10)
    memory_retrieval_time = time.time() - start
    print(
        f"Memory retrieval (1000x): {memory_retrieval_time:.4f}s ({memory_retrieval_time / 1000 * 1000:.2f}ms each)"
    )

    # AgentMind creation
    start = time.time()
    for i in range(100):
        AgentMind()
    agentmind_creation_time = time.time() - start
    print(
        f"AgentMind creation (100x): {agentmind_creation_time:.4f}s ({agentmind_creation_time / 100 * 1000:.2f}ms each)"
    )


if __name__ == "__main__":
    print("AgentMind Core Module Profiling")
    print("=" * 60)

    # Run benchmarks first
    benchmark_operations()

    # Profile individual operations
    run_profile(profile_agent_creation, "Agent Creation (100x)")
    run_profile(profile_message_processing, "Message Processing (50x)")
    run_profile(profile_memory_operations, "Memory Operations")
    run_profile(profile_agentmind_collaboration, "Multi - Agent Collaboration")
    run_profile(profile_broadcast, "Message Broadcasting")
    run_profile(profile_session_save_load, "Session Save / Load")

    print("\n" + "=" * 60)
    print("PROFILING COMPLETE")
    print("=" * 60)
    print("\nOptimization recommendations:")
    print("1. Check for repeated object creation in hot paths")
    print("2. Look for unnecessary list copies or iterations")
    print("3. Consider caching frequently accessed data")
    print("4. Optimize JSON serialization / deserialization")
    print("5. Use slots for frequently created objects")
