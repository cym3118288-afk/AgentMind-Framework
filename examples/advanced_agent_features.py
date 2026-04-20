"""Advanced Agent Features Example.

Demonstrates:
- Advanced state machine with transitions and hooks
- Multi - modal message support
- Human - in - the - loop workflows
- Sub - agent management and delegation
- Learning and adaptation
- State persistence and recovery
"""

import asyncio
from pathlib import Path

from agentmind.core.agent import Agent, AgentState, ApprovalPolicy, ContentType
from agentmind.core.types import Message, MessageRole


# Human callback for approval
def human_approval_callback(approval_request):
    """Simulate human approval."""
    print("\n[HUMAN] Approval requested:")
    print(f"  Agent: {approval_request['agent']}")
    print(f"  Action: {approval_request['action']}")
    print(f"  Context: {approval_request['context']}")

    # Auto - approve for demo (in real scenario, would prompt user)
    return True


# State transition hook
def state_hook(old_state, new_state, metadata):
    """Log state transitions."""
    print(f"[STATE HOOK] {old_state.value} -> {new_state.value}")


async def demo_state_management():
    """Demonstrate advanced state management."""
    print("\n" + "=" * 60)
    print("DEMO 1: Advanced State Management")
    print("=" * 60)

    agent = Agent(
        name="state_agent",
        role="analyst",
        enable_learning=True,
    )

    # Add state hooks
    agent.add_state_hook("on_transition", state_hook)

    # Process a message (triggers state transitions)
    message = Message(
        content="Analyze this data",
        sender="user",
        role=MessageRole.USER,
    )

    response = await agent.process_message(message)
    print(f"\nResponse: {response.content}")

    # View state history
    print("\nState History:")
    for transition in agent.get_state_history():
        print(f"  {transition['from']} -> {transition['to']} at {transition['timestamp']}")


async def demo_multimodal():
    """Demonstrate multi - modal support."""
    print("\n" + "=" * 60)
    print("DEMO 2: Multi - Modal Support")
    print("=" * 60)

    agent = Agent(name="multimodal_agent", role="analyst")

    # Enable multi - modal support
    agent.enable_multimodal(
        content_types=[ContentType.TEXT, ContentType.IMAGE, ContentType.DOCUMENT],
        streaming=False,
    )

    # Process text message
    text_msg = Message(
        content="Analyze this text",
        sender="user",
        role=MessageRole.USER,
    )
    response = await agent.process_multimodal_message(text_msg, ContentType.TEXT)
    print(f"\nText response: {response.content}")

    # Process image message
    image_msg = Message(
        content="What's in this image?",
        sender="user",
        role=MessageRole.USER,
    )
    response = await agent.process_multimodal_message(image_msg, ContentType.IMAGE)
    print(f"\nImage response: {response.content}")


async def demo_human_in_loop():
    """Demonstrate human - in - the - loop workflows."""
    print("\n" + "=" * 60)
    print("DEMO 3: Human - in - the - Loop")
    print("=" * 60)

    agent = Agent(
        name="hitl_agent",
        role="executor",
        human_in_loop=True,
        approval_policy=ApprovalPolicy.ON_TOOL_USE,
        human_callback=human_approval_callback,
    )

    # Request approval for an action
    approved = await agent.request_human_approval(
        action="Execute critical operation",
        context={"risk_level": "high", "impact": "system - wide"},
    )

    print(f"\nApproval result: {approved}")

    # Collect feedback
    await agent.collect_feedback(
        {
            "rating": 5,
            "comments": "Excellent work!",
            "helpful": True,
        }
    )

    print(f"\nFeedback collected: {len(agent.feedback_history)} entries")


