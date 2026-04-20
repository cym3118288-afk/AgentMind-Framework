"""
OpenAI Assistants API Compatibility Layer

This module provides a compatibility layer that allows AgentMind agents to work
with the OpenAI Assistants API interface, making it easy to migrate existing
code or use AgentMind as a drop - in replacement.

Key features:
- Compatible with OpenAI Assistants API structure
- Supports threads, messages, and runs
- Works with any LLM provider (not just OpenAI)
- Maintains AgentMind's lightweight philosophy
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider, LiteLLMProvider
from agentmind.tools import Tool


class RunStatus(str, Enum):
    """Status of an assistant run"""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REQUIRES_ACTION = "requires_action"


@dataclass
class Message:
    """Represents a message in a thread"""

    id: str
    role: str
    content: str
    created_at: int = field(default_factory=lambda: int(time.time()))
    thread_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Thread:
    """Represents a conversation thread"""

    id: str
    created_at: int = field(default_factory=lambda: int(time.time()))
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Run:
    """Represents an assistant run"""

    id: str
    thread_id: str
    assistant_id: str
    status: RunStatus
    created_at: int = field(default_factory=lambda: int(time.time()))
    completed_at: Optional[int] = None
    failed_at: Optional[int] = None
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Assistant:
    """
    OpenAI Assistants API compatible wrapper for AgentMind.

    Usage:
        assistant = Assistant(
            name="Math Tutor",
            instructions="You are a helpful math tutor.",
            model="llama3.2"
        )

        thread = assistant.threads.create()
        assistant.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="What is 2 + 2?"
        )

        run = assistant.threads.runs.create(thread_id=thread.id)
        result = assistant.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    """

    def __init__(
        self,
        name: str,
        instructions: str,
        model: str = "llama3.2",
        tools: Optional[List[Tool]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        provider: str = "ollama",
    ):
        self.id = f"asst_{int(time.time())}"
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools or []
        self.metadata = metadata or {}
        self.created_at = int(time.time())

        # Initialize LLM provider
        if provider == "ollama":
            self.llm_provider = OllamaProvider(model=model)
        else:
            self.llm_provider = LiteLLMProvider(model=model)

        # Create AgentMind agent
        self.agent = Agent(
            name=name, role="assistant", system_prompt=instructions, tools=self.tools
        )

        # Initialize AgentMind
        self.mind = AgentMind(llm_provider=self.llm_provider)
        self.mind.add_agent(self.agent)

        # Storage
        self._threads: Dict[str, Thread] = {}
        self._runs: Dict[str, Run] = {}

        # Thread management interface
        self.threads = ThreadManager(self)


class ThreadManager:
    """Manages threads for an assistant"""

    def __init__(self, assistant: Assistant):
        self.assistant = assistant
        self.messages = MessageManager(assistant)
        self.runs = RunManager(assistant)

    def create(self, metadata: Optional[Dict[str, Any]] = None) -> Thread:
        """Create a new thread"""
        thread = Thread(
            id=f"thread_{int(time.time())}_{len(self.assistant._threads)}", metadata=metadata or {}
        )
        self.assistant._threads[thread.id] = thread
        return thread

    def retrieve(self, thread_id: str) -> Optional[Thread]:
        """Retrieve a thread by ID"""
        return self.assistant._threads.get(thread_id)

    def delete(self, thread_id: str) -> bool:
        """Delete a thread"""
        if thread_id in self.assistant._threads:
            del self.assistant._threads[thread_id]
            return True
        return False


class MessageManager:
    """Manages messages within threads"""

    def __init__(self, assistant: Assistant):
        self.assistant = assistant

    def create(
        self, thread_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to a thread"""
        thread = self.assistant._threads.get(thread_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")

        message = Message(
            id=f"msg_{int(time.time())}_{len(thread.messages)}",
            role=role,
            content=content,
            thread_id=thread_id,
            metadata=metadata or {},
        )

        thread.messages.append(message)
        return message

    def list(self, thread_id: str) -> List[Message]:
        """List all messages in a thread"""
        thread = self.assistant._threads.get(thread_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")
        return thread.messages

    def retrieve(self, thread_id: str, message_id: str) -> Optional[Message]:
        """Retrieve a specific message"""
        thread = self.assistant._threads.get(thread_id)
        if not thread:
            return None

        for message in thread.messages:
            if message.id == message_id:
                return message
        return None


class RunManager:
    """Manages runs (assistant executions)"""

    def __init__(self, assistant: Assistant):
        self.assistant = assistant

    def create(
        self,
        thread_id: str,
        instructions: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Run:
        """Create and execute a run"""
        thread = self.assistant._threads.get(thread_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")

        run = Run(
            id=f"run_{int(time.time())}",
            thread_id=thread_id,
            assistant_id=self.assistant.id,
            status=RunStatus.QUEUED,
            metadata=metadata or {},
        )

        self.assistant._runs[run.id] = run

        # Execute asynchronously
        asyncio.create_task(self._execute_run(run, thread, instructions))

        return run

    async def _execute_run(self, run: Run, thread: Thread, custom_instructions: Optional[str]):
        """Execute the assistant run"""
        try:
            run.status = RunStatus.IN_PROGRESS

            # Get the last user message
            user_messages = [msg for msg in thread.messages if msg.role == "user"]
            if not user_messages:
                raise ValueError("No user messages in thread")

            last_message = user_messages[-1].content

            # Override instructions if provided
            if custom_instructions:
                original_prompt = self.assistant.agent.system_prompt
                self.assistant.agent.system_prompt = custom_instructions

            # Run collaboration
            result = await self.assistant.mind.collaborate(last_message, max_rounds=3)

            # Restore original instructions
            if custom_instructions:
                self.assistant.agent.system_prompt = original_prompt

            # Add assistant response to thread
            response_message = Message(
                id=f"msg_{int(time.time())}_{len(thread.messages)}",
                role="assistant",
                content=result,
                thread_id=thread.id,
            )
            thread.messages.append(response_message)

            # Mark run as completed
            run.status = RunStatus.COMPLETED
            run.completed_at = int(time.time())

        except Exception as e:
            run.status = RunStatus.FAILED
            run.failed_at = int(time.time())
            run.last_error = str(e)

    def retrieve(self, thread_id: str, run_id: str) -> Optional[Run]:
        """Retrieve a run by ID"""
        return self.assistant._runs.get(run_id)

    def list(self, thread_id: str) -> List[Run]:
        """List all runs for a thread"""
        return [run for run in self.assistant._runs.values() if run.thread_id == thread_id]

    def cancel(self, thread_id: str, run_id: str) -> Optional[Run]:
        """Cancel a run"""
        run = self.assistant._runs.get(run_id)
        if run and run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS]:
            run.status = RunStatus.CANCELLED
        return run


# Example usage
async def example_basic_assistant():
    """Basic assistant example compatible with OpenAI API"""
    print("\n=== Example 1: Basic Assistant ===\n")

    # Create assistant
    assistant = Assistant(
        name="Math Tutor",
        instructions="You are a helpful math tutor. Explain concepts clearly and provide step - by - step solutions.",
        model="llama3.2",
    )

    # Create thread
    thread = assistant.threads.create()
    print(f"Created thread: {thread.id}")

    # Add user message
    assistant.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="What is the quadratic formula and how do I use it?",
    )

    # Create run
    run = assistant.threads.runs.create(thread_id=thread.id)
    print(f"Created run: {run.id}")

    # Wait for completion
    while True:
        run = assistant.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status in [RunStatus.COMPLETED, RunStatus.FAILED]:
            break
        await asyncio.sleep(0.5)

    # Get messages
    messages = assistant.threads.messages.list(thread_id=thread.id)
    for msg in messages:
        print(f"\n{msg.role.upper()}: {msg.content}")


async def example_multi_turn_conversation():
    """Multi - turn conversation example"""
    print("\n=== Example 2: Multi - turn Conversation ===\n")

    assistant = Assistant(
        name="Code Helper",
        instructions="You are a helpful coding assistant. Provide clear, practical code examples.",
        model="llama3.2",
    )

    thread = assistant.threads.create()

    # Turn 1
    assistant.threads.messages.create(
        thread_id=thread.id, role="user", content="How do I read a file in Python?"
    )

    run1 = assistant.threads.runs.create(thread_id=thread.id)
    while assistant.threads.runs.retrieve(thread.id, run1.id).status != RunStatus.COMPLETED:
        await asyncio.sleep(0.5)

    # Turn 2
    assistant.threads.messages.create(
        thread_id=thread.id, role="user", content="What about reading CSV files specifically?"
    )

    run2 = assistant.threads.runs.create(thread_id=thread.id)
    while assistant.threads.runs.retrieve(thread.id, run2.id).status != RunStatus.COMPLETED:
        await asyncio.sleep(0.5)

    # Display conversation
    messages = assistant.threads.messages.list(thread_id=thread.id)
    for msg in messages:
        print(f"\n{msg.role.upper()}: {msg.content[:200]}...")


async def example_assistant_with_tools():
    """Assistant with custom tools"""
    print("\n=== Example 3: Assistant with Tools ===\n")

    # Create custom tool
    class CalculatorTool(Tool):
        def __init__(self):
            super().__init__(
                name="calculator",
                description="Perform mathematical calculations",
                parameters={
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate",
                    }
                },
            )

        async def execute(self, expression: str) -> str:
            try:
                result = eval(expression)
                return f"Result: {result}"
            except Exception as e:
                return f"Error: {str(e)}"

    # Create assistant with tool
    assistant = Assistant(
        name="Calculator Assistant",
        instructions="You help with calculations. Use the calculator tool for complex math.",
        model="llama3.2",
        tools=[CalculatorTool()],
    )

    thread = assistant.threads.create()

    assistant.threads.messages.create(
        thread_id=thread.id, role="user", content="What is 15% of 250?"
    )

    run = assistant.threads.runs.create(thread_id=thread.id)
    while assistant.threads.runs.retrieve(thread.id, run.id).status != RunStatus.COMPLETED:
        await asyncio.sleep(0.5)

    messages = assistant.threads.messages.list(thread_id=thread.id)
    for msg in messages:
        print(f"\n{msg.role.upper()}: {msg.content}")


async def example_custom_instructions():
    """Override instructions per run"""
    print("\n=== Example 4: Custom Instructions per Run ===\n")

    assistant = Assistant(
        name="Writer", instructions="You are a professional writer.", model="llama3.2"
    )

    thread = assistant.threads.create()

    # Run 1: Default instructions
    assistant.threads.messages.create(
        thread_id=thread.id, role="user", content="Write a short paragraph about AI."
    )

    run1 = assistant.threads.runs.create(thread_id=thread.id)
    while assistant.threads.runs.retrieve(thread.id, run1.id).status != RunStatus.COMPLETED:
        await asyncio.sleep(0.5)

    print("\nWith default instructions:")
    messages = assistant.threads.messages.list(thread_id=thread.id)
    print(messages[-1].content[:200])

    # Run 2: Custom instructions
    assistant.threads.messages.create(
        thread_id=thread.id, role="user", content="Write a short paragraph about AI."
    )

    run2 = assistant.threads.runs.create(
        thread_id=thread.id, instructions="You are a poet. Write in verse with rhymes."
    )
    while assistant.threads.runs.retrieve(thread.id, run2.id).status != RunStatus.COMPLETED:
        await asyncio.sleep(0.5)

    print("\nWith custom instructions (poetry):")
    messages = assistant.threads.messages.list(thread_id=thread.id)
    print(messages[-1].content[:200])


async def main():
    """Run all examples"""
    print("=" * 60)
    print("OpenAI Assistants API Compatibility Layer")
    print("=" * 60)

    await example_basic_assistant()
    await example_multi_turn_conversation()
    await example_assistant_with_tools()
    await example_custom_instructions()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
