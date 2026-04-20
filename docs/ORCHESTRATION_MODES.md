# Advanced Orchestration Modes

Complete guide to AgentMind's production-ready orchestration patterns for multi-agent collaboration.

## Overview

AgentMind provides 7 sophisticated orchestration modes, each optimized for different collaboration scenarios:

1. **Sequential** - Chain of responsibility with context passing
2. **Hierarchical** - 3-tier architecture with quality control
3. **Debate** - Multi-round deliberation with voting
4. **Consensus** - Agreement-based decision making
5. **Swarm** - Dynamic scaling with load balancing
6. **Graph** - DAG-based workflows with parallel execution
7. **Hybrid** - Combinations of multiple modes

All modes feature:
- Full async/await support
- Comprehensive error handling and recovery
- Detailed logging and observability
- Performance optimization
- Progress tracking and metrics

## Quick Start

```python
from agentmind.core import Agent
from agentmind.orchestration import (
    create_orchestrator,
    OrchestrationMode,
    recommend_mode,
)

# Create agents
agents = [
    Agent("analyst", "analyst"),
    Agent("reviewer", "critic"),
    Agent("coordinator", "coordinator"),
]

# Create orchestrator
orchestrator = create_orchestrator(OrchestrationMode.SEQUENTIAL)

# Execute
result = await orchestrator.orchestrate(agents, "Analyze quarterly results")

print(f"Success: {result.success}")
print(f"Duration: {result.metadata['duration']:.2f}s")
```

## Mode Selection Guide

Use `recommend_mode()` for automatic selection:

```python
mode = recommend_mode(
    num_agents=5,
    task_complexity="high",
    requires_consensus=True,
    has_hierarchy=False,
)
```

### When to Use Each Mode

| Mode | Best For | Team Size | Complexity |
|------|----------|-----------|------------|
| Sequential | Linear workflows, document review | 2-5 | Low-Medium |
| Hierarchical | Project management, quality control | 3+ | Medium-High |
| Debate | Decision making, architecture choices | 3-8 | Medium |
| Consensus | Policy agreements, standards | 3-10 | Medium |
| Swarm | Data processing, parallel tasks | 5-20 | High |
| Graph | Complex workflows, CI/CD pipelines | 3-15 | High |
| Hybrid | Multi-phase projects | 6+ | Very High |

## Detailed Mode Documentation

### 1. Sequential Orchestration

Chain of responsibility pattern where agents process tasks in order, passing context between steps.

**Features:**
- Context passing between agents
- Early termination on errors
- Progress tracking
- Retry logic for failed steps
- Full history or incremental context

**Use Cases:**
- Document review pipelines
- Multi-stage data processing
- Sequential approval workflows
- Code review chains

**Example:**

```python
from agentmind.orchestration import SequentialOrchestrator

orchestrator = SequentialOrchestrator()

result = await orchestrator.orchestrate(
    agents,
    task="Review and approve this proposal",
    early_termination=True,      # Stop on first error
    timeout_per_agent=30.0,      # 30s timeout per agent
    max_retries=2,               # Retry failed steps
    pass_full_history=True,      # Pass all previous messages
)
```

**Parameters:**
- `early_termination` (bool): Stop on first error (default: True)
- `timeout_per_agent` (float): Timeout per agent in seconds
- `max_retries` (int): Max retries per agent (default: 0)
- `pass_full_history` (bool): Pass all messages vs last only (default: False)

### 2. Hierarchical Orchestration

3-tier architecture with manager, workers, and reviewer for structured project execution.

**Architecture:**
- **Manager**: Task decomposition and delegation
- **Workers**: Parallel execution of subtasks
- **Reviewer**: Quality control and synthesis

**Features:**
- Load balancing across workers
- Escalation mechanism for quality issues
- Quality gates with configurable thresholds
- Work redistribution on failure

**Use Cases:**
- Software development projects
- Research coordination
- Content production pipelines
- Quality-critical workflows

**Example:**

