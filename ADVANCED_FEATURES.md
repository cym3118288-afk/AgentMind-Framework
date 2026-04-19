# Advanced Agent and Mind Features - Implementation Guide

## Overview

This document describes the advanced capabilities added to the AgentMind framework's core Agent and Mind classes. These enhancements provide production-ready features for building sophisticated multi-agent systems.

## Agent Class Enhancements

### 1. Advanced State Management

**Features:**
- Full state machine: IDLE → THINKING → EXECUTING → WAITING_HUMAN → DELEGATING → ERROR → RECOVERING
- State transition hooks and callbacks
- State history tracking with timestamps
- Metadata support for transitions

**Usage:**
```python
from agentmind.core.agent import Agent, AgentState

agent = Agent(name="my_agent", role="analyst")

# Add state hooks
def on_state_change(old_state, new_state, metadata):
    print(f"State changed: {old_state} -> {new_state}")

agent.add_state_hook("on_transition", on_state_change)

# Manual state transitions
agent.transition_state(AgentState.THINKING, {"reason": "processing"})

# View state history
history = agent.get_state_history(limit=10)
```

### 2. Multi-Modal Capabilities

**Features:**
- Native support for text, images, audio, video, documents
- Content type validation
- Multi-modal message formatting
- Streaming support (configurable)

**Usage:**
```python
from agentmind.core.agent import Agent, ContentType

agent = Agent(name="multimodal_agent", role="analyst")

# Enable multi-modal support
agent.enable_multimodal(
    content_types=[ContentType.TEXT, ContentType.IMAGE, ContentType.DOCUMENT],
    streaming=False
)

# Process multi-modal messages
message = Message(content="Analyze this image", sender="user")
response = await agent.process_multimodal_message(message, ContentType.IMAGE)
```

### 3. Human-in-the-Loop (HITL)

**Features:**
- Approval workflows with configurable policies
- Feedback collection and adaptation
- Interactive clarification requests
- Escalation policies

**Approval Policies:**
- `ALWAYS`: Require approval for all actions
- `NEVER`: No approval required
- `ON_TOOL_USE`: Approve tool executions
- `ON_HIGH_RISK`: Approve high-risk actions
- `ON_ERROR`: Approve after errors

**Usage:**
```python
from agentmind.core.agent import Agent, ApprovalPolicy

def human_callback(approval_request):
    print(f"Approve: {approval_request['action']}?")
    return True  # or get user input

agent = Agent(
    name="hitl_agent",
    role="executor",
    human_in_loop=True,
    approval_policy=ApprovalPolicy.ON_TOOL_USE,
    human_callback=human_callback
)

# Request approval
approved = await agent.request_human_approval(
    action="Execute critical operation",
    context={"risk": "high"}
)

# Collect feedback
await agent.collect_feedback({
    "rating": 5,
    "comments": "Great work!",
    "helpful": True
})
```

### 4. Sub-Agent Management

**Features:**
- Spawn and manage child agents dynamically
- Delegate tasks to sub-agents
- Monitor sub-agent health
- Aggregate sub-agent results
- Hierarchical agent trees

**Usage:**
```python
# Create parent and sub-agents
parent = Agent(name="supervisor", role="supervisor")
analyst = Agent(name="analyst", role="analyst")
researcher = Agent(name="researcher", role="researcher")

# Build hierarchy
parent.add_sub_agent(analyst)
parent.add_sub_agent(researcher)

# Delegate task
task = Message(content="Research AI trends", sender="supervisor")
response = await parent.delegate_task("researcher", task)

# Broadcast to all sub-agents
responses = await parent.broadcast_to_sub_agents(message)

# Monitor health
health = parent.get_sub_agent_health()

# Aggregate results
aggregated = parent.aggregate_sub_agent_results(
    responses, 
    strategy="concatenate"  # or "vote", "summarize"
)
```

### 5. Learning & Adaptation

**Features:**
- Success/failure tracking
- Performance metrics collection
- Self-improvement suggestions
- A/B testing support
- Automatic adaptation based on feedback

**Usage:**
```python
agent = Agent(name="learning_agent", role="assistant", enable_learning=True)

# Track operations
agent.track_success(True, response_time=0.5)
agent.track_success(False, response_time=1.2)

# Get metrics
metrics = agent.get_performance_metrics()
print(f"Success rate: {metrics['success_rate']:.1%}")
print(f"Avg response time: {metrics['average_response_time']:.2f}s")

# Get improvement suggestions
suggestions = agent.suggest_improvements()

# A/B testing
agent.start_ab_test(
    "temperature_test",
    variant_a={"temperature": 0.5},
    variant_b={"temperature": 0.9}
)

agent.record_ab_result("temperature_test", True)
results = agent.get_ab_test_results("temperature_test")
```

### 6. State Persistence & Recovery

**Features:**
- Save/restore agent state to disk
- Crash recovery
- State migration support
- Error recovery mechanisms

