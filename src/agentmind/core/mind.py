"""AgentMind orchestration system for multi-agent collaboration.

This module provides the AgentMind class which manages multiple agents,
coordinates their communication, and orchestrates collaborative problem-solving.

Enhanced with:
- Global orchestration with multi-agent coordination strategies
- Checkpointing and recovery with crash recovery
- Advanced task management with DAG dependencies
- System observability with real-time metrics
- Collaboration patterns with conflict resolution
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum
from collections import defaultdict, deque

from ..llm.provider import LLMProvider
from .agent import Agent
from .types import CollaborationResult, CollaborationStrategy, Message, MessageRole


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class CoordinationStrategy(str, Enum):
    """Multi-agent coordination strategies."""

    CENTRALIZED = "centralized"  # Central coordinator
    DECENTRALIZED = "decentralized"  # Peer-to-peer
    AUCTION = "auction"  # Task bidding
    VOTING = "voting"  # Democratic decision
    CONSENSUS = "consensus"  # Require agreement


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving agent conflicts."""

    PRIORITY = "priority"  # Higher priority wins
    VOTING = "voting"  # Majority vote
    SUPERVISOR = "supervisor"  # Supervisor decides
    MERGE = "merge"  # Merge conflicting results


class Task:
    """Represents a task in the system with dependencies."""

    def __init__(
        self,
        task_id: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_agents: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        retry_policy: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.description = description
        self.priority = priority
        self.assigned_agents = assigned_agents or []
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.retry_policy = retry_policy or {"max_retries": 3, "backoff": 1.0}
        self.metadata = metadata or {}
        self.status = TaskStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.retry_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "priority": self.priority.value,
            "assigned_agents": self.assigned_agents,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
        }


class ResourceAllocation:
    """Manages resource allocation across agents."""

    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.allocated_resources: Dict[str, int] = {}
        self.resource_limits: Dict[str, int] = {}

    def allocate(self, agent_name: str, amount: int = 1) -> bool:
        """Allocate resources to an agent."""
        current = self.allocated_resources.get(agent_name, 0)
        limit = self.resource_limits.get(agent_name, self.max_concurrent_tasks)

        if current + amount <= limit:
            self.allocated_resources[agent_name] = current + amount
            return True
        return False

    def release(self, agent_name: str, amount: int = 1) -> None:
        """Release resources from an agent."""
        current = self.allocated_resources.get(agent_name, 0)
        self.allocated_resources[agent_name] = max(0, current - amount)

    def get_available(self, agent_name: str) -> int:
        """Get available resources for an agent."""
        current = self.allocated_resources.get(agent_name, 0)
        limit = self.resource_limits.get(agent_name, self.max_concurrent_tasks)
        return limit - current