```python
from agentmind.orchestration import HierarchicalOrchestrator

# First agent = manager, last = reviewer, middle = workers
agents = [
    Agent("project_manager", "supervisor"),
    Agent("developer_1", "executor"),
    Agent("developer_2", "executor"),
    Agent("qa_lead", "critic"),
]

orchestrator = HierarchicalOrchestrator()

result = await orchestrator.orchestrate(
    agents,
    task="Implement user authentication system",
    quality_threshold=0.8,       # Minimum quality score
    max_escalations=2,           # Max quality escalations
    worker_timeout=60.0,         # Worker timeout
    enable_load_balancing=True,  # Balance work by priority
)
```

**Parameters:**
- `quality_threshold` (float): Minimum quality score 0-1 (default: 0.7)
- `max_escalations` (int): Maximum escalation attempts (default: 2)
- `worker_timeout` (float): Timeout per worker
- `enable_load_balancing` (bool): Balance work across workers (default: True)

### 3. Debate Orchestration

Multi-round deliberation with voting mechanisms for collaborative decision making.

**Features:**
- Multiple rounds of debate
- Voting mechanisms: majority, weighted, consensus
- Optional moderator/facilitator
- Argument tracking and synthesis
- Convergence detection

**Use Cases:**
- Architecture decisions
- Technology selection
- Policy debates
- Strategic planning

**Example:**

```python
from agentmind.orchestration import DebateOrchestrator

agents = [
    Agent("moderator", "coordinator"),  # Optional moderator
    Agent("architect_1", "analyst"),
    Agent("architect_2", "analyst"),
    Agent("engineer", "executor"),
]

orchestrator = DebateOrchestrator()

result = await orchestrator.orchestrate(
    agents,
    task="Should we adopt microservices architecture?",
    debate_rounds=3,                    # Number of rounds
    voting_mechanism="weighted",        # majority/weighted/consensus
    convergence_threshold=0.8,          # Stop if 80% agree
    enable_moderator=True,              # Use first agent as moderator
    weights={                           # For weighted voting
        "architect_1": 2.0,
        "architect_2": 2.0,
        "engineer": 1.0,
    },
)
```

**Parameters:**
- `debate_rounds` (int): Number of debate rounds (default: 3)
- `voting_mechanism` (str): 'majority', 'weighted', 'consensus' (default: 'majority')
- `convergence_threshold` (float): Stop if agreement > threshold (default: 0.8)
- `enable_moderator` (bool): Use first agent as moderator (default: False)
- `weights` (dict): Agent weights for weighted voting

**Voting Mechanisms:**
- **Majority**: Simple majority wins
- **Weighted**: Agents have different voting weights
- **Consensus**: Considers confidence levels

### 4. Consensus Orchestration

Agreement-based decision making with iterative refinement.

**Features:**
- Proposal generation
- Peer review and feedback
- Iterative refinement
- Consensus threshold configuration
- Deadlock resolution

**Use Cases:**
- Team agreements
- Coding standards
- Process definitions
- Policy creation

**Example:**

```python
from agentmind.orchestration import ConsensusOrchestrator

orchestrator = ConsensusOrchestrator()

result = await orchestrator.orchestrate(
    agents,
    task="Establish coding standards for Python project",
    consensus_threshold=0.8,     # 80% agreement required
    max_iterations=5,            # Max refinement iterations
    proposal_timeout=30.0,       # Timeout for proposals
    enable_peer_review=True,     # Enable peer review phase
)
```

**Parameters:**
- `consensus_threshold` (float): Required agreement level (default: 0.75)
- `max_iterations` (int): Maximum refinement iterations (default: 5)
- `proposal_timeout` (float): Timeout for proposals
- `enable_peer_review` (bool): Enable peer review (default: True)

### 5. Swarm Orchestration

Dynamic scaling with work stealing and load balancing for parallel processing.

**Features:**
- Task complexity analysis
- Dynamic agent spawning/termination
- Work stealing for load balancing
- Emergent behavior patterns
- Performance metrics

**Use Cases:**
- Large-scale data processing
- Parallel analysis tasks
- Distributed computation
- High-throughput workflows

**Example:**

```python
from agentmind.orchestration import SwarmOrchestrator

orchestrator = SwarmOrchestrator()

result = await orchestrator.orchestrate(
    agents,
    task="Process 10,000 customer reviews",
    max_agents=10,               # Maximum concurrent agents
    min_agents=2,                # Minimum active agents
    complexity_threshold=50,     # Words per agent
    enable_work_stealing=True,   # Enable work stealing
    agent_timeout=30.0,          # Timeout per agent
)
```