**Usage:**
```python
# Save state
agent.save_state("agent_state.json")

# Load state
new_agent = Agent(name="restored_agent", role="analyst")
new_agent.load_state("agent_state.json")

# Error recovery
if agent.state == AgentState.ERROR:
    recovered = await agent.recover_from_error()
```

## Mind Class Enhancements

### 1. Global Orchestration

**Features:**
- Multi-agent coordination strategies
- Resource allocation and scheduling
- Priority queue management
- Deadlock detection and resolution

**Coordination Strategies:**
- `CENTRALIZED`: Central coordinator
- `DECENTRALIZED`: Peer-to-peer
- `AUCTION`: Task bidding
- `VOTING`: Democratic decisions
- `CONSENSUS`: Require agreement

**Usage:**
```python
from agentmind.core.mind import AgentMind, CoordinationStrategy

mind = AgentMind(
    coordination_strategy=CoordinationStrategy.CENTRALIZED,
    max_concurrent_tasks=10
)

# Resource allocation
mind.resource_allocation.allocate("agent1", amount=2)
available = mind.resource_allocation.get_available("agent1")
mind.resource_allocation.release("agent1", amount=1)
```

### 2. Advanced Task Management

**Features:**
- Task dependencies (DAG)
- Parallel task execution
- Task prioritization (CRITICAL, HIGH, MEDIUM, LOW)
- Task timeout and cancellation
- Retry policies with backoff

**Usage:**
```python
from agentmind.core.mind import AgentMind, TaskPriority

mind = AgentMind()

# Add tasks with dependencies
mind.add_task(
    task_id="research",
    description="Research the topic",
    priority=TaskPriority.HIGH,
    assigned_agents=["researcher"]
)

mind.add_task(
    task_id="analyze",
    description="Analyze findings",
    priority=TaskPriority.HIGH,
    dependencies=["research"],  # Depends on research
    timeout=60.0,  # 60 second timeout
    retry_policy={"max_retries": 3, "backoff": 1.0}
)

# Execute task queue
results = await mind.execute_task_queue(max_parallel=3)

# Cancel task
mind.cancel_task("analyze")

# Get task status
status = mind.get_task_status("research")
```

### 3. Checkpointing & Recovery

**Features:**
- Save/restore full system state
- Crash recovery with automatic restoration
- Replay capability
- State migration between versions

**Usage:**
```python
mind = AgentMind(enable_checkpointing=True)

# Add agents and tasks
mind.add_agent(Agent(name="agent1", role="analyst"))
mind.add_task("task1", "First task")

# Save checkpoint
checkpoint_path = mind.save_checkpoint("my_checkpoint")

# Restore checkpoint
new_mind = AgentMind()
success = new_mind.restore_checkpoint("my_checkpoint")

# Crash recovery
recovered = await mind.crash_recovery()
```

### 4. System Observability

**Features:**
- Real-time metrics dashboard data
- Event streaming
- Performance profiling
- Cost tracking per agent/task

**Usage:**
```python
# Get real-time metrics
metrics = mind.get_real_time_metrics()
print(f"Active agents: {metrics['agents']['active']}")
print(f"Running tasks: {metrics['tasks']['running']}")
print(f"Success rate: {metrics['collaboration']['success_rate']:.1%}")

# Event stream
events = mind.get_event_stream(limit=100)
for event in events:
    print(f"{event['type']}: {event['timestamp']}")

# Performance profiling
mind.profile_performance("collaboration", duration=1.5)
profile = mind.get_performance_profile("collaboration")
print(f"Average: {profile['average']:.2f}s")

# Cost tracking
mind.track_cost("agent1", 0.05)
costs = mind.get_cost_summary()
```

### 5. Collaboration Patterns

**Features:**
- Agent communication protocols
- Shared context management
- Conflict resolution strategies
- Consensus building

**Conflict Resolution Strategies:**
- `PRIORITY`: Higher priority wins
- `VOTING`: Majority vote
- `SUPERVISOR`: Supervisor decides
- `MERGE`: Merge conflicting results

**Usage:**
```python
from agentmind.core.mind import ConflictResolutionStrategy

mind = AgentMind()

# Shared context
mind.set_shared_context("project_goal", "Build AI system")
goal = mind.get_shared_context("project_goal")

# Conflict resolution
mind.conflict_resolution = ConflictResolutionStrategy.VOTING
conflicting_results = [
    ("agent1", "Option A"),
    ("agent2", "Option B"),
    ("agent3", "Option A")
]
resolved = mind.resolve_conflict(conflicting_results)

# Build consensus
consensus = await mind.build_consensus(
    "Should we proceed?",
    threshold=0.7  # 70% agreement required
)
```

### 6. Observers & Event System

**Features:**
- Observer pattern for system events
- Async event notifications
- Custom event handlers

**Usage:**
```python
def event_observer(event_type, data):
    print(f"Event: {event_type}")
    if event_type == "task_completed":
        print(f"Task {data['task_id']} completed")

mind.add_observer(event_observer)

# Events are automatically emitted for:
# - task_added, task_started, task_completed, task_failed
# - collaboration_started, collaboration_completed
# - shared_context_updated
```

