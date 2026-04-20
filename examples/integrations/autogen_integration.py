"""
AutoGen Integration Example

This example demonstrates integration between AgentMind and Microsoft AutoGen:
- Converting AutoGen agents to AgentMind agents
- Using AutoGen's group chat with AgentMind orchestration
- Code execution capabilities
- Compatibility layer

Note: This is a compatibility example. Install autogen with:
pip install pyautogen
"""

import asyncio
from typing import Dict, List, Any, Optional
from agentmind import Agent, AgentMind, Message
from agentmind.llm import OllamaProvider


class AutoGenCompatAgent(Agent):
    """AgentMind agent with AutoGen - like interface"""

    def __init__(self, *args, system_message: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.system_message = system_message or f"You are {self.name}, a helpful assistant."
        self.conversation_history = []

    async def generate_reply(
        self, messages: List[Dict[str, str]], sender: Optional[str] = None
    ) -> str:
        """AutoGen - style reply generation"""
        # Convert AutoGen message format to AgentMind format
        if messages:
            last_message = messages[-1]
            content = last_message.get("content", "")

            message = Message(content=content, sender=sender or "user", role="user")

            response = await self.process_message(message)
            return response.content

        return "No message to respond to"

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation in AutoGen format"""
        history = []
        for msg in self.memory:
            history.append({"role": msg.role, "content": msg.content, "name": msg.sender})
        return history


class GroupChatManager:
    """AutoGen - style group chat manager"""

    def __init__(self, agents: List[AutoGenCompatAgent], max_rounds: int = 10):
        self.agents = agents
        self.max_rounds = max_rounds
        self.messages: List[Dict[str, Any]] = []

    async def run_chat(self, initial_message: str) -> List[Dict[str, Any]]:
        """Run group chat similar to AutoGen"""
        self.messages = [{"role": "user", "content": initial_message, "name": "user"}]

        for round_num in range(self.max_rounds):
            # Select next speaker (round - robin for simplicity)
            speaker = self.agents[round_num % len(self.agents)]

            # Generate reply
            reply = await speaker.generate_reply(self.messages, sender="system")

            # Add to messages
            self.messages.append({"role": "assistant", "content": reply, "name": speaker.name})

            # Check for termination
            if self._should_terminate(reply):
                break

        return self.messages

    def _should_terminate(self, message: str) -> bool:
        """Check if conversation should terminate"""
        termination_keywords = ["TERMINATE", "DONE", "FINISHED"]
        return any(keyword in message.upper() for keyword in termination_keywords)


class CodeExecutor:
    """AutoGen - style code execution"""

    def __init__(self, work_dir: str = "/tmp"):
        self.work_dir = work_dir
        self.execution_history: List[Dict[str, Any]] = []

    async def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code (simulated for safety)"""
        # In production, use actual code execution with sandboxing
        result = {
            "success": True,
            "output": f"[Simulated execution of {language} code]\n{code[:100]}...",
            "language": language,
            "code": code,
        }

        self.execution_history.append(result)
        return result

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get code execution history"""
        return self.execution_history.copy()


async def example_1_basic_autogen_compat():
    """Example 1: Basic AutoGen compatibility"""
    print("\n=== Example 1: AutoGen Compatibility ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create AutoGen - compatible agent
    agent = AutoGenCompatAgent(
        name="assistant",
        role="assistant",
        llm_provider=llm,
        system_message="You are a helpful AI assistant.",
    )

    # Use AutoGen - style interface
    messages = [{"role": "user", "content": "Hello! How are you?"}]
    reply = await agent.generate_reply(messages, sender="user")

    print("User: Hello! How are you?")
    print(f"Agent: {reply}\n")


async def example_2_group_chat():
    """Example 2: AutoGen - style group chat"""
    print("\n=== Example 2: Group Chat ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create multiple agents
    agents = [
        AutoGenCompatAgent(
            name="planner",
            role="planner",
            llm_provider=llm,
            system_message="You are a strategic planner.",
        ),
        AutoGenCompatAgent(
            name="engineer",
            role="engineer",
            llm_provider=llm,
            system_message="You are a software engineer.",
        ),
        AutoGenCompatAgent(
            name="critic",
            role="critic",
            llm_provider=llm,
            system_message="You are a critical reviewer.",
        ),
    ]

    # Create group chat manager
    manager = GroupChatManager(agents, max_rounds=3)

    # Run group chat
    messages = await manager.run_chat("Let's design a new mobile app for task management.")

    print("Group Chat Conversation:")
    for msg in messages:
        print(f"{msg['name']}: {msg['content'][:100]}...\n")


async def example_3_code_execution():
    """Example 3: Code execution capability"""
    print("\n=== Example 3: Code Execution ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create agent with code execution
    agent = AutoGenCompatAgent(
        name="coder",
        role="developer",
        llm_provider=llm,
        system_message="You are a Python programmer.",
    )

    executor = CodeExecutor()

    # Agent generates code
    messages = [{"role": "user", "content": "Write a function to calculate fibonacci numbers"}]
    code_response = await agent.generate_reply(messages)

    print(f"Agent generated code:\n{code_response[:200]}...\n")

    # Execute the code
    sample_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(10))
"""

    result = await executor.execute_code(sample_code)
    print(f"Execution result: {result['output']}\n")


async def example_4_autogen_to_agentmind():
    """Example 4: Converting AutoGen patterns to AgentMind"""
    print("\n=== Example 4: AutoGen to AgentMind ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # AutoGen - style agents
    autogen_agents = [
        AutoGenCompatAgent(name="agent1", role="analyst", llm_provider=llm),
        AutoGenCompatAgent(name="agent2", role="writer", llm_provider=llm),
    ]

    # Convert to AgentMind orchestration
    mind = AgentMind(strategy="round_robin")
    for agent in autogen_agents:
        mind.add_agent(agent)

    # Use AgentMind orchestration
    result = await mind.start_collaboration(
        "Analyze market trends and write a summary", max_rounds=2
    )

    print("Using AgentMind orchestration with AutoGen - compatible agents:")
    print(f"Result: {result.final_output[:200]}...\n")


async def example_5_hybrid_system():
    """Example 5: Hybrid AutoGen + AgentMind system"""
    print("\n=== Example 5: Hybrid System ===\n")

    # _llm = OllamaProvider(model="llama3.2:3b")

    # Create hybrid system
    print("Hybrid System Features:")
    print("  - AutoGen - style agent interface")
    print("  - AgentMind orchestration")
    print("  - Code execution capabilities")
    print("  - Group chat management")
    print("\nBest of both frameworks!\n")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("AutoGen Integration Example")
    print("=" * 60)

    await example_1_basic_autogen_compat()
    await example_2_group_chat()
    await example_3_code_execution()
    await example_4_autogen_to_agentmind()
    await example_5_hybrid_system()

    print("\n" + "=" * 60)
    print("Example Complete!")
    print("=" * 60)
    print("\nKey Concepts:")
    print("1. AutoGen compatibility layer enables migration")
    print("2. Group chat patterns work with AgentMind")
    print("3. Code execution can be integrated")
    print("4. Hybrid systems combine strengths")
    print("5. AgentMind provides additional orchestration options")


if __name__ == "__main__":
    asyncio.run(main())
