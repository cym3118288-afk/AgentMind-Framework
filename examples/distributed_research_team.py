"""
Distributed Research Team Example
Demonstrates distributed agent execution using Ray or Celery
"""

from typing import List, Dict, Any


def create_research_agents() -> List[Dict[str, Any]]:
    """Create configuration for research team agents"""
    return [
        {
            "name": "DataCollector",
            "role": "data_collection",
            "system_prompt": "You collect and organize data from various sources. Be thorough and systematic.",
        },
        {
            "name": "Analyst",
            "role": "analysis",
            "system_prompt": "You analyze data and identify patterns, trends, and insights.",
        },
        {
            "name": "Synthesizer",
            "role": "synthesis",
            "system_prompt": "You synthesize information from multiple sources into coherent summaries.",
        },
        {
            "name": "Validator",
            "role": "validation",
            "system_prompt": "You validate findings and check for accuracy and consistency.",
        },
    ]


def example_ray_distributed():
    """Example using Ray backend for distributed execution"""
    print("=" * 80)
    print("DISTRIBUTED RESEARCH TEAM - RAY BACKEND")
    print("=" * 80)

    try:
        from agentmind.distributed import create_distributed_mind, RAY_AVAILABLE

        if not RAY_AVAILABLE:
            print("Ray not available. Install with: pip install ray")
            return

        # Initialize distributed mind
        print("\nInitializing Ray distributed mind...")
        mind = create_distributed_mind("ray", num_cpus=4)

        # Create agents
        agents = create_research_agents()
        llm_config = {"model": "llama3.2", "temperature": 0.7}

        # Research topics
        topics = [
            "What are the latest developments in quantum computing?",
            "How is AI being used in healthcare?",
            "What are the environmental impacts of cryptocurrency mining?",
            "What are the trends in renewable energy adoption?",
        ]

        print(f"\nResearching {len(topics)} topics in parallel...")
        print("-" * 80)

        # Execute in parallel
        results = mind.parallel_execute(agents, topics[0], llm_config)

        print("\nResults:")
        for i, result in enumerate(results):
            if result.get("success"):
                print(f"\n{i + 1}. {result['agent']}:")
                print(f"   {result['result'][:200]}...")
            else:
                print(f"\n{i + 1}. {result['agent']}: ERROR - {result.get('error')}")

        # Map - reduce example
        print("\n" + "=" * 80)
        print("MAP - REDUCE EXAMPLE")
        print("=" * 80)

        def combine_results(results: List[Dict]) -> str:
            """Combine results from multiple agents"""
            successful = [r for r in results if r.get("success")]
            combined = "\n\n".join([r["result"] for r in successful])
            return f"Combined research from {len(successful)} agents:\n\n{combined}"

        print("\nExecuting map - reduce across all topics...")
        final_result = mind.map_reduce(agents, topics, llm_config, combine_results)

        print("\nFinal Combined Result:")
        print(final_result[:500] + "...")

        # Cleanup
        mind.shutdown()
        print("\n✓ Ray distributed execution completed successfully")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


def example_celery_distributed():
    """Example using Celery backend for distributed execution"""
    print("=" * 80)
    print("DISTRIBUTED RESEARCH TEAM - CELERY BACKEND")
    print("=" * 80)

    try:
        from agentmind.distributed import create_distributed_mind, CELERY_AVAILABLE

        if not CELERY_AVAILABLE:
            print("Celery not available. Install with: pip install celery redis")
            return

        # Initialize distributed mind
        print("\nInitializing Celery distributed mind...")
        print("Note: Make sure Redis is running and Celery workers are started")
        print("Start workers with: celery -A agentmind.distributed.celery_backend worker")

        mind = create_distributed_mind(
            "celery",
            broker_url="redis://localhost:6379 / 0",
            backend_url="redis://localhost:6379 / 1",
        )

        # Create agents
        agents = create_research_agents()
        llm_config = {"model": "llama3.2", "temperature": 0.7}

        # Submit tasks
        print("\nSubmitting research tasks...")
        task_ids = []

        for agent in agents:
            task_id = mind.submit_agent_task(
                agent,
                "What are the key trends in artificial intelligence?",
                llm_config,
            )
            task_ids.append(task_id)
            print(f"  ✓ Submitted task for {agent['name']}: {task_id}")

        # Monitor progress
        print("\nMonitoring task progress...")
        import time

        while True:
            statuses = mind.get_all_tasks_status()
            pending = sum(1 for s in statuses.values() if not s["ready"])

            if pending == 0:
                break

            print(f"  Pending tasks: {pending}/{len(task_ids)}")
            time.sleep(2)

        # Get results
        print("\nResults:")
        for task_id in task_ids:
            result = mind.wait_for_task(task_id)
            if result.get("success"):
                print(f"\n✓ {result['agent']}:")
                print(f"  {result['result'][:200]}...")
            else:
                print(f"\n✗ {result['agent']}: ERROR - {result.get('error')}")

        print("\n✓ Celery distributed execution completed successfully")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


