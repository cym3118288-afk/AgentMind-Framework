import asyncio
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    content: str
    sender: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class Agent:
    def __init__(self, name: str, role: str = "assistant"):
        self.name = name
        self.role = role
        self.memory: List[Message] = []
        self.is_active = True

    async def process_message(self, message: Message) -> Optional[Message]:
        if not self.is_active:
            return None

        # Generate different response styles based on role
        if self.role == "analyst":
            response_content = f"[Analysis] {self.name}: From a data perspective, '{message.content}' requires further analysis"
        elif self.role == "creative":
            response_content = f"[Creative] {self.name}: This gives me an interesting idea about '{message.content}'"
        elif self.role == "coordinator":
            response_content = f"[Coordination] {self.name}: Let's integrate the perspectives on '{message.content}'"
        else:
            response_content = f"[{self.role}] {self.name}: Received message '{message.content}'"

        response = Message(content=response_content, sender=self.name)

        self.memory.append(message)
        self.memory.append(response)

        return response

    def get_recent_memory(self, limit: int = 5) -> List[Message]:
        return self.memory[-limit:]