async def demo_sub_agents():
    """Demonstrate sub - agent management."""
    print("\n" + "=" * 60)
    print("DEMO 4: Sub - Agent Management")
    print("=" * 60)

    # Create parent agent
    parent = Agent(name="supervisor", role="supervisor")

    # Create sub - agents
    analyst = Agent(name="analyst_sub", role="analyst")
    researcher = Agent(name="researcher_sub", role="researcher")

    # Add sub - agents
    parent.add_sub_agent(analyst)
    parent.add_sub_agent(researcher)

    print(f"\nParent agent has {len(parent.sub_agents)} sub - agents")

    # Delegate task to sub - agent
    task = Message(
        content="Research the latest AI trends",
        sender="supervisor",
        role=MessageRole.AGENT,
    )

    response = await parent.delegate_task("researcher_sub", task)
    print(f"\nDelegation response: {response.content if response else 'None'}")

    # Broadcast to all sub - agents
    broadcast_msg = Message(
        content="What are your thoughts on this?",
        sender="supervisor",
        role=MessageRole.AGENT,
    )

    responses = await parent.broadcast_to_sub_agents(broadcast_msg)
    print(f"\nBroadcast received {len(responses)} responses")

    # Check sub - agent health
    health = parent.get_sub_agent_health()
    print("\nSub - agent health:")
    for agent_name, status in health.items():
        print(f"  {agent_name}: {status}")

    # Aggregate results
    aggregated = parent.aggregate_sub_agent_results(responses, strategy="concatenate")
    print(f"\nAggregated results:\n{aggregated}")


async def demo_learning():
    """Demonstrate learning and adaptation."""
    print("\n" + "=" * 60)
    print("DEMO 5: Learning & Adaptation")
    print("=" * 60)

    agent = Agent(
        name="learning_agent",
        role="assistant",
        enable_learning=True,
    )

    # Track some operations
    agent.track_success(True, response_time=0.5)
    agent.track_success(True, response_time=0.3)
    agent.track_success(False, response_time=1.2)
    agent.track_success(True, response_time=0.4)

    # Get performance metrics
    metrics = agent.get_performance_metrics()
    print("\nPerformance Metrics:")
    print(f"  Total messages: {metrics['total_messages']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print(f"  Average response time: {metrics['average_response_time']:.2f}s")

    # Get improvement suggestions
    suggestions = agent.suggest_improvements()
    print("\nImprovement Suggestions:")
    for suggestion in suggestions:
        print(f"  - {suggestion}")

    # Start A / B test
    agent.start_ab_test(
        "temperature_test",
        variant_a={"temperature": 0.5},
        variant_b={"temperature": 0.9},
    )

    # Record some results
    agent.record_ab_result("temperature_test", True)
    agent.record_ab_result("temperature_test", True)
    agent.record_ab_result("temperature_test", False)
    agent.record_ab_result("temperature_test", True)

    # Get A / B test results
    ab_results = agent.get_ab_test_results("temperature_test")
    print("\nA / B Test Results:")
    print(f"  Variant A success rate: {ab_results['variant_a_success_rate']:.1%}")
    print(f"  Variant B success rate: {ab_results['variant_b_success_rate']:.1%}")


async def demo_persistence():
    """Demonstrate state persistence and recovery."""
    print("\n" + "=" * 60)
    print("DEMO 6: State Persistence & Recovery")
    print("=" * 60)

    # Create agent and process some messages
    agent = Agent(name="persistent_agent", role="analyst")

    for i in range(3):
        msg = Message(
            content=f"Message {i + 1}",
            sender="user",
            role=MessageRole.USER,
        )
        await agent.process_message(msg)

    print(f"\nAgent has {len(agent.memory)} messages in memory")

    # Save state
    state_file = "agent_state.json"
    success = agent.save_state(state_file)
    print(f"\nState saved: {success}")

    # Create new agent and load state
    new_agent = Agent(name="persistent_agent", role="analyst")
    success = new_agent.load_state(state_file)
    print(f"State loaded: {success}")
    print(f"Restored agent has {len(new_agent.memory)} messages in memory")

    # Clean up
    Path(state_file).unlink(missing_ok=True)

    # Demonstrate error recovery
    agent.transition_state(AgentState.ERROR, {"error": "Simulated error"})
    print(f"\nAgent state: {agent.state.value}")

    recovered = await agent.recover_from_error()
    print(f"Recovery successful: {recovered}")
    print(f"Agent state after recovery: {agent.state.value}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("ADVANCED AGENT FEATURES DEMONSTRATION")
    print("=" * 60)

    await demo_state_management()
    await demo_multimodal()
    await demo_human_in_loop()
    await demo_sub_agents()
    await demo_learning()
    await demo_persistence()

    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