def example_load_balancing():
    """Example demonstrating load balancing"""
    print("=" * 80)
    print("LOAD BALANCING EXAMPLE")
    print("=" * 80)

    try:
        from agentmind.distributed import (
            create_distributed_mind,
            LoadBalancer,
            CELERY_AVAILABLE,
        )

        if not CELERY_AVAILABLE:
            print("Celery not available. Install with: pip install celery redis")
            return

        # Initialize
        mind = create_distributed_mind("celery")
        balancer = LoadBalancer(mind)

        # Create agents
        agents = create_research_agents()
        llm_config = {"model": "llama3.2", "temperature": 0.7}

        # Add many tasks to queue
        print("\nAdding tasks to queue...")
        topics = [
            "AI in healthcare",
            "Quantum computing advances",
            "Climate change solutions",
            "Space exploration",
            "Renewable energy",
            "Biotechnology breakthroughs",
            "Cybersecurity trends",
            "Autonomous vehicles",
        ]

        for i, topic in enumerate(topics):
            agent = agents[i % len(agents)]
            balancer.add_task(agent, f"Research: {topic}", llm_config)
            print(f"  ✓ Added task: {topic}")

        # Process with load balancing
        print(f"\nProcessing {len(topics)} tasks with max 3 concurrent workers...")
        results = balancer.process_queue(max_concurrent=3)

        print(f"\n✓ Completed {len(results)} tasks")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


def example_fault_tolerance():
    """Example demonstrating fault tolerance"""
    print("=" * 80)
    print("FAULT TOLERANCE EXAMPLE")
    print("=" * 80)

    try:
        from agentmind.distributed import (
            create_distributed_mind,
            FaultTolerantExecutor,
            RAY_AVAILABLE,
        )

        if not RAY_AVAILABLE:
            print("Ray not available. Install with: pip install ray")
            return

        # Initialize
        mind = create_distributed_mind("ray")
        executor = FaultTolerantExecutor(mind, max_retries=3, retry_delay=1.0)

        # Create agent
        agent = {
            "name": "Researcher",
            "role": "research",
            "system_prompt": "You are a thorough researcher.",
        }
        llm_config = {"model": "llama3.2", "temperature": 0.7}

        # Execute with automatic retry
        print("\nExecuting task with fault tolerance (max 3 retries)...")
        result = executor.execute_with_retry(agent, "What is machine learning?", llm_config)

        if result.get("success"):
            print(f"\n✓ Success: {result['result'][:200]}...")
        else:
            print(f"\n✗ Failed: {result.get('error')}")

        # Cleanup
        mind.shutdown()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("AGENTMIND DISTRIBUTED EXECUTION EXAMPLES")
    print("=" * 80)

    # Check available backends
    try:
        from agentmind.distributed import RAY_AVAILABLE, CELERY_AVAILABLE

        print("\nAvailable backends:")
        print(f"  Ray: {'✓' if RAY_AVAILABLE else '✗'}")
        print(f"  Celery: {'✓' if CELERY_AVAILABLE else '✗'}")
    except ImportError:
        print("\nDistributed module not available")
        return

    print("\n")

    # Run examples
    if RAY_AVAILABLE:
        example_ray_distributed()
        print("\n")
        example_fault_tolerance()

    if CELERY_AVAILABLE:
        print("\n")
        example_celery_distributed()
        print("\n")
        example_load_balancing()

    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
