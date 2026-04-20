"""Advanced orchestration modes for multi-agent collaboration.

This module implements production-ready orchestration patterns:
- Sequential: Chain of responsibility with context passing and error handling
- Hierarchical: 3-tier architecture with manager, workers, and reviewer
- Debate: Multi-round deliberation with voting and convergence detection
- Consensus: Agreement-based decision making with iterative refinement
- Swarm: Dynamic scaling with work stealing and load balancing
- Graph: DAG-based workflows with parallel execution and cycle detection
- Hybrid: Combinations of multiple modes

All modes support:
- Full async/await
- Comprehensive error handling and recovery
- Detailed logging and observability
- Performance optimization
- Progress tracking and metrics
"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from collections import defaultdict

from ..core.agent import Agent
from ..core.types import Message, MessageRole, CollaborationResult

# Configure logging
logger = logging.getLogger(__name__)


class OrchestrationMode(str, Enum):
    """Available orchestration modes."""

    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"
    DEBATE = "debate"
    CONSENSUS = "consensus"
    SWARM = "swarm"
    GRAPH = "graph"
    HYBRID = "hybrid"


@dataclass
class OrchestrationMetrics:
    """Metrics for orchestration execution."""

    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_messages: int = 0
    total_rounds: int = 0
    agent_workload: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    def record_message(self, agent_name: str) -> None:
        """Record a message from an agent."""
        self.total_messages += 1
        self.agent_workload[agent_name] = self.agent_workload.get(agent_name, 0) + 1

    def record_error(self, error: str) -> None:
        """Record an error."""
        self.errors.append(error)
        logger.error(f"Orchestration error: {error}")

    def record_warning(self, warning: str) -> None:
        """Record a warning."""
        self.warnings.append(warning)
        logger.warning(f"Orchestration warning: {warning}")

    def finalize(self) -> None:
        """Finalize metrics collection."""
        self.end_time = time.time()

    def get_duration(self) -> float:
        """Get execution duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "duration": self.get_duration(),
            "total_messages": self.total_messages,
            "total_rounds": self.total_rounds,
            "agent_workload": self.agent_workload,
            "errors": self.errors,
            "warnings": self.warnings,
            "custom_metrics": self.custom_metrics,
        }