**Parameters:**
- `max_agents` (int): Maximum concurrent agents (default: 10)
- `min_agents` (int): Minimum active agents (default: 2)
- `complexity_threshold` (int): Words per agent (default: 50)
- `enable_work_stealing` (bool): Enable work stealing (default: True)
- `agent_timeout` (float): Timeout per agent

### 6. Graph Orchestration

DAG-based workflows with parallel execution and cycle detection.

**Features:**
- Node types: Agent, Decision, Merge
- Edge conditions and routing
- Parallel execution paths
- Cycle detection
- Mermaid/Graphviz visualization

**Use Cases:**
- CI/CD pipelines
- Complex workflows
- State machines
- Conditional execution paths

**Example:**

```python
from agentmind.orchestration import GraphOrchestrator

orchestrator = GraphOrchestrator()

# Build graph
orchestrator.add_node("start", agent1, "agent")
orchestrator.add_node("test", agent2, "agent")
orchestrator.add_node("decision", agent3, "decision")
orchestrator.add_node("deploy", agent4, "agent")

# Define edges
orchestrator.add_edge("start", "test")
orchestrator.add_edge("test", "decision")
orchestrator.add_edge("decision", "deploy", 
    condition=lambda msg: "PASS" in msg.content)

# Execute
result = await orchestrator.orchestrate(
    agents,
    task="Execute CI/CD pipeline",
    start_node="start",
    max_parallel=3,              # Max parallel executions
    node_timeout=30.0,           # Timeout per node
)

# Visualize
print(orchestrator.visualize_graph("mermaid"))
print(orchestrator.get_graph_stats())
```

**Parameters:**
- `start_node` (str): Starting node ID
- `max_parallel` (int): Maximum parallel executions (default: 5)
- `node_timeout` (float): Timeout per node

**Node Types:**
- `agent`: Standard agent node
- `decision`: Decision/branching node
- `merge`: Merge multiple inputs

### 7. Hybrid Orchestration

Combine multiple orchestration modes for complex multi-phase workflows.

**Integration Strategies:**
- **Sequential**: Phase 1 → Phase 2
- **Parallel**: Both phases simultaneously
- **Nested**: One mode within another

**Use Cases:**
- Multi-phase projects
- Complex research workflows
- Enterprise processes
- Adaptive workflows

**Example:**

```python
from agentmind.orchestration import HybridOrchestrator, OrchestrationMode

# Hierarchical planning + Swarm execution
orchestrator = HybridOrchestrator(
    OrchestrationMode.HIERARCHICAL,
    OrchestrationMode.SWARM,
)

result = await orchestrator.orchestrate(
    agents,
    task="Conduct market research project",
    split_ratio=0.4,                    # 40% agents for phase 1
    integration_strategy="sequential",   # sequential/parallel/nested
    phase_1_kwargs={                    # Hierarchical params
        "quality_threshold": 0.8,
    },
    phase_2_kwargs={                    # Swarm params
        "enable_work_stealing": True,
    },
)
```

**Parameters:**
- `split_ratio` (float): Agent split ratio (default: 0.5)
- `integration_strategy` (str): 'sequential', 'parallel', 'nested'
- `phase_1_kwargs` (dict): Parameters for primary mode
- `phase_2_kwargs` (dict): Parameters for secondary mode

**Common Combinations:**
- Hierarchical + Swarm: Coordinated parallel processing
- Debate + Consensus: Decision followed by agreement
- Sequential + Graph: Linear phases with complex workflows

## Metrics and Observability

All orchestrators provide detailed metrics:

```python
result = await orchestrator.orchestrate(agents, task)

# Access metrics
metrics = result.metadata["metrics"]
print(f"Duration: {metrics['duration']:.2f}s")
print(f"Messages: {metrics['total_messages']}")
print(f"Errors: {len(metrics['errors'])}")
print(f"Agent workload: {metrics['agent_workload']}")

# Mode-specific metrics
custom = metrics.get("custom_metrics", {})
print(f"Custom metrics: {custom}")
```