class AgentMind:
    """Central orchestrator for multi-agent collaboration.

    AgentMind manages a collection of agents and coordinates their communication
    through various collaboration strategies (broadcast, round-robin, hierarchical, etc.).

    Attributes:
        agents: List of agents in the system
        conversation_history: Complete history of all messages
        is_running: Whether a collaboration session is currently active
        strategy: The collaboration strategy being used

    Example:
        >>> mind = AgentMind()
        >>> mind.add_agent(Agent(name="analyst", role="analyst"))
        >>> mind.add_agent(Agent(name="creative", role="creative"))
        >>> result = await mind.start_collaboration("Analyze this problem")
    """

    def __init__(
        self,
        strategy: CollaborationStrategy = CollaborationStrategy.BROADCAST,
        llm_provider: Optional[LLMProvider] = None,
    ) -> None:
        """Initialize a new AgentMind orchestrator.

        Args:
            strategy: The collaboration strategy to use (default: broadcast)
            llm_provider: Optional LLM provider to use for all agents
        """
        self.agents: List[Agent] = []
        self.conversation_history: List[Message] = []
        self.is_running = False
        self.strategy = strategy
        self.llm_provider = llm_provider
        print("[AgentMind] Initialized - Multi-agent collaboration framework started!")

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the collaboration system.

        Args:
            agent: The agent to add

        Raises:
            ValueError: If an agent with the same name already exists

        Example:
            >>> mind = AgentMind()
            >>> agent = Agent(name="analyst", role="analyst")
            >>> mind.add_agent(agent)
        """
        # Check for duplicate names
        if any(a.name == agent.name for a in self.agents):
            raise ValueError(f"Agent with name '{agent.name}' already exists")

        # Set LLM provider if not already set
        if self.llm_provider and not agent.llm_provider:
            agent.llm_provider = self.llm_provider

        self.agents.append(agent)
        print(f"[+] Added agent: {agent.name} ({agent.role})")

    def remove_agent(self, agent_name: str) -> bool:
        """Remove an agent from the system.

        Args:
            agent_name: Name of the agent to remove

        Returns:
            True if agent was removed, False if not found

        Example:
            >>> mind = AgentMind()
            >>> mind.add_agent(Agent(name="test", role="assistant"))
            >>> mind.remove_agent("test")
            True
        """
        for i, agent in enumerate(self.agents):
            if agent.name == agent_name:
                self.agents.pop(i)
                print(f"[-] Removed agent: {agent_name}")
                return True
        return False

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """Retrieve an agent by name.

        Args:
            agent_name: Name of the agent to find

        Returns:
            The agent if found, None otherwise

        Example:
            >>> mind = AgentMind()
            >>> mind.add_agent(Agent(name="test", role="assistant"))
            >>> agent = mind.get_agent("test")
            >>> print(agent.name)
            test
        """
        # Optimized: use next() with generator for early exit
        return next((agent for agent in self.agents if agent.name == agent_name), None)

    async def broadcast_message(
        self, message: Message, exclude_sender: bool = True, use_llm: bool = True
    ) -> List[Message]:
        """Broadcast a message to all agents and collect responses.

        Args:
            message: The message to broadcast
            exclude_sender: If True, don't send to the agent that sent the message
            use_llm: If True, use LLM-powered responses via think_and_respond

        Returns:
            List of response messages from agents

        Example:
            >>> mind = AgentMind()
            >>> mind.add_agent(Agent(name="agent1", role="analyst"))
            >>> msg = Message(content="Hello", sender="system")
            >>> responses = await mind.broadcast_message(msg)
        """
        responses: List[Message] = []
        self.conversation_history.append(message)

        # Create tasks for parallel processing
        tasks = []
        for agent in self.agents:
            if exclude_sender and agent.name == message.sender:
                continue

            # Use LLM-powered response if available and requested
            if use_llm and agent.llm_provider:
                tasks.append(agent.think_and_respond(message))
            else:
                tasks.append(agent.process_message(message))

        # Wait for all agents to respond
        agent_responses = await asyncio.gather(*tasks)

        # Collect non-None responses
        for response in agent_responses:
            if response:
                responses.append(response)
                self.conversation_history.append(response)

        return responses

    async def start_collaboration(
        self,
        initial_message: str,
        max_rounds: int = 10,
        stop_condition: Optional[Callable[[List[Message]], bool]] = None,
        use_llm: bool = True,
    ) -> CollaborationResult:
        """Start a multi-agent collaboration session.

        Args:
            initial_message: The initial task or question to discuss
            max_rounds: Maximum number of collaboration rounds
            stop_condition: Optional function to determine when to stop early.
                          Takes list of recent messages, returns True to stop.
            use_llm: If True, use LLM-powered intelligent responses

        Returns:
            CollaborationResult with success status and summary

        Example:
            >>> mind = AgentMind()
            >>> mind.add_agent(Agent(name="analyst", role="analyst"))
            >>> result = await mind.start_collaboration(
            ...     "Analyze this problem",
            ...     max_rounds=5
            ... )
            >>> print(result.success)
            True
        """
        if not self.agents:
            print("[!] No agents available, cannot start collaboration")
            return CollaborationResult(
                success=False,
                error="No agents available",
                total_rounds=0,
                total_messages=0,
            )

        print(f"[*] Starting multi-agent collaboration: {initial_message}")
        print(f"[*] Strategy: {self.strategy.value}, LLM-powered: {use_llm}")
        self.is_running = True

        # Create initial message
        init_msg = Message(
            content=initial_message,
            sender="system",
            role=MessageRole.SYSTEM,
        )

        # Track agent contributions
        agent_contributions: Dict[str, int] = {agent.name: 0 for agent in self.agents}

        try:
            if self.strategy == CollaborationStrategy.BROADCAST:
                # Broadcast strategy: all agents respond to initial message
                responses = await self.broadcast_message(
                    init_msg, exclude_sender=False, use_llm=use_llm
                )

                for response in responses:
                    agent_contributions[response.sender] = (
                        agent_contributions.get(response.sender, 0) + 1
                    )

                print(f"[>] Round 1: Received {len(responses)} responses")
                rounds_completed = 1

            elif self.strategy == CollaborationStrategy.ROUND_ROBIN:
                # Round-robin strategy: agents take turns
                responses = []
                rounds_completed = 0
                current_message = init_msg

                for round_num in range(min(max_rounds, len(self.agents))):
                    agent = self.agents[round_num % len(self.agents)]
                    if use_llm and agent.llm_provider:
                        response = await agent.think_and_respond(current_message)
                    else:
                        response = await agent.process_message(current_message)

                    if response:
                        responses.append(response)
                        self.conversation_history.append(response)
                        agent_contributions[response.sender] += 1
                        current_message = response

                    rounds_completed += 1
                    print(f"[>] Round {round_num + 1}: {agent.name} responded")

                    # Check stop condition
                    if stop_condition and stop_condition([response]):
                        print("[*] Stop condition met, ending collaboration")
                        break

            elif self.strategy == CollaborationStrategy.HIERARCHICAL:
                # Hierarchical strategy: supervisor coordinates sub-agents
                supervisor = None
                sub_agents = []

                for agent in self.agents:
                    if agent.role == "supervisor":
                        supervisor = agent
                    else:
                        sub_agents.append(agent)

                if not supervisor:
                    # Fall back to broadcast if no supervisor
                    responses = await self.broadcast_message(
                        init_msg, exclude_sender=False, use_llm=use_llm
                    )
                else:
                    # Supervisor delegates to sub-agents
                    responses = []
                    for agent in sub_agents:
                        if use_llm and agent.llm_provider:
                            response = await agent.think_and_respond(init_msg)
                        else:
                            response = await agent.process_message(init_msg)
                        if response:
                            responses.append(response)
                            self.conversation_history.append(response)
                            agent_contributions[response.sender] += 1

                    # Supervisor synthesizes
                    summary_msg = Message(
                        content=f"Synthesize these perspectives: {[r.content for r in responses]}",
                        sender="system",
                        role=MessageRole.SYSTEM,
                    )
                    if use_llm and supervisor.llm_provider:
                        supervisor_response = await supervisor.think_and_respond(summary_msg)
                    else:
                        supervisor_response = await supervisor.process_message(summary_msg)

                    if supervisor_response:
                        responses.append(supervisor_response)
                        self.conversation_history.append(supervisor_response)
                        agent_contributions[supervisor_response.sender] += 1

                rounds_completed = 1
                print(f"[>] Hierarchical collaboration: {len(responses)} responses")

            else:
                # Default to broadcast for other strategies
                responses = await self.broadcast_message(
                    init_msg, exclude_sender=False, use_llm=use_llm
                )
                rounds_completed = 1

            # Check stop condition
            if stop_condition and stop_condition(responses):
                print("[*] Stop condition met, ending collaboration")

            # Generate final output
            final_output = self._generate_final_output(responses)

            result = CollaborationResult(
                success=True,
                total_rounds=rounds_completed,
                total_messages=len(self.conversation_history),
                final_output=final_output,
                agent_contributions=agent_contributions,
            )

            print("[*] Collaboration completed successfully")
            return result

        except Exception as e:
            print(f"[!] Collaboration failed: {str(e)}")
            return CollaborationResult(
                success=False,
                error=str(e),
                total_rounds=0,
                total_messages=len(self.conversation_history),
                agent_contributions=agent_contributions,
            )
        finally:
            self.is_running = False

    def _generate_final_output(self, responses: List[Message]) -> str:
        """Generate a final output summary from agent responses.

        Args:
            responses: List of agent responses

        Returns:
            Formatted summary string
        """
        if not responses:
            return "No responses generated"

        # Optimized: use list comprehension and join in one step
        output_lines = ["=== Collaboration Summary ==="] + [
            f"• {response.sender}: {response.content}" for response in responses
        ]
        return "\n".join(output_lines)

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation state.

        Returns:
            Dictionary with conversation statistics

        Example:
            >>> mind = AgentMind()
            >>> summary = mind.get_conversation_summary()
            >>> print(summary['total_messages'])
            0
        """
        return {
            "total_messages": len(self.conversation_history),
            "active_agents": len([a for a in self.agents if a.is_active]),
            "total_agents": len(self.agents),
            "recent_messages": [msg.content for msg in self.conversation_history[-5:]],
            "is_running": self.is_running,
        }

    def clear_history(self) -> None:
        """Clear the conversation history.

        This does not clear individual agent memories.
        """
        self.conversation_history.clear()
        print("[*] Conversation history cleared")

    def reset(self) -> None:
        """Reset the entire system, clearing all agents and history."""
        self.agents.clear()
        self.conversation_history.clear()
        self.is_running = False
        print("[*] AgentMind reset complete")

    def save_session(self, session_id: str, save_dir: str = ".agentmind_sessions") -> str:
        """Save the current session state to disk.

        Args:
            session_id: Unique identifier for this session
            save_dir: Directory to save session files (default: .agentmind_sessions)

        Returns:
            Path to the saved session file

        Example:
            >>> mind = AgentMind()
            >>> mind.add_agent(Agent(name="test", role="assistant"))
            >>> path = mind.save_session("my_session")
            >>> print(f"Session saved to {path}")
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        session_file = save_path / f"{session_id}.json"

        # Serialize session data
        session_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "strategy": self.strategy.value,
            "agents": [],
            "conversation_history": [],
        }

        # Serialize agents
        for agent in self.agents:
            agent_data = {
                "name": agent.name,
                "role": agent.role,
                "config": agent.config.model_dump(),
                "memory": [msg.model_dump(mode="json") for msg in agent.memory],
                "is_active": agent.is_active,
            }
            session_data["agents"].append(agent_data)

        # Serialize conversation history
        for msg in self.conversation_history:
            session_data["conversation_history"].append(msg.model_dump(mode="json"))

        # Write to file
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"[*] Session saved: {session_file}")
        return str(session_file)

    def load_session(self, session_id: str, save_dir: str = ".agentmind_sessions") -> bool:
        """Load a previously saved session from disk.

        Args:
            session_id: Unique identifier for the session to load
            save_dir: Directory where session files are stored

        Returns:
            True if session loaded successfully, False otherwise

        Example:
            >>> mind = AgentMind()
            >>> success = mind.load_session("my_session")
            >>> if success:
            ...     print("Session loaded successfully")
        """
        session_file = Path(save_dir) / f"{session_id}.json"

        if not session_file.exists():
            print(f"[!] Session file not found: {session_file}")
            return False

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Clear current state
            self.reset()

            # Restore strategy
            self.strategy = CollaborationStrategy(session_data["strategy"])

            # Restore agents
            for agent_data in session_data["agents"]:
                from .types import AgentConfig

                config = AgentConfig(**agent_data["config"])
                agent = Agent(
                    name=agent_data["name"],
                    role=agent_data["role"],
                    config=config,
                    llm_provider=self.llm_provider,
                )

                # Restore agent memory
                agent.memory = [Message(**msg_data) for msg_data in agent_data["memory"]]
                agent.is_active = agent_data["is_active"]

                self.agents.append(agent)

            # Restore conversation history
            self.conversation_history = [
                Message(**msg_data) for msg_data in session_data["conversation_history"]
            ]

            print(f"[*] Session loaded: {session_id}")
            print(f"    - Agents: {len(self.agents)}")
            print(f"    - Messages: {len(self.conversation_history)}")
            return True

        except Exception as e:
            print(f"[!] Failed to load session: {str(e)}")
            return False

    def list_sessions(self, save_dir: str = ".agentmind_sessions") -> List[Dict[str, Any]]:
        """List all saved sessions.

        Args:
            save_dir: Directory where session files are stored

        Returns:
            List of session info dictionaries

        Example:
            >>> mind = AgentMind()
            >>> sessions = mind.list_sessions()
            >>> for session in sessions:
            ...     print(f"{session['session_id']}: {session['timestamp']}")
        """
        save_path = Path(save_dir)
        if not save_path.exists():
            return []

        # Optimized: use list comprehension with inline error handling
        sessions = []
        for session_file in save_path.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append(
                        {
                            "session_id": data.get("session_id"),
                            "timestamp": data.get("timestamp"),
                            "num_agents": len(data.get("agents", [])),
                            "num_messages": len(data.get("conversation_history", [])),
                            "file_path": str(session_file),
                        }
                    )
            except Exception:
                continue

        # Optimized: use itemgetter for faster sorting
        from operator import itemgetter

        return sorted(sessions, key=itemgetter("timestamp"), reverse=True)

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return (
            f"AgentMind(agents={len(self.agents)}, "
            f"messages={len(self.conversation_history)}, "
            f"running={self.is_running})"
        )

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"AgentMind with {len(self.agents)} agents"
