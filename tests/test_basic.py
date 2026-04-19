import unittest
import asyncio
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agentmind.core.agent import Agent, Message
from agentmind.core.mind import AgentMind

class TestAgent(unittest.TestCase):
    def test_agent_creation(self):
        agent = Agent("TestAgent", "analyst")
        self.assertEqual(agent.name, "TestAgent")
        self.assertEqual(agent.role, "analyst")
        self.assertTrue(agent.is_active)

    def test_message_creation(self):
        msg = Message(content="Hello", sender="TestAgent")
        self.assertEqual(msg.content, "Hello")
        self.assertEqual(msg.sender, "TestAgent")
        self.assertIsNotNone(msg.timestamp)

    def test_agent_process_message(self):
        agent = Agent("TestAgent", "analyst")
        msg = Message(content="Test message", sender="User")

        # Run async test
        async def run_test():
            response = await agent.process_message(msg)
            self.assertIsNotNone(response)
            self.assertEqual(response.sender, "TestAgent")
            self.assertIn("Test message", response.content)

        asyncio.run(run_test())

class TestAgentMind(unittest.TestCase):
    def test_agentmind_creation(self):
        mind = AgentMind()
        self.assertEqual(len(mind.agents), 0)
        self.assertEqual(len(mind.conversation_history), 0)

    def test_add_agent(self):
        mind = AgentMind()
        agent = Agent("TestAgent", "analyst")
        mind.add_agent(agent)
        self.assertEqual(len(mind.agents), 1)

    def test_collaboration(self):
        mind = AgentMind()
        agent1 = Agent("Agent1", "analyst")
        agent2 = Agent("Agent2", "creative")
        mind.add_agent(agent1)
        mind.add_agent(agent2)

        # Run async test
        async def run_test():
            responses = await mind.start_collaboration("Test collaboration")
            self.assertEqual(len(responses), 2)
            self.assertGreater(len(mind.conversation_history), 0)

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