**Standard Metrics:**
- `duration`: Execution time in seconds
- `total_messages`: Total messages exchanged
- `total_rounds`: Number of rounds executed
- `agent_workload`: Messages per agent
- `errors`: List of errors encountered
- `warnings`: List of warnings

**Mode-Specific Metrics:**
- Sequential: retry counts, step durations
- Hierarchical: escalations, quality scores
- Debate: convergence, vote results
- Consensus: iterations, consensus scores
- Swarm: swarm size, task complexity
- Graph: nodes visited, execution order

## Error Handling

All orchestrators include comprehensive error handling:

```python
result = await orchestrator.orchestrate(
    agents,
    task,
    timeout_per_agent=30.0,  # Prevent hanging
)

if not result.success:
    print(f"Error: {result.error}")
    
# Check metrics for issues
metrics = result.metadata["metrics"]
if metrics["errors"]:
    print(f"Errors encountered: {metrics['errors']}")
if metrics["warnings"]:
    print(f"Warnings: {metrics['warnings']}")
```

**Error Recovery:**
- Automatic retries (configurable)
- Graceful degradation
- Partial results on failure
- Detailed error reporting

## Best Practices

### 1. Choose the Right Mode

```python
# Use recommendation system
mode = recommend_mode(
    num_agents=len(agents),
    task_complexity="high",
    requires_consensus=True,
)

orchestrator = create_orchestrator(mode)
```

### 2. Set Appropriate Timeouts

```python
# Prevent hanging agents
result = await orchestrator.orchestrate(
    agents,
    task,
    timeout_per_agent=60.0,  # Adjust based on task
)
```

### 3. Monitor Metrics

```python
# Track performance
metrics = result.metadata["metrics"]
if metrics["duration"] > 300:  # 5 minutes
    print("Warning: Slow execution")
```

### 4. Handle Errors Gracefully

```python
try:
    result = await orchestrator.orchestrate(agents, task)
    if not result.success:
        # Handle failure
        fallback_result = await simple_orchestrator.orchestrate(agents, task)
except Exception as e:
    logger.error(f"Orchestration failed: {e}")
```

### 5. Use Hybrid for Complex Workflows

```python
# Combine modes for multi-phase tasks
orchestrator = HybridOrchestrator(
    OrchestrationMode.HIERARCHICAL,  # Planning
    OrchestrationMode.SWARM,         # Execution
)
```

## Performance Optimization

### Parallel Execution

```python
# Graph mode for maximum parallelism
orchestrator = GraphOrchestrator()
# Build parallel paths
orchestrator.add_edge("start", "path1")
orchestrator.add_edge("start", "path2")
orchestrator.add_edge("start", "path3")
```

### Load Balancing

```python
# Swarm with work stealing
result = await orchestrator.orchestrate(
    agents,
    task,
    enable_work_stealing=True,
    max_agents=10,
)
```

### Resource Management

```python
# Limit concurrent agents
result = await orchestrator.orchestrate(
    agents,
    task,
    max_parallel=5,  # Limit parallelism
)
```

## Examples

See `examples/orchestration_showcase.py` for comprehensive demonstrations of all modes.

## API Reference

### Factory Functions

```python
create_orchestrator(mode: OrchestrationMode, **kwargs) -> BaseOrchestrator
get_available_modes() -> List[str]
get_mode_description(mode: OrchestrationMode) -> str
recommend_mode(num_agents, task_complexity, requires_consensus, has_hierarchy) -> OrchestrationMode
```

### Base Classes

All orchestrators inherit from `BaseOrchestrator` and implement:

```python
async def orchestrate(
    agents: List[Agent],
    task: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> CollaborationResult
```

## Testing

Run comprehensive tests:

```bash
pytest tests/test_advanced_orchestration.py -v
```

## Contributing

When adding new orchestration modes:

1. Inherit from `BaseOrchestrator`
2. Implement `orchestrate()` and `get_mode()`
3. Use `_safe_process_message()` for error handling
4. Track metrics with `self.metrics`
5. Add comprehensive tests
6. Update documentation

## License

MIT License - see LICENSE file for details.