## Backward Compatibility

All enhancements maintain full backward compatibility with existing code:

```python
# Old code still works
agent = Agent(name="agent", role="analyst")
mind = AgentMind()
mind.add_agent(agent)
result = await mind.start_collaboration("Task")

# New features are opt-in
agent = Agent(
    name="agent",
    role="analyst",
    human_in_loop=True,  # New feature
    enable_learning=True  # New feature
)
```

## Performance Considerations

1. **State History**: Limited to recent transitions (configurable)
2. **Event Stream**: Automatically trimmed to last 1000 events
3. **Performance Profiles**: Keep last 100 measurements per operation
4. **Memory Management**: Automatic trimming based on limits

## Migration Guide

### From Basic Agent to Advanced Agent

```python
# Before
agent = Agent(name="agent", role="analyst")

# After (with new features)
agent = Agent(
    name="agent",
    role="analyst",
    human_in_loop=True,
    approval_policy=ApprovalPolicy.ON_TOOL_USE,
    human_callback=my_callback,
    enable_learning=True
)

# Enable multi-modal
agent.enable_multimodal([ContentType.TEXT, ContentType.IMAGE])

# Add sub-agents
agent.add_sub_agent(sub_agent)
```

### From Basic Mind to Advanced Mind

```python
# Before
mind = AgentMind(strategy=CollaborationStrategy.BROADCAST)

# After (with new features)
mind = AgentMind(
    strategy=CollaborationStrategy.BROADCAST,
    coordination_strategy=CoordinationStrategy.CENTRALIZED,
    enable_checkpointing=True,
    max_concurrent_tasks=10
)

# Use task management
mind.add_task("task1", "Description", TaskPriority.HIGH)
results = await mind.execute_task_queue()

# Use observability
metrics = mind.get_real_time_metrics()
```

## Examples

See the following example files for complete demonstrations:

- `examples/advanced_agent_features.py` - All agent features
- `examples/advanced_mind_features.py` - All mind features

## Testing

Comprehensive test coverage is provided:

- `tests/test_advanced_agent.py` - 23 tests for agent features
- `tests/test_advanced_mind.py` - 31 tests for mind features

Run tests:
```bash
pytest tests/test_advanced_agent.py -v
pytest tests/test_advanced_mind.py -v
```

## API Reference

### Agent Class

**New Methods:**
- `transition_state(new_state, metadata)` - Transition to new state
- `add_state_hook(hook_type, callback)` - Add state hook
- `get_state_history(limit)` - Get state history
- `enable_multimodal(content_types, streaming)` - Enable multi-modal
- `process_multimodal_message(message, content_type)` - Process multi-modal
- `request_human_approval(action, context)` - Request approval
- `collect_feedback(feedback)` - Collect feedback
- `request_clarification(question)` - Request clarification
- `add_sub_agent(agent)` - Add sub-agent
- `delegate_task(sub_agent_name, task)` - Delegate task
- `broadcast_to_sub_agents(message)` - Broadcast to sub-agents
- `get_sub_agent_health()` - Get sub-agent health
- `aggregate_sub_agent_results(results, strategy)` - Aggregate results
- `track_success(success, response_time)` - Track performance
- `get_performance_metrics()` - Get metrics
- `suggest_improvements()` - Get suggestions
- `start_ab_test(name, variant_a, variant_b)` - Start A/B test
- `record_ab_result(test_name, success)` - Record A/B result
- `get_ab_test_results(test_name)` - Get A/B results
- `save_state(filepath)` - Save state
- `load_state(filepath)` - Load state
- `recover_from_error()` - Recover from error

### Mind Class

**New Methods:**
- `add_task(task_id, description, priority, ...)` - Add task
- `cancel_task(task_id)` - Cancel task
- `get_task_status(task_id)` - Get task status
- `get_ready_tasks()` - Get ready tasks
- `execute_task_queue(max_parallel)` - Execute tasks
- `save_checkpoint(checkpoint_name)` - Save checkpoint
- `restore_checkpoint(checkpoint_name)` - Restore checkpoint
- `crash_recovery()` - Recover from crash
- `get_real_time_metrics()` - Get metrics
- `get_event_stream(limit)` - Get events
- `profile_performance(operation, duration)` - Profile performance
- `get_performance_profile(operation)` - Get profile
- `track_cost(agent_name, cost)` - Track cost
- `get_cost_summary()` - Get cost summary
- `set_shared_context(key, value)` - Set shared context
- `get_shared_context(key)` - Get shared context
- `resolve_conflict(conflicting_results, strategy)` - Resolve conflict
- `build_consensus(question, threshold)` - Build consensus
- `add_observer(observer)` - Add observer

## Conclusion

These enhancements transform AgentMind into a production-ready framework with enterprise-grade features while maintaining simplicity and backward compatibility. All features are fully tested and documented with working examples.