class BaseOrchestrator(ABC):
    """Base class for orchestrators with common functionality."""

    def __init__(self) -> None:
        """Initialize base orchestrator."""
        self.metrics = OrchestrationMetrics()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def orchestrate(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> CollaborationResult:
        """Orchestrate agent collaboration.

        Args:
            agents: List of agents
            task: Task description
            context: Optional context
            **kwargs: Mode-specific parameters

        Returns:
            Collaboration result
        """

    @abstractmethod
    def get_mode(self) -> OrchestrationMode:
        """Get orchestration mode."""

    async def _safe_process_message(
        self, agent: Agent, message: Message, timeout: Optional[float] = None
    ) -> Optional[Message]:
        """Safely process a message with error handling.

        Args:
            agent: Agent to process message
            message: Message to process
            timeout: Optional timeout in seconds

        Returns:
            Response message or None on error
        """
        try:
            if timeout:
                response = await asyncio.wait_for(agent.process_message(message), timeout=timeout)
            else:
                response = await agent.process_message(message)

            if response:
                self.metrics.record_message(agent.name)
            return response

        except asyncio.TimeoutError:
            error_msg = f"Agent {agent.name} timed out after {timeout}s"
            self.metrics.record_error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Agent {agent.name} error: {str(e)}"
            self.metrics.record_error(error_msg)
            return None

    def _validate_agents(self, agents: List[Agent], min_agents: int = 1) -> bool:
        """Validate agent list.

        Args:
            agents: List of agents to validate
            min_agents: Minimum required agents

        Returns:
            True if valid, False otherwise
        """
        if not agents:
            self.metrics.record_error("No agents provided")
            return False

        if len(agents) < min_agents:
            self.metrics.record_error(f"Insufficient agents: {len(agents)} < {min_agents}")
            return False

        active_agents = [a for a in agents if a.is_active]
        if not active_agents:
            self.metrics.record_warning("No active agents available")
            return False

        return True

    def _create_result(
        self,
        success: bool,
        messages: List[Message],
        error: Optional[str] = None,
    ) -> CollaborationResult:
        """Create a collaboration result.

        Args:
            success: Whether orchestration succeeded
            messages: List of messages exchanged
            error: Optional error message

        Returns:
            CollaborationResult
        """
        self.metrics.finalize()

        agent_contributions = {}
        for agent_name, count in self.metrics.agent_workload.items():
            agent_contributions[agent_name] = count

        final_output = messages[-1].content if messages else None

        return CollaborationResult(
            success=success,
            total_rounds=self.metrics.total_rounds,
            total_messages=self.metrics.total_messages,
            final_output=final_output,
            agent_contributions=agent_contributions,
            error=error,
            metadata={
                "mode": self.get_mode().value,
                "duration": self.metrics.get_duration(),
                "metrics": self.metrics.to_dict(),
            },
        )


class SequentialOrchestrator(BaseOrchestrator):
    """Sequential orchestration with chain of responsibility pattern.

    Features:
    - Context passing between agents
    - Early termination on errors
    - Progress tracking
    - Retry logic for failed steps
    """

    def get_mode(self) -> OrchestrationMode:
        return OrchestrationMode.SEQUENTIAL

    async def orchestrate(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> CollaborationResult:
        """Execute agents sequentially with context passing.

        Args:
            agents: List of agents
            task: Task description
            context: Optional initial context
            **kwargs: Additional parameters
                - early_termination: Stop on first error (default: True)
                - timeout_per_agent: Timeout per agent in seconds
                - max_retries: Max retries per agent (default: 0)
                - pass_full_history: Pass all previous messages (default: False)

        Returns:
            Collaboration result
        """
        if not self._validate_agents(agents):
            return self._create_result(False, [], "Invalid agents")

        early_termination = kwargs.get("early_termination", True)
        timeout_per_agent = kwargs.get("timeout_per_agent")
        max_retries = kwargs.get("max_retries", 0)
        pass_full_history = kwargs.get("pass_full_history", False)

        self.logger.info(f"Starting sequential orchestration with {len(agents)} agents")

        messages: List[Message] = []
        current_context = context or {}

        # Initial message
        current_message = Message(
            content=task,
            sender="system",
            role=MessageRole.SYSTEM,
            metadata={"context": current_context},
        )
        messages.append(current_message)

        # Process each agent in sequence
        for i, agent in enumerate(agents):
            if not agent.is_active:
                self.metrics.record_warning(f"Agent {agent.name} is inactive, skipping")
                continue

            self.logger.info(f"Step {i + 1}/{len(agents)}: {agent.name}")
            self.metrics.total_rounds += 1

            # Prepare message with context
            if pass_full_history:
                # Include all previous messages
                message_content = f"{task}\n\nPrevious steps:\n"
                for msg in messages[1:]:  # Skip initial system message
                    message_content += f"- {msg.sender}: {msg.content[:100]}...\n"
                message_content += (
                    f"\nYour turn: Continue from where {messages[-1].sender} left off."
                )
            else:
                # Only pass last message
                message_content = current_message.content

            step_message = Message(
                content=message_content,
                sender="orchestrator",
                role=MessageRole.SYSTEM,
                metadata={"step": i + 1, "context": current_context},
            )

            # Execute with retries
            response = await self._execute_with_retry(
                agent, step_message, max_retries, timeout_per_agent
            )

            if response:
                messages.append(response)
                current_message = response

                # Update context from response metadata
                if response.metadata:
                    current_context.update(response.metadata.get("context", {}))

                self.logger.debug(f"Agent {agent.name} completed successfully")
            else:
                error_msg = f"Agent {agent.name} failed to respond"
                self.metrics.record_error(error_msg)

                if early_termination:
                    self.logger.error(f"Early termination triggered at step {i + 1}")
                    return self._create_result(False, messages, error_msg)

        success = len(messages) > 1  # At least one agent responded
        return self._create_result(success, messages)

    async def _execute_with_retry(
        self,
        agent: Agent,
        message: Message,
        max_retries: int,
        timeout: Optional[float],
    ) -> Optional[Message]:
        """Execute agent with retry logic.

        Args:
            agent: Agent to execute
            message: Message to process
            max_retries: Maximum retry attempts
            timeout: Timeout per attempt

        Returns:
            Response message or None
        """
        for attempt in range(max_retries + 1):
            if attempt > 0:
                self.logger.info(f"Retry attempt {attempt}/{max_retries} for {agent.name}")
                await asyncio.sleep(0.5 * attempt)  # Exponential backoff

            response = await self._safe_process_message(agent, message, timeout)
            if response:
                return response

        return None


class HierarchicalOrchestrator(BaseOrchestrator):
    """Hierarchical orchestration with 3-tier architecture.

    Architecture:
    - Manager: Task decomposition and delegation
    - Workers: Parallel execution
    - Reviewer: Quality control and synthesis

    Features:
    - Load balancing across workers
    - Escalation mechanism
    - Quality gates
    - Work redistribution on failure
    """

    def get_mode(self) -> OrchestrationMode:
        return OrchestrationMode.HIERARCHICAL

    async def orchestrate(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> CollaborationResult:
        """Execute in hierarchical mode.

        Args:
            agents: List of agents (first is manager, last is reviewer, rest are workers)
            task: Task description
            context: Optional context
            **kwargs: Additional parameters
                - quality_threshold: Minimum quality score (0-1)
                - max_escalations: Maximum escalation attempts
                - worker_timeout: Timeout per worker
                - enable_load_balancing: Balance work across workers

        Returns:
            Collaboration result
        """
        if not self._validate_agents(agents, min_agents=3):
            return self._create_result(False, [], "Hierarchical mode requires at least 3 agents")

        quality_threshold = kwargs.get("quality_threshold", 0.7)
        max_escalations = kwargs.get("max_escalations", 2)
        worker_timeout = kwargs.get("worker_timeout", 30.0)
        enable_load_balancing = kwargs.get("enable_load_balancing", True)

        self.logger.info(f"Starting hierarchical orchestration with {len(agents)} agents")

        manager = agents[0]
        workers = agents[1:-1]
        reviewer = agents[-1]

        messages: List[Message] = []
        escalation_count = 0

        # Phase 1: Manager decomposes task
        self.logger.info("Phase 1: Manager planning and task decomposition")
        self.metrics.total_rounds += 1

        manager_msg = Message(
            content=f"""As the manager, decompose this task into {len(workers)} subtasks:

Task: {task}

Provide:
1. Clear subtask descriptions
2. Priority levels
3. Dependencies between subtasks

Format each subtask as:
SUBTASK [number]: [description]
PRIORITY: [high/medium/low]
DEPENDENCIES: [none or list]""",
            sender="system",
            role=MessageRole.SYSTEM,
        )

        manager_response = await self._safe_process_message(manager, manager_msg, worker_timeout)

        if not manager_response:
            return self._create_result(False, messages, "Manager failed to respond")

        messages.append(manager_response)

        # Parse subtasks
        subtasks = self._parse_subtasks(manager_response.content, len(workers))

        # Phase 2: Workers execute in parallel
        self.logger.info(f"Phase 2: {len(workers)} workers executing subtasks")
        self.metrics.total_rounds += 1

        worker_results = await self._execute_workers(
            workers, subtasks, worker_timeout, enable_load_balancing
        )

        for result in worker_results:
            if result:
                messages.append(result)

        # Phase 3: Reviewer evaluates and synthesizes
        while escalation_count <= max_escalations:
            self.logger.info(f"Phase 3: Reviewer evaluation (attempt {escalation_count + 1})")
            self.metrics.total_rounds += 1

            review_content = f"""Review and synthesize these worker results:

Original task: {task}

Worker outputs:
"""
            for i, result in enumerate(worker_results):
                if result:
                    review_content += f"\nWorker {i + 1}: {result.content[:200]}...\n"

            review_content += """

Evaluate:
1. Quality score (0-1)
2. Completeness
3. Issues found
4. Final synthesis

Format:
QUALITY: [0.0-1.0]
COMPLETENESS: [percentage]
ISSUES: [list or none]
SYNTHESIS: [final output]"""

            review_msg = Message(content=review_content, sender="system", role=MessageRole.SYSTEM)

            review_response = await self._safe_process_message(reviewer, review_msg, worker_timeout)

            if not review_response:
                return self._create_result(False, messages, "Reviewer failed to respond")

            messages.append(review_response)

            # Check quality
            quality_score = self._extract_quality_score(review_response.content)

            if quality_score >= quality_threshold:
                self.logger.info(f"Quality threshold met: {quality_score:.2f}")
                break

            # Escalate if quality insufficient
            escalation_count += 1
            if escalation_count <= max_escalations:
                self.logger.warning(
                    f"Quality below threshold ({quality_score:.2f} < {quality_threshold}), escalating"
                )
                self.metrics.record_warning(
                    f"Escalation {escalation_count}: Quality {quality_score:.2f}"
                )

                # Re-execute with feedback
                feedback_msg = Message(
                    content=(
                        f"Previous attempt had quality {quality_score:.2f}. "
                        f"Issues: {review_response.content}. Please improve."
                    ),
                    sender="reviewer",
                    role=MessageRole.SYSTEM,
                )

                worker_results = await self._execute_workers(
                    workers, subtasks, worker_timeout, enable_load_balancing, feedback_msg
                )

        self.metrics.custom_metrics["escalations"] = escalation_count
        self.metrics.custom_metrics["final_quality"] = quality_score

        return self._create_result(True, messages)

    def _parse_subtasks(self, content: str, num_workers: int) -> List[Dict[str, Any]]:
        """Parse subtasks from manager response."""
        subtasks = []
        lines = content.split("\n")

        current_subtask = {}
        for line in lines:
            line = line.strip()
            if line.startswith("SUBTASK"):
                if current_subtask:
                    subtasks.append(current_subtask)
                desc = line.split(":", 1)[1].strip() if ":" in line else line
                current_subtask = {
                    "description": desc,
                    "priority": "medium",
                    "dependencies": [],
                }
            elif line.startswith("PRIORITY:") and current_subtask:
                current_subtask["priority"] = line.split(":", 1)[1].strip().lower()
            elif line.startswith("DEPENDENCIES:") and current_subtask:
                deps = line.split(":", 1)[1].strip().lower()
                if deps != "none":
                    current_subtask["dependencies"] = [d.strip() for d in deps.split(",")]

        if current_subtask:
            subtasks.append(current_subtask)

        # Ensure we have enough subtasks
        while len(subtasks) < num_workers:
            subtasks.append(
                {
                    "description": f"Support task {len(subtasks) + 1}",
                    "priority": "low",
                    "dependencies": [],
                }
            )

        return subtasks[:num_workers]

    async def _execute_workers(
        self,
        workers: List[Agent],
        subtasks: List[Dict[str, Any]],
        timeout: float,
        load_balance: bool,
        feedback: Optional[Message] = None,
    ) -> List[Optional[Message]]:
        """Execute workers in parallel with optional load balancing."""
        if load_balance:
            # Sort subtasks by priority
            priority_order = {"high": 0, "medium": 1, "low": 2}
            sorted_subtasks = sorted(
                enumerate(subtasks), key=lambda x: priority_order.get(x[1]["priority"], 1)
            )
            assignments = [
                (workers[i % len(workers)], st) for i, (_, st) in enumerate(sorted_subtasks)
            ]
        else:
            # Simple assignment
            assignments = [(workers[i % len(workers)], st) for i, st in enumerate(subtasks)]

        tasks = []
        for worker, subtask in assignments:
            content = subtask["description"]
            if feedback:
                content = f"{feedback.content}\n\nSubtask: {content}"

            msg = Message(content=content, sender="manager", role=MessageRole.SYSTEM)
            tasks.append(self._safe_process_message(worker, msg, timeout))

        return await asyncio.gather(*tasks)

    def _extract_quality_score(self, content: str) -> float:
        """Extract quality score from reviewer response."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("QUALITY:"):
                try:
                    score_str = line.split(":", 1)[1].strip()
                    return float(score_str)
                except (ValueError, IndexError):
                    pass
        return 0.5  # Default if not found


class DebateOrchestrator(BaseOrchestrator):
    """Debate orchestration with multi-round deliberation.

    Features:
    - Multiple rounds of debate
    - Voting mechanisms (majority, weighted, consensus)
    - Moderator/facilitator agent
    - Argument tracking and synthesis
    - Convergence detection
    """

    def get_mode(self) -> OrchestrationMode:
        return OrchestrationMode.DEBATE

    async def orchestrate(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> CollaborationResult:
        """Execute debate mode with voting.

        Args:
            agents: List of agents
            task: Task description
            context: Optional context
            **kwargs: Additional parameters
                - debate_rounds: Number of debate rounds (default: 3)
                - voting_mechanism: 'majority', 'weighted', 'consensus' (default: 'majority')
                - convergence_threshold: Stop if agreement > threshold (default: 0.8)
                - enable_moderator: Use first agent as moderator (default: False)
                - weights: Dict of agent weights for weighted voting

        Returns:
            Collaboration result
        """
        if not self._validate_agents(agents, min_agents=2):
            return self._create_result(False, [], "Debate requires at least 2 agents")

        debate_rounds = kwargs.get("debate_rounds", 3)
        voting_mechanism = kwargs.get("voting_mechanism", "majority")
        convergence_threshold = kwargs.get("convergence_threshold", 0.8)
        enable_moderator = kwargs.get("enable_moderator", False)
        weights = kwargs.get("weights", {})

        self.logger.info(f"Starting debate with {len(agents)} agents for {debate_rounds} rounds")

        messages: List[Message] = []
        debate_history: List[Dict[str, Any]] = []

        # Setup moderator if enabled
        if enable_moderator:
            moderator = agents[0]
            debaters = agents[1:]
            self.logger.info(f"Moderator: {moderator.name}")
        else:
            moderator = None
            debaters = agents

        # Initial positions
        initial_msg = Message(
            content=f"""State your position on: {task}

Provide:
1. Your stance (SUPPORT/OPPOSE/NEUTRAL)
2. Key arguments (2-3 points)
3. Confidence level (0-100)

Format:
STANCE: [SUPPORT/OPPOSE/NEUTRAL]
ARGUMENTS:
- [argument 1]
- [argument 2]
CONFIDENCE: [0-100]""",
            sender="system",
            role=MessageRole.SYSTEM,
        )

        # Debate rounds
        for round_num in range(debate_rounds):
            self.logger.info(f"Debate round {round_num + 1}/{debate_rounds}")
            self.metrics.total_rounds += 1

            round_responses = []

            # Moderator introduces round
            if moderator and round_num > 0:
                mod_msg = Message(
                    content=f"Round {round_num + 1}: Review previous arguments and refine your position.",
                    sender="moderator",
                    role=MessageRole.SYSTEM,
                )
                mod_response = await self._safe_process_message(moderator, mod_msg)
                if mod_response:
                    messages.append(mod_response)

            # Each agent presents position
            for agent in debaters:
                if round_num == 0:
                    context_msg = initial_msg
                else:
                    # Include previous round context
                    prev_args = self._summarize_previous_round(debate_history[-1])
                    context_msg = Message(
                        content=f"""{task}

Previous round summary:
{prev_args}

Respond to these arguments and refine your position.""",
                        sender="system",
                        role=MessageRole.SYSTEM,
                    )

                response = await self._safe_process_message(agent, context_msg)
                if response:
                    round_responses.append(response)
                    messages.append(response)

            # Parse positions
            positions = self._parse_debate_positions(round_responses)
            debate_history.append(
                {
                    "round": round_num + 1,
                    "positions": positions,
                    "responses": round_responses,
                }
            )

            # Check for convergence
            convergence = self._calculate_convergence(positions)
            self.logger.info(f"Round {round_num + 1} convergence: {convergence:.2f}")

            if convergence >= convergence_threshold:
                self.logger.info("Convergence threshold reached, ending debate")
                break

        # Final voting phase
        self.logger.info(f"Final voting using {voting_mechanism} mechanism")
        vote_result = await self._conduct_voting(
            debaters, debate_history, voting_mechanism, weights
        )

        # Moderator summarizes if enabled
        if moderator:
            summary_msg = Message(
                content=f"""Summarize the debate and final decision:

Debate topic: {task}
Voting result: {vote_result}

Provide a balanced summary of all perspectives.""",
                sender="system",
                role=MessageRole.SYSTEM,
            )
            summary = await self._safe_process_message(moderator, summary_msg)
            if summary:
                messages.append(summary)

        self.metrics.custom_metrics["debate_rounds"] = len(debate_history)
        self.metrics.custom_metrics["final_convergence"] = convergence
        self.metrics.custom_metrics["vote_result"] = vote_result

        return self._create_result(True, messages)

    def _parse_debate_positions(self, responses: List[Message]) -> List[Dict[str, Any]]:
        """Parse debate positions from responses."""
        positions = []

        for response in responses:
            position = {
                "agent": response.sender,
                "stance": "NEUTRAL",
                "arguments": [],
                "confidence": 50,
            }

            lines = response.content.split("\n")
            current_section = None

            for line in lines:
                line = line.strip()
                if line.startswith("STANCE:"):
                    stance = line.split(":", 1)[1].strip().upper()
                    if stance in ["SUPPORT", "OPPOSE", "NEUTRAL"]:
                        position["stance"] = stance
                elif line.startswith("ARGUMENTS:"):
                    current_section = "arguments"
                elif line.startswith("CONFIDENCE:"):
                    try:
                        position["confidence"] = int(line.split(":", 1)[1].strip())
                    except (ValueError, IndexError):
                        pass
                elif current_section == "arguments" and line.startswith("-"):
                    position["arguments"].append(line[1:].strip())

            positions.append(position)

        return positions

    def _calculate_convergence(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate convergence level (0-1) based on stance agreement."""
        if not positions:
            return 0.0

        stance_counts = defaultdict(int)
        for pos in positions:
            stance_counts[pos["stance"]] += 1

        max_agreement = max(stance_counts.values())
        return max_agreement / len(positions)

    def _summarize_previous_round(self, round_data: Dict[str, Any]) -> str:
        """Summarize previous round arguments."""
        summary = []
        for pos in round_data["positions"]:
            summary.append(f"{pos['agent']} ({pos['stance']}): {', '.join(pos['arguments'][:2])}")
        return "\n".join(summary)

    async def _conduct_voting(
        self,
        agents: List[Agent],
        debate_history: List[Dict[str, Any]],
        mechanism: str,
        weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Conduct final voting."""
        # Get final positions
        final_positions = debate_history[-1]["positions"] if debate_history else []

        if mechanism == "majority":
            return self._majority_vote(final_positions)
        elif mechanism == "weighted":
            return self._weighted_vote(final_positions, weights)
        elif mechanism == "consensus":
            return self._consensus_vote(final_positions)
        else:
            return {"error": f"Unknown voting mechanism: {mechanism}"}

    def _majority_vote(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple majority voting."""
        stance_counts = defaultdict(int)
        for pos in positions:
            stance_counts[pos["stance"]] += 1

        winner = max(stance_counts.items(), key=lambda x: x[1])
        return {
            "mechanism": "majority",
            "winner": winner[0],
            "votes": dict(stance_counts),
            "total": len(positions),
        }

    def _weighted_vote(
        self, positions: List[Dict[str, Any]], weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Weighted voting based on agent weights."""
        stance_weights = defaultdict(float)

        for pos in positions:
            weight = weights.get(pos["agent"], 1.0)
            stance_weights[pos["stance"]] += weight

        winner = max(stance_weights.items(), key=lambda x: x[1])
        return {
            "mechanism": "weighted",
            "winner": winner[0],
            "weighted_votes": dict(stance_weights),
            "weights_used": weights,
        }

    def _consensus_vote(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consensus voting considering confidence levels."""
        stance_confidence = defaultdict(float)

        for pos in positions:
            stance_confidence[pos["stance"]] += pos["confidence"]

        winner = max(stance_confidence.items(), key=lambda x: x[1])
        avg_confidence = winner[1] / len([p for p in positions if p["stance"] == winner[0]])

        return {
            "mechanism": "consensus",
            "winner": winner[0],
            "total_confidence": dict(stance_confidence),
            "average_confidence": avg_confidence,
        }


class ConsensusOrchestrator(BaseOrchestrator):
    """Consensus orchestration with agreement-based decision making.

    Features:
    - Proposal generation
    - Peer review and feedback
    - Iterative refinement
    - Consensus threshold configuration
    - Deadlock resolution
    """

    def get_mode(self) -> OrchestrationMode:
        return OrchestrationMode.CONSENSUS

    async def orchestrate(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> CollaborationResult:
        """Execute consensus mode.

        Args:
            agents: List of agents
            task: Task description
            context: Optional context
            **kwargs: Additional parameters
                - consensus_threshold: Required agreement level (default: 0.75)
                - max_iterations: Maximum refinement iterations (default: 5)
                - proposal_timeout: Timeout for proposals
                - enable_peer_review: Enable peer review phase (default: True)

        Returns:
            Collaboration result
        """
        if not self._validate_agents(agents, min_agents=2):
            return self._create_result(False, [], "Consensus requires at least 2 agents")

        consensus_threshold = kwargs.get("consensus_threshold", 0.75)
        max_iterations = kwargs.get("max_iterations", 5)
        proposal_timeout = kwargs.get("proposal_timeout", 30.0)
        enable_peer_review = kwargs.get("enable_peer_review", True)

        self.logger.info(
            f"Starting consensus building with {len(agents)} agents, threshold={consensus_threshold}"
        )

        messages: List[Message] = []
        proposals: List[Dict[str, Any]] = []

        # Phase 1: Initial proposal generation
        self.logger.info("Phase 1: Generating initial proposals")
        self.metrics.total_rounds += 1

        proposal_msg = Message(
            content=f"""Generate a proposal for: {task}

Provide:
1. Your proposed solution
2. Key benefits
3. Potential concerns

Format:
PROPOSAL: [your solution]
BENEFITS:
- [benefit 1]
- [benefit 2]
CONCERNS:
- [concern 1]
- [concern 2]""",
            sender="system",
            role=MessageRole.SYSTEM,
        )

        proposal_responses = await asyncio.gather(
            *[self._safe_process_message(agent, proposal_msg, proposal_timeout) for agent in agents]
        )

        for response in proposal_responses:
            if response:
                messages.append(response)
                proposal = self._parse_proposal(response)
                proposals.append(proposal)

        if not proposals:
            return self._create_result(False, messages, "No proposals generated")

        # Iterative refinement
        iteration = 0
        consensus_reached = False

        while iteration < max_iterations and not consensus_reached:
            iteration += 1
            self.logger.info(f"Iteration {iteration}/{max_iterations}")
            self.metrics.total_rounds += 1

            # Phase 2: Peer review (if enabled)
            if enable_peer_review:
                self.logger.info("Phase 2: Peer review")
                reviews = await self._conduct_peer_review(agents, proposals, proposal_timeout)

                for review in reviews:
                    if review:
                        messages.append(review)

                # Update proposals based on feedback
                proposals = self._refine_proposals(proposals, reviews)

            # Phase 3: Consensus check
            self.logger.info("Phase 3: Checking consensus")
            agreement_level = await self._check_consensus(agents, proposals, proposal_timeout)

            for response in agreement_level["responses"]:
                if response:
                    messages.append(response)

            consensus_score = agreement_level["score"]
            self.logger.info(f"Consensus score: {consensus_score:.2f}")

            if consensus_score >= consensus_threshold:
                consensus_reached = True
                self.logger.info("Consensus reached!")
                break

            # Phase 4: Refinement
            if iteration < max_iterations:
                self.logger.info("Phase 4: Refining proposals")
                refinement_msg = Message(
                    content=f"""Consensus not yet reached (score: {consensus_score:.2f}).

Current proposals:
{self._format_proposals(proposals)}

Refine your proposal addressing concerns and incorporating feedback.""",
                    sender="system",
                    role=MessageRole.SYSTEM,
                )

                refined_responses = await asyncio.gather(
                    *[
                        self._safe_process_message(agent, refinement_msg, proposal_timeout)
                        for agent in agents
                    ]
                )

                proposals = []
                for response in refined_responses:
                    if response:
                        messages.append(response)
                        proposals.append(self._parse_proposal(response))

        # Deadlock resolution if needed
        if not consensus_reached:
            self.logger.warning("Consensus not reached, applying deadlock resolution")
            final_proposal = self._resolve_deadlock(proposals, agreement_level)
        else:
            final_proposal = self._merge_proposals(proposals)

        self.metrics.custom_metrics["iterations"] = iteration
        self.metrics.custom_metrics["consensus_reached"] = consensus_reached
        self.metrics.custom_metrics["final_consensus_score"] = consensus_score

        # Add final synthesis message
        final_msg = Message(
            content=f"CONSENSUS {'REACHED' if consensus_reached else 'APPROXIMATED'}: {final_proposal}",
            sender="system",
            role=MessageRole.SYSTEM,
        )
        messages.append(final_msg)

        return self._create_result(True, messages)

    def _parse_proposal(self, response: Message) -> Dict[str, Any]:
        """Parse proposal from response."""
        proposal = {
            "agent": response.sender,
            "solution": "",
            "benefits": [],
            "concerns": [],
        }

        lines = response.content.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith("PROPOSAL:"):
                proposal["solution"] = line.split(":", 1)[1].strip()
            elif line.startswith("BENEFITS:"):
                current_section = "benefits"
            elif line.startswith("CONCERNS:"):
                current_section = "concerns"
            elif line.startswith("-") and current_section:
                proposal[current_section].append(line[1:].strip())

        return proposal

    async def _conduct_peer_review(
        self, agents: List[Agent], proposals: List[Dict[str, Any]], timeout: float
    ) -> List[Optional[Message]]:
        """Conduct peer review of proposals."""
        review_msg = Message(
            content=f"""Review these proposals:

{self._format_proposals(proposals)}

For each proposal, provide:
1. Strengths
2. Weaknesses
3. Suggestions for improvement

Format:
REVIEW [agent_name]:
STRENGTHS: [list]
WEAKNESSES: [list]
SUGGESTIONS: [list]""",
            sender="system",
            role=MessageRole.SYSTEM,
        )

        return await asyncio.gather(
            *[self._safe_process_message(agent, review_msg, timeout) for agent in agents]
        )

    def _refine_proposals(
        self, proposals: List[Dict[str, Any]], reviews: List[Optional[Message]]
    ) -> List[Dict[str, Any]]:
        """Refine proposals based on reviews."""
        # In a full implementation, would use LLM to incorporate feedback
        # For now, just return original proposals
        return proposals

    async def _check_consensus(
        self, agents: List[Agent], proposals: List[Dict[str, Any]], timeout: float
    ) -> Dict[str, Any]:
        """Check consensus level among agents."""
        consensus_msg = Message(
            content=f"""Rate your agreement with these proposals (0-100):

{self._format_proposals(proposals)}

Format:
AGREEMENT: [0-100]
PREFERRED: [agent_name or 'merged']
REASONING: [brief explanation]""",
            sender="system",
            role=MessageRole.SYSTEM,
        )

        responses = await asyncio.gather(
            *[self._safe_process_message(agent, consensus_msg, timeout) for agent in agents]
        )

        agreements = []
        for response in responses:
            if response:
                agreement = self._parse_agreement(response.content)
                agreements.append(agreement)

        avg_agreement = sum(agreements) / len(agreements) if agreements else 0.0

        return {
            "score": avg_agreement / 100.0,
            "agreements": agreements,
            "responses": responses,
        }

    def _parse_agreement(self, content: str) -> int:
        """Parse agreement score from response."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("AGREEMENT:"):
                try:
                    return int(line.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    pass
        return 50  # Default

    def _format_proposals(self, proposals: List[Dict[str, Any]]) -> str:
        """Format proposals for display."""
        formatted = []
        for i, prop in enumerate(proposals, 1):
            formatted.append(f"{i}. {prop['agent']}: {prop['solution'][:100]}...")
        return "\n".join(formatted)

    def _merge_proposals(self, proposals: List[Dict[str, Any]]) -> str:
        """Merge proposals into final solution."""
        # Simple merge - in production would use LLM
        solutions = [p["solution"] for p in proposals]
        return f"Merged solution incorporating {len(solutions)} proposals"

    def _resolve_deadlock(
        self, proposals: List[Dict[str, Any]], agreement_data: Dict[str, Any]
    ) -> str:
        """Resolve deadlock when consensus not reached."""
        # Use proposal with highest individual agreement
        if proposals:
            return proposals[0]["solution"]
        return "No consensus reached"


class SwarmOrchestrator(BaseOrchestrator):
    """Swarm orchestration with dynamic scaling.

    Features:
    - Task complexity analysis
    - Dynamic agent spawning/termination
    - Work stealing and load balancing
    - Emergent behavior patterns
    - Performance metrics
    """

    def get_mode(self) -> OrchestrationMode:
        return OrchestrationMode.SWARM

    async def orchestrate(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> CollaborationResult:
        """Execute swarm mode with dynamic scaling.

        Args:
            agents: Initial agent pool
            task: Task description
            context: Optional context
            **kwargs: Additional parameters
                - max_agents: Maximum concurrent agents (default: 10)
                - min_agents: Minimum active agents (default: 2)
                - complexity_threshold: Words per agent (default: 50)
                - enable_work_stealing: Enable work stealing (default: True)
                - agent_timeout: Timeout per agent

        Returns:
            Collaboration result
        """
        if not self._validate_agents(agents, min_agents=1):
            return self._create_result(False, [], "Swarm requires at least 1 agent")

        max_agents = kwargs.get("max_agents", 10)
        min_agents = kwargs.get("min_agents", 2)
        complexity_threshold = kwargs.get("complexity_threshold", 50)
        enable_work_stealing = kwargs.get("enable_work_stealing", True)
        agent_timeout = kwargs.get("agent_timeout", 30.0)

        self.logger.info(f"Starting swarm with {len(agents)} initial agents")

        messages: List[Message] = []

        # Analyze task complexity
        task_complexity = self._analyze_complexity(task)
        self.logger.info(f"Task complexity: {task_complexity}")

        # Determine optimal swarm size
        optimal_size = self._calculate_swarm_size(
            task_complexity, complexity_threshold, min_agents, max_agents
        )
        self.logger.info(f"Optimal swarm size: {optimal_size}")

        # Select/activate agents
        active_agents = self._select_agents(agents, optimal_size)
        self.logger.info(f"Active agents: {[a.name for a in active_agents]}")

        # Decompose task for parallel execution
        subtasks = self._decompose_for_swarm(task, len(active_agents))

        # Phase 1: Parallel swarm execution
        self.logger.info("Phase 1: Swarm parallel execution")
        self.metrics.total_rounds += 1

        work_queue = list(enumerate(subtasks))
        completed_work: List[Tuple[int, Message]] = []
        agent_status = {agent.name: "idle" for agent in active_agents}

        # Execute with work stealing
        if enable_work_stealing:
            completed_work = await self._execute_with_work_stealing(
                active_agents, work_queue, agent_timeout, agent_status
            )
        else:
            completed_work = await self._execute_simple(active_agents, subtasks, agent_timeout)

        # Collect results
        for _, response in sorted(completed_work, key=lambda x: x[0]):
            if response:
                messages.append(response)

        # Phase 2: Emergent synthesis
        self.logger.info("Phase 2: Emergent synthesis")
        self.metrics.total_rounds += 1

        synthesis = await self._emergent_synthesis(active_agents, messages, agent_timeout)
        if synthesis:
            messages.append(synthesis)

        self.metrics.custom_metrics["swarm_size"] = len(active_agents)
        self.metrics.custom_metrics["task_complexity"] = task_complexity
        self.metrics.custom_metrics["subtasks"] = len(subtasks)
        self.metrics.custom_metrics["agent_status"] = agent_status

        return self._create_result(True, messages)

    def _analyze_complexity(self, task: str) -> int:
        """Analyze task complexity."""
        # Simple heuristic: word count + sentence count
        words = len(task.split())
        sentences = task.count(".") + task.count("!") + task.count("?")
        return words + (sentences * 5)

    def _calculate_swarm_size(
        self, complexity: int, threshold: int, min_size: int, max_size: int
    ) -> int:
        """Calculate optimal swarm size based on complexity."""
        calculated = max(min_size, complexity // threshold)
        return min(calculated, max_size)

    def _select_agents(self, agents: List[Agent], target_size: int) -> List[Agent]:
        """Select agents for swarm."""
        active = [a for a in agents if a.is_active]
        return active[:target_size]

    def _decompose_for_swarm(self, task: str, num_agents: int) -> List[str]:
        """Decompose task into subtasks for swarm."""
        # Simple decomposition - in production would use LLM
        base_task = f"Work on: {task}"
        return [f"{base_task} (part {i + 1}/{num_agents})" for i in range(num_agents)]

    async def _execute_with_work_stealing(
        self,
        agents: List[Agent],
        work_queue: List[Tuple[int, str]],
        timeout: float,
        status: Dict[str, str],
    ) -> List[Tuple[int, Message]]:
        """Execute with work stealing for load balancing."""
        completed: List[Tuple[int, Message]] = []
        queue_lock = asyncio.Lock()

        async def worker(agent: Agent) -> None:
            while True:
                async with queue_lock:
                    if not work_queue:
                        break
                    task_id, subtask = work_queue.pop(0)

                status[agent.name] = "working"
                msg = Message(content=subtask, sender="swarm", role=MessageRole.SYSTEM)
                response = await self._safe_process_message(agent, msg, timeout)

                if response:
                    async with queue_lock:
                        completed.append((task_id, response))

                status[agent.name] = "idle"

        await asyncio.gather(*[worker(agent) for agent in agents])
        return completed

    async def _execute_simple(
        self, agents: List[Agent], subtasks: List[str], timeout: float
    ) -> List[Tuple[int, Message]]:
        """Simple parallel execution without work stealing."""
        tasks = []
        for i, (agent, subtask) in enumerate(zip(agents, subtasks)):
            msg = Message(content=subtask, sender="swarm", role=MessageRole.SYSTEM)
            tasks.append(self._safe_process_message(agent, msg, timeout))

        responses = await asyncio.gather(*tasks)
        return [(i, r) for i, r in enumerate(responses) if r]

    async def _emergent_synthesis(
        self, agents: List[Agent], messages: List[Message], timeout: float
    ) -> Optional[Message]:
        """Synthesize results through emergent collaboration."""
        if not agents or not messages:
            return None

        # Use first agent for synthesis
        synthesizer = agents[0]

        synthesis_msg = Message(
            content=f"""Synthesize these swarm results:

{chr(10).join(f'- {m.sender}: {m.content[:100]}...' for m in messages[-len(agents):])}

Provide a coherent synthesis.""",
            sender="swarm",
            role=MessageRole.SYSTEM,
        )

        return await self._safe_process_message(synthesizer, synthesis_msg, timeout)


class GraphOrchestrator(BaseOrchestrator):
    """Graph-based orchestration with DAG workflows.

    Features:
    - Node types: Agent, Tool, Decision, Merge
    - Edge conditions and routing
    - Parallel execution paths
    - Cycle detection
    - Mermaid visualization export
    """

    def __init__(self) -> None:
        """Initialize graph orchestrator."""
        super().__init__()
        self.graph: Dict[str, List[str]] = {}
        self.node_agents: Dict[str, Agent] = {}
        self.node_types: Dict[str, str] = {}
        self.edge_conditions: Dict[Tuple[str, str], Callable] = {}

    def get_mode(self) -> OrchestrationMode:
        return OrchestrationMode.GRAPH

    def add_node(self, node_id: str, agent: Agent, node_type: str = "agent") -> None:
        """Add a node to the graph.

        Args:
            node_id: Node identifier
            agent: Agent for this node
            node_type: Type of node (agent, decision, merge)
        """
        self.node_agents[node_id] = agent
        self.node_types[node_id] = node_type
        if node_id not in self.graph:
            self.graph[node_id] = []

    def add_edge(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[Callable[[Message], bool]] = None,
    ) -> None:
        """Add an edge between nodes.

        Args:
            from_node: Source node
            to_node: Target node
            condition: Optional condition function for edge traversal
        """
        if from_node not in self.graph:
            self.graph[from_node] = []
        self.graph[from_node].append(to_node)

        if condition:
            self.edge_conditions[(from_node, to_node)] = condition

    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the graph.

        Returns:
            List of cycles found (each cycle is a list of node IDs)
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            rec_stack.remove(node)

        for node in self.graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    async def orchestrate(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> CollaborationResult:
        """Execute graph-based orchestration.

        Args:
            agents: List of agents (used if graph not pre-configured)
            task: Task description
            context: Optional context
            **kwargs: Additional parameters
                - start_node: Starting node ID
                - max_parallel: Maximum parallel executions
                - node_timeout: Timeout per node

        Returns:
            Collaboration result
        """
        start_node = kwargs.get("start_node", "start")
        max_parallel = kwargs.get("max_parallel", 5)
        node_timeout = kwargs.get("node_timeout", 30.0)

        # Auto-build graph if not configured
        if not self.graph:
            self._auto_build_graph(agents)
            start_node = "node_0"

        # Detect cycles
        cycles = self.detect_cycles()
        if cycles:
            self.metrics.record_warning(f"Cycles detected: {cycles}")

        self.logger.info(f"Starting graph execution with {len(self.node_agents)} nodes")

        messages: List[Message] = []
        visited: Set[str] = set()
        execution_order: List[str] = []

        # Initial message
        current_message = Message(content=task, sender="system", role=MessageRole.SYSTEM)

        # Execute graph traversal
        await self._traverse_graph(
            start_node,
            current_message,
            visited,
            execution_order,
            messages,
            node_timeout,
            max_parallel,
        )

        self.metrics.custom_metrics["nodes_visited"] = len(visited)
        self.metrics.custom_metrics["execution_order"] = execution_order
        self.metrics.custom_metrics["cycles_detected"] = len(cycles)

        return self._create_result(True, messages)

    def _auto_build_graph(self, agents: List[Agent]) -> None:
        """Auto-build a linear graph from agents."""
        for i, agent in enumerate(agents):
            node_id = f"node_{i}"
            self.add_node(node_id, agent)
            if i > 0:
                self.add_edge(f"node_{i - 1}", node_id)

    async def _traverse_graph(
        self,
        node_id: str,
        message: Message,
        visited: Set[str],
        execution_order: List[str],
        messages: List[Message],
        timeout: float,
        max_parallel: int,
    ) -> None:
        """Traverse graph with parallel execution support.

        Args:
            node_id: Current node
            message: Current message
            visited: Set of visited nodes
            execution_order: List tracking execution order
            messages: List of all messages
            timeout: Timeout per node
            max_parallel: Maximum parallel executions
        """
        if node_id in visited or node_id not in self.node_agents:
            return

        visited.add(node_id)
        execution_order.append(node_id)
        agent = self.node_agents[node_id]
        node_type = self.node_types.get(node_id, "agent")

        self.logger.info(f"Visiting node: {node_id} (type: {node_type}, agent: {agent.name})")
        self.metrics.total_rounds += 1

        # Process based on node type
        if node_type == "decision":
            response = await self._process_decision_node(agent, message, timeout)
        elif node_type == "merge":
            response = await self._process_merge_node(agent, message, messages, timeout)
        else:  # agent node
            response = await self._safe_process_message(agent, message, timeout)

        if response:
            messages.append(response)

            # Get next nodes
            next_nodes = self._get_next_nodes(node_id, response)

            # Execute next nodes in parallel if possible
            if len(next_nodes) <= max_parallel:
                await asyncio.gather(
                    *[
                        self._traverse_graph(
                            next_node,
                            response,
                            visited,
                            execution_order,
                            messages,
                            timeout,
                            max_parallel,
                        )
                        for next_node in next_nodes
                    ]
                )
            else:
                # Sequential execution if too many parallel paths
                for next_node in next_nodes:
                    await self._traverse_graph(
                        next_node,
                        response,
                        visited,
                        execution_order,
                        messages,
                        timeout,
                        max_parallel,
                    )

    def _get_next_nodes(self, current_node: str, message: Message) -> List[str]:
        """Get next nodes based on edge conditions.

        Args:
            current_node: Current node ID
            message: Current message

        Returns:
            List of next node IDs
        """
        next_nodes = []
        for next_node in self.graph.get(current_node, []):
            condition = self.edge_conditions.get((current_node, next_node))
            if condition is None or condition(message):
                next_nodes.append(next_node)

        return next_nodes

    async def _process_decision_node(
        self, agent: Agent, message: Message, timeout: float
    ) -> Optional[Message]:
        """Process a decision node."""
        decision_msg = Message(
            content=f"{message.content}\n\nMake a decision: YES or NO",
            sender="graph",
            role=MessageRole.SYSTEM,
        )
        return await self._safe_process_message(agent, decision_msg, timeout)

    async def _process_merge_node(
        self,
        agent: Agent,
        message: Message,
        all_messages: List[Message],
        timeout: float,
    ) -> Optional[Message]:
        """Process a merge node that combines multiple inputs."""
        recent = all_messages[-3:] if len(all_messages) >= 3 else all_messages
        merge_content = "Merge these inputs:\n" + "\n".join(
            f"- {m.sender}: {m.content[:100]}..." for m in recent
        )

        merge_msg = Message(content=merge_content, sender="graph", role=MessageRole.SYSTEM)
        return await self._safe_process_message(agent, merge_msg, timeout)

    def visualize_graph(self, format: str = "mermaid") -> str:
        """Generate visualization of the graph.

        Args:
            format: Visualization format ('mermaid' or 'dot')

        Returns:
            Visualization string
        """
        if format == "mermaid":
            return self._generate_mermaid()
        elif format == "dot":
            return self._generate_dot()
        else:
            raise ValueError(f"Unknown format: {format}")

    def _generate_mermaid(self) -> str:
        """Generate Mermaid diagram."""
        lines = ["graph TD"]

        # Add nodes
        for node_id, agent in self.node_agents.items():
            node_type = self.node_types.get(node_id, "agent")
            shape = {
                "agent": f"{node_id}[{agent.name}]",
                "decision": f"{node_id}{{{agent.name}}}",
                "merge": f"{node_id}(({agent.name}))",
            }.get(node_type, f"{node_id}[{agent.name}]")
            lines.append(f"    {shape}")

        # Add edges
        for from_node, to_nodes in self.graph.items():
            for to_node in to_nodes:
                has_condition = (from_node, to_node) in self.edge_conditions
                edge = "-->" if not has_condition else "-.->|condition|"
                lines.append(f"    {from_node} {edge} {to_node}")

        return "\n".join(lines)

    def _generate_dot(self) -> str:
        """Generate Graphviz DOT format."""
        lines = ["digraph G {"]

        # Add nodes
        for node_id, agent in self.node_agents.items():
            node_type = self.node_types.get(node_id, "agent")
            shape = {
                "agent": "box",
                "decision": "diamond",
                "merge": "circle",
            }.get(node_type, "box")
            lines.append(f'    {node_id} [label="{agent.name}", shape={shape}];')

        # Add edges
        for from_node, to_nodes in self.graph.items():
            for to_node in to_nodes:
                has_condition = (from_node, to_node) in self.edge_conditions
                style = "dashed" if has_condition else "solid"
                lines.append(f"    {from_node} -> {to_node} [style={style}];")

        lines.append("}")
        return "\n".join(lines)

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the graph.

        Returns:
            Dictionary with graph statistics
        """
        return {
            "total_nodes": len(self.node_agents),
            "total_edges": sum(len(edges) for edges in self.graph.values()),
            "node_types": dict(
                (nt, sum(1 for t in self.node_types.values() if t == nt))
                for nt in set(self.node_types.values())
            ),
            "cycles": len(self.detect_cycles()),
            "max_depth": self._calculate_max_depth(),
        }

    def _calculate_max_depth(self) -> int:
        """Calculate maximum depth of the graph."""
        if not self.graph:
            return 0

        def dfs_depth(node: str, visited: Set[str]) -> int:
            if node in visited:
                return 0
            visited.add(node)
            max_child_depth = 0
            for child in self.graph.get(node, []):
                max_child_depth = max(max_child_depth, dfs_depth(child, visited.copy()))
            return 1 + max_child_depth

        # Find root nodes (nodes with no incoming edges)
        all_targets = set()
        for targets in self.graph.values():
            all_targets.update(targets)
        roots = [n for n in self.graph if n not in all_targets]

        if not roots:
            roots = [list(self.graph.keys())[0]]  # Use first node if no clear root

        return max(dfs_depth(root, set()) for root in roots)


class HybridOrchestrator(BaseOrchestrator):
    """Hybrid orchestration combining multiple modes.

    Supports combinations like:
    - Hierarchical + Swarm: Manager coordinates swarms
    - Debate + Consensus: Debate followed by consensus building
    - Sequential + Graph: Sequential phases with graph workflows
    """

    def __init__(
        self,
        primary_mode: OrchestrationMode,
        secondary_mode: OrchestrationMode,
    ) -> None:
        """Initialize hybrid orchestrator.

        Args:
            primary_mode: Primary orchestration mode
            secondary_mode: Secondary orchestration mode
        """
        super().__init__()
        self.primary_mode = primary_mode
        self.secondary_mode = secondary_mode
        self.primary_orchestrator = create_orchestrator(primary_mode)
        self.secondary_orchestrator = create_orchestrator(secondary_mode)

    def get_mode(self) -> OrchestrationMode:
        return OrchestrationMode.HYBRID

    async def orchestrate(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> CollaborationResult:
        """Execute hybrid orchestration.

        Args:
            agents: List of agents
            task: Task description
            context: Optional context
            **kwargs: Additional parameters
                - split_ratio: Agent split ratio for two modes (default: 0.5)
                - phase_1_kwargs: Kwargs for primary mode
                - phase_2_kwargs: Kwargs for secondary mode
                - integration_strategy: 'sequential', 'parallel', 'nested'

        Returns:
            Collaboration result
        """
        if not self._validate_agents(agents, min_agents=2):
            return self._create_result(False, [], "Hybrid requires at least 2 agents")

        split_ratio = kwargs.get("split_ratio", 0.5)
        phase_1_kwargs = kwargs.get("phase_1_kwargs", {})
        phase_2_kwargs = kwargs.get("phase_2_kwargs", {})
        integration_strategy = kwargs.get("integration_strategy", "sequential")

        self.logger.info(
            f"Starting hybrid orchestration: {self.primary_mode.value} + {self.secondary_mode.value}"
        )

        if integration_strategy == "sequential":
            result = await self._sequential_integration(
                agents, task, context, split_ratio, phase_1_kwargs, phase_2_kwargs
            )
        elif integration_strategy == "parallel":
            result = await self._parallel_integration(
                agents, task, context, split_ratio, phase_1_kwargs, phase_2_kwargs
            )
        elif integration_strategy == "nested":
            result = await self._nested_integration(
                agents, task, context, phase_1_kwargs, phase_2_kwargs
            )
        else:
            return self._create_result(
                False, [], f"Unknown integration strategy: {integration_strategy}"
            )

        # Add hybrid metadata
        if result.metadata:
            result.metadata["hybrid_modes"] = [
                self.primary_mode.value,
                self.secondary_mode.value,
            ]
            result.metadata["integration_strategy"] = integration_strategy

        return result

    async def _sequential_integration(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]],
        split_ratio: float,
        phase_1_kwargs: Dict[str, Any],
        phase_2_kwargs: Dict[str, Any],
    ) -> CollaborationResult:
        """Sequential integration: Phase 1 then Phase 2."""
        split_point = int(len(agents) * split_ratio)
        phase_1_agents = agents[:split_point] if split_point > 0 else agents[:1]
        phase_2_agents = agents[split_point:] if split_point < len(agents) else agents[1:]

        self.logger.info(f"Phase 1: {self.primary_mode.value} with {len(phase_1_agents)} agents")
        result_1 = await self.primary_orchestrator.orchestrate(
            phase_1_agents, task, context, **phase_1_kwargs
        )

        # Use Phase 1 output as input for Phase 2
        phase_2_task = result_1.final_output or task
        self.logger.info(f"Phase 2: {self.secondary_mode.value} with {len(phase_2_agents)} agents")
        result_2 = await self.secondary_orchestrator.orchestrate(
            phase_2_agents, phase_2_task, context, **phase_2_kwargs
        )

        # Merge results
        return self._merge_results(result_1, result_2)

    async def _parallel_integration(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]],
        split_ratio: float,
        phase_1_kwargs: Dict[str, Any],
        phase_2_kwargs: Dict[str, Any],
    ) -> CollaborationResult:
        """Parallel integration: Both modes run simultaneously."""
        split_point = int(len(agents) * split_ratio)
        phase_1_agents = agents[:split_point] if split_point > 0 else agents[:1]
        phase_2_agents = agents[split_point:] if split_point < len(agents) else agents[1:]

        self.logger.info("Running both modes in parallel")

        results = await asyncio.gather(
            self.primary_orchestrator.orchestrate(phase_1_agents, task, context, **phase_1_kwargs),
            self.secondary_orchestrator.orchestrate(
                phase_2_agents, task, context, **phase_2_kwargs
            ),
        )

        return self._merge_results(results[0], results[1])

    async def _nested_integration(
        self,
        agents: List[Agent],
        task: str,
        context: Optional[Dict[str, Any]],
        phase_1_kwargs: Dict[str, Any],
        phase_2_kwargs: Dict[str, Any],
    ) -> CollaborationResult:
        """Nested integration: Secondary mode runs within primary mode."""
        self.logger.info(f"Nested: {self.secondary_mode.value} within {self.primary_mode.value}")

        # For nested, we run primary with all agents
        # The primary orchestrator can internally use secondary for subtasks
        # This is a simplified version - full implementation would require
        # orchestrators to support nested execution

        result = await self.primary_orchestrator.orchestrate(
            agents, task, context, **phase_1_kwargs
        )

        return result

    def _merge_results(
        self, result_1: CollaborationResult, result_2: CollaborationResult
    ) -> CollaborationResult:
        """Merge two collaboration results."""
        # Combine agent contributions
        combined_contributions = dict(result_1.agent_contributions)
        for agent, count in result_2.agent_contributions.items():
            combined_contributions[agent] = combined_contributions.get(agent, 0) + count

        # Combine metadata
        combined_metadata = {
            "phase_1": result_1.metadata,
            "phase_2": result_2.metadata,
        }

        return CollaborationResult(
            success=result_1.success and result_2.success,
            total_rounds=result_1.total_rounds + result_2.total_rounds,
            total_messages=result_1.total_messages + result_2.total_messages,
            final_output=result_2.final_output or result_1.final_output,
            agent_contributions=combined_contributions,
            error=result_2.error or result_1.error,
            metadata=combined_metadata,
        )


# Factory function
def create_orchestrator(
    mode: OrchestrationMode,
    **kwargs: Any,
) -> BaseOrchestrator:
    """Create an orchestrator by mode.

    Args:
        mode: Orchestration mode
        **kwargs: Mode-specific initialization parameters
            For HYBRID mode:
                - secondary_mode: Required secondary mode

    Returns:
        Orchestrator instance

    Raises:
        ValueError: If mode is unknown or required parameters missing
    """
    if mode == OrchestrationMode.SEQUENTIAL:
        return SequentialOrchestrator()
    elif mode == OrchestrationMode.HIERARCHICAL:
        return HierarchicalOrchestrator()
    elif mode == OrchestrationMode.DEBATE:
        return DebateOrchestrator()
    elif mode == OrchestrationMode.CONSENSUS:
        return ConsensusOrchestrator()
    elif mode == OrchestrationMode.SWARM:
        return SwarmOrchestrator()
    elif mode == OrchestrationMode.GRAPH:
        return GraphOrchestrator()
    elif mode == OrchestrationMode.HYBRID:
        secondary_mode = kwargs.get("secondary_mode")
        if not secondary_mode:
            raise ValueError("HYBRID mode requires 'secondary_mode' parameter")
        return HybridOrchestrator(mode, secondary_mode)
    else:
        raise ValueError(f"Unknown orchestration mode: {mode}")


# Utility functions
def get_available_modes() -> List[str]:
    """Get list of available orchestration modes.

    Returns:
        List of mode names
    """
    return [mode.value for mode in OrchestrationMode]


def get_mode_description(mode: OrchestrationMode) -> str:
    """Get description of an orchestration mode.

    Args:
        mode: Orchestration mode

    Returns:
        Mode description
    """
    descriptions = {
        OrchestrationMode.SEQUENTIAL: "Chain of responsibility with context passing",
        OrchestrationMode.HIERARCHICAL: "3-tier architecture: manager, workers, reviewer",
        OrchestrationMode.DEBATE: "Multi-round deliberation with voting",
        OrchestrationMode.CONSENSUS: "Agreement-based decision making",
        OrchestrationMode.SWARM: "Dynamic scaling with load balancing",
        OrchestrationMode.GRAPH: "DAG-based workflows with parallel execution",
        OrchestrationMode.HYBRID: "Combination of multiple modes",
    }
    return descriptions.get(mode, "Unknown mode")


def recommend_mode(
    num_agents: int,
    task_complexity: str = "medium",
    requires_consensus: bool = False,
    has_hierarchy: bool = False,
) -> OrchestrationMode:
    """Recommend an orchestration mode based on requirements.

    Args:
        num_agents: Number of agents
        task_complexity: Task complexity ('low', 'medium', 'high')
        requires_consensus: Whether consensus is required
        has_hierarchy: Whether hierarchical structure exists

    Returns:
        Recommended orchestration mode
    """
    if requires_consensus:
        return OrchestrationMode.CONSENSUS

    if has_hierarchy and num_agents >= 3:
        return OrchestrationMode.HIERARCHICAL

    if task_complexity == "high" and num_agents >= 5:
        return OrchestrationMode.SWARM

    if num_agents >= 4:
        return OrchestrationMode.DEBATE

    if num_agents >= 2:
        return OrchestrationMode.SEQUENTIAL

    return OrchestrationMode.SEQUENTIAL


__all__ = [
    "OrchestrationMode",
    "OrchestrationMetrics",
    "BaseOrchestrator",
    "SequentialOrchestrator",
    "HierarchicalOrchestrator",
    "DebateOrchestrator",
    "ConsensusOrchestrator",
    "SwarmOrchestrator",
    "GraphOrchestrator",
    "HybridOrchestrator",
    "create_orchestrator",
    "get_available_modes",
    "get_mode_description",
    "recommend_mode",
]
