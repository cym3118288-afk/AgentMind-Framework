"""Core agent implementation for AgentMind framework.

This module provides the Agent class which represents an individual agent
in the multi-agent system with memory, role-based behavior, and message processing.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from ..llm.provider import LLMProvider
from ..prompts import get_system_prompt
from ..tools import ToolRegistry, get_global_registry
from .types import AgentConfig, AgentRole, Message, MessageRole


class Agent:
    """An intelligent agent that can process messages and collaborate with other agents.

    The Agent class represents a single agent in the multi-agent system. Each agent
    has a unique name, role, memory, and can process incoming messages to generate
    responses based on its role and configuration.

    Attributes:
        name: Unique identifier for this agent
        role: The agent's role (analyst, creative, coordinator, etc.)
        config: Full configuration for the agent
        memory: List of messages this agent has seen/sent
        is_active: Whether the agent is currently active

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
    ) -> None:
        """Initialize a new agent.

        Args:
            name: Unique name for the agent
            role: Role of the agent (analyst, creative, coordinator, etc.)
            config: Optional full configuration. If not provided, creates default config.
            llm_provider: Optional LLM provider for intelligent responses
            tool_registry: Optional tool registry (defaults to global registry)

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

    async def process_message(self, message: Message) -> Optional[Message]:
        """Process an incoming message and generate a response.

        This method processes a message according to the agent's role and generates
        an appropriate response. The message and response are both stored in the
        agent's memory.

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

        # Generate response based on role
        response_content = self._generate_response(message)

        response = Message(
            content=response_content,
            sender=self.name,
            role=MessageRole.AGENT,
            metadata={"agent_role": self.role},
        )

        # Store in memory
        self.memory.append(message)
        self.memory.append(response)

        # Trim memory if needed
        if len(self.memory) > self.config.memory_limit:
            self.memory = self.memory[-self.config.memory_limit :]

        return response

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
        available = []
        for tool_name in self.config.tools:
            tool = self.tool_registry.get(tool_name)
            if tool:
                available.append(tool_name)
        return available

    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            Dict with tool result
        """
        if tool_name not in self._available_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not available to this agent"
            }

        result = await self.tool_registry.execute(tool_name, **kwargs)
        return result.model_dump()

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
            memory_lines = []
            for msg in recent_messages:
                memory_lines.append(f"{msg.sender}: {msg.content}")
            memory_context = "\n".join(memory_lines)

        return get_system_prompt(
            role=self.role,
            backstory=self.config.backstory,
            custom_prompt=self.config.system_prompt,
            memory_context=memory_context,
            tools=self.config.tools if self.config.tools else None
        )

    async def think_and_respond(
        self,
        incoming_message: Message,
        mode: str = "simple"
    ) -> Message:
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
            {"role": "user", "content": incoming_message.content}
        ]

        # Add tool definitions if in tool_use mode
        tool_definitions = None
        if mode == "tool_use" and self._available_tools:
            tool_definitions = self.get_tool_definitions()

        try:
            # Generate response using LLM
            llm_response = await self.llm_provider.generate(
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            response_content = llm_response.content
            metadata = {
                "agent_role": self.role,
                "model": llm_response.model,
                "usage": llm_response.usage,
                "mode": mode
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
                metadata=metadata
            )

            # Store in memory
            self.memory.append(incoming_message)
            self.memory.append(response)

            # Trim memory if needed
            if len(self.memory) > self.config.memory_limit:
                self.memory = self.memory[-self.config.memory_limit:]

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
        pattern = r'TOOL\[(\w+)\]\((.*?)\)'
        matches = re.findall(pattern, llm_output)

        for tool_name, params_str in matches:
            try:
                # Parse parameters (simple key=value format)
                params = {}
                if params_str:
                    for param in params_str.split(','):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key.strip()] = value.strip().strip('"\'')

                # Execute tool
                result = await self.execute_tool(tool_name, **params)
                results.append({
                    "tool": tool_name,
                    "params": params,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "tool": tool_name,
                    "error": str(e)
                })

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
        return self.memory[-limit:] if self.memory else []

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
        return f"Agent(name='{self.name}', role='{self.role}', status={status}, memory={len(self.memory)})"

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.name} ({self.role})"
