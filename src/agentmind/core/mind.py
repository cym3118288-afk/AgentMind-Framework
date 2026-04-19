from .agent import Agent, Message
import asyncio
from typing import List, Dict, Any

class AgentMind:
    def __init__(self):
        self.agents: List[Agent] = []
        self.conversation_history: List[Message] = []
        self.is_running = False
        print("[AgentMind] Initialized - Multi-agent collaboration framework started!")

    def add_agent(self, agent: Agent):
        self.agents.append(agent)
        print(f"[+] Added agent: {agent.name} ({agent.role})")

    async def broadcast_message(self, message: Message, exclude_sender: bool = True):
        responses = []
        self.conversation_history.append(message)

        for agent in self.agents:
            if exclude_sender and agent.name == message.sender:
                continue
            response = await agent.process_message(message)
            if response:
                responses.append(response)
                self.conversation_history.append(response)
        return responses

    async def start_collaboration(self, initial_message: str):
        if not self.agents:
            print("[!] No agents available, cannot start collaboration")
            return

        print(f"[*] Starting multi-agent collaboration: {initial_message}")

        # Create initial message
        init_msg = Message(content=initial_message, sender="system")

        # Broadcast to all agents
        responses = await self.broadcast_message(init_msg, exclude_sender=False)

        print(f"[>] Received {len(responses)} responses")
        for response in responses:
            print(f"  {response.content}")

        return responses

    def get_conversation_summary(self) -> Dict[str, Any]:
        return {
            "total_messages": len(self.conversation_history),
            "active_agents": len([a for a in self.agents if a.is_active]),
            "recent_messages": [msg.content for msg in self.conversation_history[-5:]]
        }
