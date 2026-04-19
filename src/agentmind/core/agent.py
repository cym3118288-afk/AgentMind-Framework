"""Core agent implementation for AgentMind framework.

This module provides the Agent class which represents an individual agent
in the multi-agent system with memory, role-based behavior, and message processing.

Enhanced with:
- Advanced state machine (IDLE → THINKING → EXECUTING → WAITING_HUMAN → DELEGATING → ERROR → RECOVERING)
- Multi-modal capabilities (images, audio, video, documents)
- Human-in-the-loop workflows
- Sub-agent management
- Learning and adaptation
- State persistence and recovery
"""

import json
import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..llm.provider import LLMProvider
from ..prompts import get_system_prompt
from ..tools import ToolRegistry, get_global_registry
from .types import AgentConfig, AgentRole, Message, MessageRole


class AgentState(str, Enum):
    """Advanced agent execution states."""

    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING_HUMAN = "waiting_human"
    DELEGATING = "delegating"
    ERROR = "error"
    RECOVERING = "recovering"


class ContentType(str, Enum):
    """Multi-modal content types."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    STRUCTURED = "structured"


class ApprovalPolicy(str, Enum):
    """Human approval policies."""

    ALWAYS = "always"  # Always require approval
    NEVER = "never"  # Never require approval
    ON_TOOL_USE = "on_tool_use"  # Require approval for tool usage
    ON_HIGH_RISK = "on_high_risk"  # Require approval for high-risk actions
    ON_ERROR = "on_error"  # Require approval after errors


class Agent:
    """An intelligent agent that can process messages and collaborate with other agents.

    The Agent class represents a single agent in the multi-agent system. Each agent
    has a unique name, role, memory, and can process incoming messages to generate
    responses based on its role and configuration.

    Enhanced Features:
    - Advanced state machine with transitions and hooks
    - Multi-modal message support (text, images, audio, video, documents)
    - Human-in-the-loop workflows with approval policies
    - Sub-agent management and delegation
    - Learning and adaptation with performance tracking
    - State persistence and recovery

    Attributes:
        name: Unique identifier for this agent
        role: The agent's role (analyst, creative, coordinator, etc.)
        config: Full configuration for the agent
        memory: List of messages this agent has seen/sent
        is_active: Whether the agent is currently active
        state: Current execution state
        sub_agents: List of child agents
        performance_metrics: Performance tracking data

    Example:
        >>> agent = Agent(name="analyst_1", role="analyst")
        >>> message = Message(content="Analyze this data", sender="system")
        >>> response = await agent.process_message(message)
        >>> print(response.content)
    """

    def __init__(
        self,
        name: str,
        role: str = "assistant",
        config: Optional[AgentConfig] = None,
        llm_provider: Optional[LLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
        human_in_loop: bool = False,
        approval_policy: ApprovalPolicy = ApprovalPolicy.NEVER,
        human_callback: Optional[Callable] = None,
        enable_learning: bool = True,
    ) -> None:
        """Initialize a new agent.

        Args:
            name: Unique name for the agent
            role: Role of the agent (analyst, creative, coordinator, etc.)
            config: Optional full configuration. If not provided, creates default config.
            llm_provider: Optional LLM provider for intelligent responses
            tool_registry: Optional tool registry (defaults to global registry)
            human_in_loop: Enable human-in-the-loop workflows
            approval_policy: Policy for when to request human approval
            human_callback: Callback function for human interaction
            enable_learning: Enable learning and adaptation features

        Raises:
            ValueError: If name is empty or invalid
        """
        if not name or not name.strip():
            raise ValueError("Agent name cannot be empty")

        self.name = name
        self.role = role

        # Create config if not provided
        if config is None:
            self.config = AgentConfig(name=name, role=role)
        else:
            self.config = config

        self.memory: List[Message] = []
        self.is_active = True
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry or get_global_registry()

        # Bind tools from config
        self._available_tools = self._bind_tools()

        # Advanced state management
        self.state = AgentState.IDLE
        self.state_history: List[Dict[str, Any]] = []
        self.state_hooks: Dict[str, List[Callable]] = {
            "on_enter": [],
            "on_exit": [],
            "on_transition": [],
        }

        # Human-in-the-loop
        self.human_in_loop = human_in_loop
        self.approval_policy = approval_policy
        self.human_callback = human_callback
        self.pending_approvals: List[Dict[str, Any]] = []

        # Sub-agent management
        self.sub_agents: List["Agent"] = []
        self.parent_agent: Optional["Agent"] = None
        self.delegation_history: List[Dict[str, Any]] = []

        # Learning and adaptation
        self.enable_learning = enable_learning
        self.performance_metrics = {
            "total_messages": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "tool_calls": 0,
            "successful_tool_calls": 0,
            "human_interventions": 0,
            "delegations": 0,
            "average_response_time": 0.0,
            "error_count": 0,
        }
        self.feedback_history: List[Dict[str, Any]] = []
        self.ab_tests: Dict[str, Dict[str, Any]] = {}

        # Multi-modal support
        self.supported_content_types = [ContentType.TEXT]
        self.streaming_enabled = False

    # ==================== State Management ====================

    def transition_state(
        self, new_state: AgentState, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Transition to a new state with hooks and history tracking.

        Args:
            new_state: The state to transition to
            metadata: Optional metadata about the transition
        """
        old_state = self.state

        # Call on_exit hooks for old state
        self._call_state_hooks("on_exit", old_state, new_state, metadata)

        # Record transition
        transition = {
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.state_history.append(transition)

        # Update state
        self.state = new_state

        # Call on_enter hooks for new state
        self._call_state_hooks("on_enter", old_state, new_state, metadata)

        # Call on_transition hooks
        self._call_state_hooks("on_transition", old_state, new_state, metadata)

    def add_state_hook(
        self, hook_type: str, callback: Callable[[AgentState, AgentState, Optional[Dict]], None]
    ) -> None:
        """Add a state transition hook.

        Args:
            hook_type: Type of hook ('on_enter', 'on_exit', 'on_transition')
            callback: Callback function to execute
        """
        if hook_type in self.state_hooks:
            self.state_hooks[hook_type].append(callback)

    def _call_state_hooks(
        self,
        hook_type: str,
        old_state: AgentState,
        new_state: AgentState,
        metadata: Optional[Dict[str, Any]],
    ) -> None:
        """Call registered state hooks.

        Args:
            hook_type: Type of hook to call
            old_state: Previous state
            new_state: New state
            metadata: Transition metadata
        """
        for hook in self.state_hooks.get(hook_type, []):
            try:
                hook(old_state, new_state, metadata)
            except Exception as e:
                print(f"[!] State hook error in {self.name}: {e}")

    def get_state_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent state transition history.

        Args:
            limit: Maximum number of transitions to return

        Returns:
            List of state transitions
        """
        return self.state_history[-limit:] if self.state_history else []

    # ==================== Multi-Modal Support ====================

    def enable_multimodal(
        self, content_types: List[ContentType], streaming: bool = False
    ) -> None:
        """Enable multi-modal content support.

        Args:
            content_types: List of content types to support
            streaming: Enable streaming input/output
        """
        self.supported_content_types = content_types
        self.streaming_enabled = streaming
        print(f"[*] Agent {self.name} enabled multi-modal: {[ct.value for ct in content_types]}")

    def validate_content_type(self, content_type: ContentType) -> bool:
        """Validate if a content type is supported.

        Args:
            content_type: Content type to validate

        Returns:
            True if supported
        """
        return content_type in self.supported_content_types

    async def process_multimodal_message(
        self, message: Message, content_type: ContentType = ContentType.TEXT
    ) -> Optional[Message]:
        """Process a multi-modal message.

        Args:
            message: Message to process
            content_type: Type of content in the message

        Returns:
            Response message
        """
        if not self.validate_content_type(content_type):
            return Message(
                content=f"Content type {content_type.value} not supported",
                sender=self.name,
                role=MessageRole.AGENT,
                metadata={"error": "unsupported_content_type"},
            )

        # Add content type to metadata
        message.metadata["content_type"] = content_type.value

        # Process based on content type
        if content_type == ContentType.TEXT:
            return await self.process_message(message)
        else:
            # For non-text content, add description to message
            enhanced_content = f"[{content_type.value.upper()} CONTENT] {message.content}"
            enhanced_message = Message(
                content=enhanced_content,
                sender=message.sender,
                role=message.role,
                metadata=message.metadata,
            )
            return await self.process_message(enhanced_message)

    # ==================== Human-in-the-Loop ====================

    async def request_human_approval(
        self, action: str, context: Dict[str, Any]
    ) -> bool:
        """Request human approval for an action.

        Args:
            action: Description of the action
            context: Context information

        Returns:
            True if approved, False otherwise
        """
        if not self.human_in_loop or not self.human_callback:
            return True

        self.transition_state(AgentState.WAITING_HUMAN, {"action": action})

        approval_request = {
            "agent": self.name,
            "action": action,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }

        self.pending_approvals.append(approval_request)

        try:
            # Call human callback
            if asyncio.iscoroutinefunction(self.human_callback):
                approved = await self.human_callback(approval_request)
            else:
                approved = self.human_callback(approval_request)

            self.pending_approvals.remove(approval_request)

            if approved:
                self.transition_state(AgentState.IDLE)
            else:
                self.performance_metrics["human_interventions"] += 1

            return bool(approved)

        except Exception as e:
            print(f"[!] Human callback error in {self.name}: {e}")
            self.pending_approvals.remove(approval_request)
            self.transition_state(AgentState.ERROR, {"error": str(e)})
            return False

    def should_request_approval(self, action_type: str) -> bool:
        """Determine if approval is needed based on policy.

        Args:
            action_type: Type of action ('tool_use', 'delegation', 'message')

        Returns:
            True if approval is needed
        """
        if self.approval_policy == ApprovalPolicy.ALWAYS:
            return True
        elif self.approval_policy == ApprovalPolicy.NEVER:
            return False
        elif self.approval_policy == ApprovalPolicy.ON_TOOL_USE:
            return action_type == "tool_use"
        elif self.approval_policy == ApprovalPolicy.ON_HIGH_RISK:
            # Define high-risk actions
            return action_type in ["tool_use", "delegation"]
        elif self.approval_policy == ApprovalPolicy.ON_ERROR:
            return self.state == AgentState.ERROR
        return False

    async def collect_feedback(self, feedback: Dict[str, Any]) -> None:
        """Collect feedback on agent performance.

        Args:
            feedback: Feedback data (rating, comments, etc.)
        """
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback,
            "state": self.state.value,
        }
        self.feedback_history.append(feedback_entry)

        if self.enable_learning:
            await self._adapt_from_feedback(feedback)

    async def request_clarification(self, question: str) -> Optional[str]:
        """Request clarification from human.

        Args:
            question: Question to ask

        Returns:
            Human response or None
        """
        if not self.human_callback:
            return None

        clarification_request = {
            "agent": self.name,
            "type": "clarification",
            "question": question,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            if asyncio.iscoroutinefunction(self.human_callback):
                response = await self.human_callback(clarification_request)
            else:
                response = self.human_callback(clarification_request)

            return str(response) if response else None

        except Exception as e:
            print(f"[!] Clarification request error in {self.name}: {e}")
            return None

    # ==================== Sub-Agent Management ====================

    def add_sub_agent(self, agent: "Agent") -> None:
        """Add a child agent for delegation.

        Args:
            agent: Sub-agent to add
        """
        if agent not in self.sub_agents:
            self.sub_agents.append(agent)
            agent.parent_agent = self
            print(f"[+] Agent {self.name} added sub-agent: {agent.name}")

    def remove_sub_agent(self, agent_name: str) -> bool:
        """Remove a sub-agent.

        Args:
            agent_name: Name of sub-agent to remove

        Returns:
            True if removed successfully
        """
        for i, agent in enumerate(self.sub_agents):
            if agent.name == agent_name:
                agent.parent_agent = None
                self.sub_agents.pop(i)
                print(f"[-] Agent {self.name} removed sub-agent: {agent_name}")
                return True
        return False

    async def delegate_task(
        self, sub_agent_name: str, task: Message, require_approval: bool = False
    ) -> Optional[Message]:
        """Delegate a task to a sub-agent.

        Args:
            sub_agent_name: Name of sub-agent
            task: Task message
            require_approval: Whether to require human approval

        Returns:
            Sub-agent response or None
        """
        # Find sub-agent
        sub_agent = None
        for agent in self.sub_agents:
            if agent.name == sub_agent_name:
                sub_agent = agent
                break

        if not sub_agent:
            print(f"[!] Sub-agent not found: {sub_agent_name}")
            return None

        # Check approval if needed
        if require_approval or self.should_request_approval("delegation"):
            approved = await self.request_human_approval(
                f"Delegate to {sub_agent_name}",
                {"task": task.content, "sub_agent": sub_agent_name},
            )
            if not approved:
                return Message(
                    content="Delegation rejected by human",
                    sender=self.name,
                    role=MessageRole.AGENT,
                )

        self.transition_state(AgentState.DELEGATING, {"sub_agent": sub_agent_name})

        try:
            # Delegate task
            response = await sub_agent.process_message(task)

            # Record delegation
            delegation_record = {
                "timestamp": datetime.now().isoformat(),
                "sub_agent": sub_agent_name,
                "task": task.content,
                "success": response is not None,
            }
            self.delegation_history.append(delegation_record)
            self.performance_metrics["delegations"] += 1

            self.transition_state(AgentState.IDLE)
            return response

        except Exception as e:
            print(f"[!] Delegation error in {self.name}: {e}")
            self.transition_state(AgentState.ERROR, {"error": str(e)})
            return None

    async def broadcast_to_sub_agents(self, message: Message) -> List[Message]:
        """Broadcast a message to all sub-agents.

        Args:
            message: Message to broadcast

        Returns:
            List of responses from sub-agents
        """
        if not self.sub_agents:
            return []

        self.transition_state(AgentState.DELEGATING, {"type": "broadcast"})

        tasks = [agent.process_message(message) for agent in self.sub_agents]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        self.transition_state(AgentState.IDLE)

        # Filter out None and exceptions
        return [r for r in responses if isinstance(r, Message)]

    def get_sub_agent_health(self) -> Dict[str, Dict[str, Any]]:
        """Monitor health of all sub-agents.

        Returns:
            Health status for each sub-agent
        """
        health = {}
        for agent in self.sub_agents:
            health[agent.name] = {
                "is_active": agent.is_active,
                "state": agent.state.value if hasattr(agent, "state") else "unknown",
                "memory_size": len(agent.memory),
                "error_count": agent.performance_metrics.get("error_count", 0)
                if hasattr(agent, "performance_metrics")
                else 0,
            }
        return health

    def aggregate_sub_agent_results(
        self, results: List[Message], strategy: str = "concatenate"
    ) -> str:
        """Aggregate results from multiple sub-agents.

        Args:
            results: List of sub-agent responses
            strategy: Aggregation strategy ('concatenate', 'vote', 'summarize')

        Returns:
            Aggregated result
        """
        if not results:
            return "No results to aggregate"

        if strategy == "concatenate":
            return "\n\n".join(f"[{r.sender}] {r.content}" for r in results)
        elif strategy == "vote":
            # Simple voting: most common response
            from collections import Counter

            contents = [r.content for r in results]
            most_common = Counter(contents).most_common(1)
            return most_common[0][0] if most_common else ""
        elif strategy == "summarize":
            # Create summary
            return f"Aggregated {len(results)} responses from sub-agents"
        else:
            return "\n".join(r.content for r in results)

    # ==================== Learning & Adaptation ====================

    def track_success(self, success: bool, response_time: float = 0.0) -> None:
        """Track success/failure of an operation.

        Args:
            success: Whether the operation succeeded
            response_time: Time taken for the operation
        """
        if not self.enable_learning:
            return

        self.performance_metrics["total_messages"] += 1

        if success:
            self.performance_metrics["successful_responses"] += 1
        else:
            self.performance_metrics["failed_responses"] += 1
            self.performance_metrics["error_count"] += 1

        # Update average response time
        total = self.performance_metrics["total_messages"]
        current_avg = self.performance_metrics["average_response_time"]
        self.performance_metrics["average_response_time"] = (
            current_avg * (total - 1) + response_time
        ) / total

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics.

        Returns:
            Performance metrics dictionary
        """
        metrics = self.performance_metrics.copy()

        # Calculate success rate
        total = metrics["total_messages"]
        if total > 0:
            metrics["success_rate"] = metrics["successful_responses"] / total
        else:
            metrics["success_rate"] = 0.0

        # Calculate tool success rate
        tool_calls = metrics["tool_calls"]
        if tool_calls > 0:
            metrics["tool_success_rate"] = metrics["successful_tool_calls"] / tool_calls
        else:
            metrics["tool_success_rate"] = 0.0

        return metrics

    async def _adapt_from_feedback(self, feedback: Dict[str, Any]) -> None:
        """Adapt behavior based on feedback.

        Args:
            feedback: Feedback data
        """
        # Simple adaptation: adjust temperature based on feedback
        rating = feedback.get("rating", 0)

        if rating < 3 and self.config.temperature > 0.3:
            # Lower temperature for more deterministic responses
            self.config.temperature = max(0.3, self.config.temperature - 0.1)
            print(f"[Adaptation] {self.name} lowered temperature to {self.config.temperature}")
        elif rating > 4 and self.config.temperature < 0.9:
            # Increase temperature for more creative responses
            self.config.temperature = min(0.9, self.config.temperature + 0.1)
            print(f"[Adaptation] {self.name} increased temperature to {self.config.temperature}")

    def suggest_improvements(self) -> List[str]:
        """Generate self-improvement suggestions based on performance.

        Returns:
            List of improvement suggestions
        """
        suggestions = []
        metrics = self.get_performance_metrics()

        if metrics["success_rate"] < 0.7:
            suggestions.append("Consider adjusting temperature or system prompt")

        if metrics["tool_success_rate"] < 0.8 and metrics["tool_calls"] > 5:
            suggestions.append("Review tool usage patterns and error handling")

        if metrics["error_count"] > 10:
            suggestions.append("Implement better error recovery mechanisms")

        if metrics["human_interventions"] > metrics["total_messages"] * 0.3:
            suggestions.append("Reduce dependency on human intervention")

        if len(self.memory) > self.config.memory_limit * 0.9:
            suggestions.append("Consider implementing memory summarization")

        return suggestions

    def start_ab_test(
        self, test_name: str, variant_a: Dict[str, Any], variant_b: Dict[str, Any]
    ) -> None:
        """Start an A/B test for behavior optimization.

        Args:
            test_name: Name of the test
            variant_a: Configuration for variant A
            variant_b: Configuration for variant B
        """
        self.ab_tests[test_name] = {
            "variant_a": variant_a,
            "variant_b": variant_b,
            "results_a": [],
            "results_b": [],
            "current_variant": "a",
            "started_at": datetime.now().isoformat(),
        }
        print(f"[A/B Test] Started test '{test_name}' in {self.name}")

    def record_ab_result(self, test_name: str, success: bool) -> None:
        """Record result for current A/B test variant.

        Args:
            test_name: Name of the test
            success: Whether the operation succeeded
        """
        if test_name not in self.ab_tests:
            return

        test = self.ab_tests[test_name]
        variant = test["current_variant"]

        if variant == "a":
            test["results_a"].append(success)
            test["current_variant"] = "b"
        else:
            test["results_b"].append(success)
            test["current_variant"] = "a"

    def get_ab_test_results(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Get results of an A/B test.

        Args:
            test_name: Name of the test

        Returns:
            Test results or None
        """
        if test_name not in self.ab_tests:
            return None

        test = self.ab_tests[test_name]
        results_a = test["results_a"]
        results_b = test["results_b"]

        return {
            "test_name": test_name,
            "variant_a_success_rate": sum(results_a) / len(results_a) if results_a else 0,
            "variant_b_success_rate": sum(results_b) / len(results_b) if results_b else 0,
            "variant_a_count": len(results_a),
            "variant_b_count": len(results_b),
            "started_at": test["started_at"],
        }

    # ==================== State Persistence ====================

    def save_state(self, filepath: str) -> bool:
        """Save agent state to disk.

        Args:
            filepath: Path to save state file

        Returns:
            True if saved successfully
        """
        try:
            state_data = {
                "name": self.name,
                "role": self.role,
                "config": self.config.model_dump(),
                "state": self.state.value,
                "memory": [msg.model_dump(mode="json") for msg in self.memory],
                "performance_metrics": self.performance_metrics,
                "state_history": self.state_history[-50:],
                "delegation_history": self.delegation_history[-20:],
                "feedback_history": self.feedback_history[-20:],
                "sub_agents": [agent.name for agent in self.sub_agents],
                "timestamp": datetime.now().isoformat(),
            }

            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, default=str)

            print(f"[*] Agent {self.name} state saved to {filepath}")
            return True

        except Exception as e:
            print(f"[!] Failed to save state for {self.name}: {e}")
            return False

    def load_state(self, filepath: str) -> bool:
        """Load agent state from disk.

        Args:
            filepath: Path to state file

        Returns:
            True if loaded successfully
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state_data = json.load(f)

            # Restore state
            self.state = AgentState(state_data["state"])
            self.memory = [Message(**msg_data) for msg_data in state_data["memory"]]
            self.performance_metrics = state_data["performance_metrics"]
            self.state_history = state_data["state_history"]
            self.delegation_history = state_data["delegation_history"]
            self.feedback_history = state_data["feedback_history"]

            print(f"[*] Agent {self.name} state loaded from {filepath}")
            return True

        except Exception as e:
            print(f"[!] Failed to load state for {self.name}: {e}")
            return False

    async def recover_from_error(self) -> bool:
        """Attempt to recover from error state.

        Returns:
            True if recovery successful
        """
        if self.state != AgentState.ERROR:
            return True

        self.transition_state(AgentState.RECOVERING)

        try:
            # Clear error state
            self.performance_metrics["error_count"] = max(
                0, self.performance_metrics["error_count"] - 1
            )

            # Return to idle
            self.transition_state(AgentState.IDLE)
            print(f"[*] Agent {self.name} recovered from error")
            return True

        except Exception as e:
            print(f"[!] Recovery failed for {self.name}: {e}")
            self.transition_state(AgentState.ERROR)
            return False

    # ==================== Original Methods (Enhanced) ====================

    async def process_message(self, message: Message) -> Optional[Message]:
        """Process an incoming message and generate a response.

        This method processes a message according to the agent's role and generates
        an appropriate response. The message and response are both stored in the
        agent's memory. Enhanced with state tracking and performance metrics.

        Args:
            message: The incoming message to process

        Returns:
            A response message, or None if the agent is inactive

        Example:
            >>> agent = Agent(name="analyst", role="analyst")
            >>> msg = Message(content="What do you think?", sender="user")
            >>> response = await agent.process_message(msg)
        """
        if not self.is_active:
            return None

        start_time = datetime.now()
        self.transition_state(AgentState.THINKING)

        try:
            # Check if approval needed
            if self.should_request_approval("message"):
                approved = await self.request_human_approval(
                    "Process message", {"content": message.content[:100]}
                )
                if not approved:
                    self.transition_state(AgentState.IDLE)
                    return Message(
                        content="Message processing rejected by human",
                        sender=self.name,
                        role=MessageRole.AGENT,
                    )

            # Generate response based on role
            response_content = self._generate_response(message)

            response = Message(
                content=response_content,
                sender=self.name,
                role=MessageRole.AGENT,
                metadata={"agent_role": self.role, "state": self.state.value},
            )

            # Store in memory
            self.memory.append(message)
            self.memory.append(response)

            # Trim memory if needed
            if len(self.memory) > self.config.memory_limit:
                self.memory = self.memory[-self.config.memory_limit :]

            # Track performance
            response_time = (datetime.now() - start_time).total_seconds()
            self.track_success(True, response_time)

            self.transition_state(AgentState.IDLE)
            return response

        except Exception as e:
            print(f"[!] Error in {self.name}.process_message: {e}")
            self.transition_state(AgentState.ERROR, {"error": str(e)})
            self.track_success(False)

            # Attempt recovery
            await self.recover_from_error()
            return None

    def _generate_response(self, message: Message) -> str:
        """Generate a response based on the agent's role.

        This is a placeholder implementation that will be replaced with actual
        LLM integration in Phase 1.

        Args:
            message: The message to respond to

        Returns:
            Generated response text
        """
        # Role-based response templates (will be replaced with LLM in Phase 1)
        role_templates = {
            AgentRole.ANALYST: f"[Analysis] {self.name}: From a data perspective, '{message.content}' requires further analysis",
            AgentRole.CREATIVE: f"[Creative] {self.name}: This gives me an interesting idea about '{message.content}'",
            AgentRole.COORDINATOR: f"[Coordination] {self.name}: Let's integrate the perspectives on '{message.content}'",
            AgentRole.CRITIC: f"[Critique] {self.name}: I see potential issues with '{message.content}'",
            AgentRole.RESEARCHER: f"[Research] {self.name}: I need to investigate '{message.content}' further",
            AgentRole.EXECUTOR: f"[Execution] {self.name}: I will take action on '{message.content}'",
            AgentRole.SUMMARIZER: f"[Summary] {self.name}: To summarize '{message.content}'...",
            AgentRole.DEBATER: f"[Debate] {self.name}: Let me present a counterpoint to '{message.content}'",
            AgentRole.SUPERVISOR: f"[Supervision] {self.name}: Overseeing the discussion on '{message.content}'",
        }

        # Try to match role to enum, otherwise use generic response
        try:
            role_enum = AgentRole(self.role)
            return role_templates.get(
                role_enum, f"[{self.role}] {self.name}: Received message '{message.content}'"
            )
        except ValueError:
            return f"[{self.role}] {self.name}: Received message '{message.content}'"

    def _bind_tools(self) -> List[str]:
        """Bind tools from config to this agent.

        Returns:
            List of available tool names
        """
        # Optimized: use list comprehension for better performance
        return [
            tool_name
            for tool_name in self.config.tools
            if self.tool_registry.get(tool_name) is not None
        ]

    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with approval and tracking.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            Dict with tool result
        """
        if tool_name not in self._available_tools:
            return {"success": False, "error": f"Tool '{tool_name}' not available to this agent"}

        # Check if approval needed
        if self.should_request_approval("tool_use"):
            approved = await self.request_human_approval(
                f"Execute tool: {tool_name}", {"tool": tool_name, "params": kwargs}
            )
            if not approved:
                return {"success": False, "error": "Tool execution rejected by human"}

        self.transition_state(AgentState.EXECUTING, {"tool": tool_name})
        self.performance_metrics["tool_calls"] += 1

        try:
            result = await self.tool_registry.execute(tool_name, **kwargs)
            result_dict = result.model_dump()

            if result_dict.get("success", False):
                self.performance_metrics["successful_tool_calls"] += 1

            self.transition_state(AgentState.IDLE)
            return result_dict

        except Exception as e:
            print(f"[!] Tool execution error in {self.name}: {e}")
            self.transition_state(AgentState.ERROR, {"error": str(e)})
            return {"success": False, "error": str(e)}

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get definitions for all tools available to this agent.

        Returns:
            List of tool definition dicts
        """
        definitions = []
        for tool_name in self._available_tools:
            tool = self.tool_registry.get(tool_name)
            if tool:
                tool_def = tool.get_definition()
                definitions.append(tool_def.model_dump())
        return definitions

    def get_system_prompt(self) -> str:
        """Build the system prompt for this agent.

        Returns:
            Complete system prompt including role, backstory, and memory context
        """
        # Get recent memory for context
        recent_messages = self.get_recent_memory(limit=5)
        memory_context = None
        if recent_messages:
            # Optimized: use list comprehension and join in one step
            memory_context = "\n".join(f"{msg.sender}: {msg.content}" for msg in recent_messages)

        return get_system_prompt(
            role=self.role,
            backstory=self.config.backstory,
            custom_prompt=self.config.system_prompt,
            memory_context=memory_context,
            tools=self.config.tools if self.config.tools else None,
        )

    async def think_and_respond(self, incoming_message: Message, mode: str = "simple") -> Message:
        """Think about a message and generate an intelligent response using LLM.

        This implements a ReAct-style reasoning pattern:
        1. Thought: Analyze the message and decide on approach
        2. Action: Generate response or use tools
        3. Observation: Reflect on the result

        Args:
            incoming_message: The message to respond to
            mode: Response mode - "simple" (direct reply) or "tool_use" (function calling)

        Returns:
            Response message with generated content

        Raises:
            ValueError: If LLM provider is not configured
        """
        if not self.llm_provider:
            # Fall back to template-based response
            return await self.process_message(incoming_message)

        # Build conversation messages for LLM
        system_prompt = self.get_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": incoming_message.content},
        ]

        # Add tool definitions if in tool_use mode
        if mode == "tool_use" and self._available_tools:
            _ = self.get_tool_definitions()  # Tool definitions prepared for future use

        try:
            # Generate response using LLM
            llm_response = await self.llm_provider.generate(
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            response_content = llm_response.content
            metadata = {
                "agent_role": self.role,
                "model": llm_response.model,
                "usage": llm_response.usage,
                "mode": mode,
            }

            # Check if LLM wants to use tools (simple pattern matching for now)
            if mode == "tool_use" and self._available_tools:
                tool_results = await self._process_tool_calls(response_content)
                if tool_results:
                    metadata["tool_calls"] = tool_results
                    # Append tool results to response
                    response_content += f"\n\n[Tool Results: {json.dumps(tool_results, indent=2)}]"

            # Create response message
            response = Message(
                content=response_content,
                sender=self.name,
                role=MessageRole.AGENT,
                metadata=metadata,
            )

            # Store in memory
            self.memory.append(incoming_message)
            self.memory.append(response)

            # Trim memory if needed
            if len(self.memory) > self.config.memory_limit:
                self.memory = self.memory[-self.config.memory_limit :]

            return response

        except Exception as e:
            # On error, fall back to template response
            print(f"[!] LLM error for {self.name}: {str(e)}, falling back to template")
            return await self.process_message(incoming_message)

    async def _process_tool_calls(self, llm_output: str) -> List[Dict[str, Any]]:
        """Process tool calls from LLM output.

        This is a simple implementation that looks for tool call patterns.
        A more sophisticated version would use structured output from the LLM.

        Args:
            llm_output: The LLM's response text

        Returns:
            List of tool execution results
        """
        results = []

        # Simple pattern: look for tool calls in format: TOOL[tool_name](param=value)
        # This is a placeholder - real implementation would use LLM function calling
        import re

        pattern = r"TOOL\[(\w+)\]\((.*?)\)"
        matches = re.findall(pattern, llm_output)

        for tool_name, params_str in matches:
            try:
                # Parse parameters (simple key=value format)
                params = {}
                if params_str:
                    for param in params_str.split(","):
                        if "=" in param:
                            key, value = param.split("=", 1)
                            params[key.strip()] = value.strip().strip("\"'")

                # Execute tool
                result = await self.execute_tool(tool_name, **params)
                results.append({"tool": tool_name, "params": params, "result": result})
            except Exception as e:
                results.append({"tool": tool_name, "error": str(e)})

        return results

    def get_recent_memory(self, limit: int = 5) -> List[Message]:
        """Retrieve the most recent messages from memory.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent messages, newest last

        Example:
            >>> agent = Agent(name="test")
            >>> recent = agent.get_recent_memory(limit=10)
            >>> for msg in recent:
            ...     print(f"{msg.sender}: {msg.content}")
        """
        # Optimized: avoid creating new list if memory is empty
        if not self.memory:
            return []
        # Use negative indexing for efficient slicing
        return self.memory[-limit:] if len(self.memory) > limit else self.memory

    def clear_memory(self) -> None:
        """Clear all messages from the agent's memory.

        This is useful for starting fresh or managing memory usage.
        """
        self.memory.clear()

    def get_memory_summary(self) -> str:
        """Get a text summary of the agent's memory.

        Returns:
            A formatted string summarizing the agent's memory

        Example:
            >>> agent = Agent(name="test")
            >>> print(agent.get_memory_summary())
            Agent 'test' memory: 0 messages
        """
        return f"Agent '{self.name}' memory: {len(self.memory)} messages"

    def deactivate(self) -> None:
        """Deactivate this agent, preventing it from processing messages."""
        self.is_active = False

    def activate(self) -> None:
        """Activate this agent, allowing it to process messages."""
        self.is_active = True

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        status = "active" if self.is_active else "inactive"
        return (
            f"Agent(name='{self.name}', role='{self.role}', status={status}, "
            f"state={self.state.value}, memory={len(self.memory)}, "
            f"sub_agents={len(self.sub_agents)})"
        )

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.name} ({self.role})"
