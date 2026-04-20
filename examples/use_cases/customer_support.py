"""
Real - world Use Case: Customer Support Automation

This example demonstrates a complete customer support automation system using AgentMind.
The system handles customer inquiries, searches knowledge bases, escalates complex issues,
and provides personalized responses.

Features:
- Multi - agent collaboration for support tasks
- Knowledge base integration
- Ticket classification and routing
- Sentiment analysis
- Automated response generation
- Escalation handling
"""

import asyncio
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@dataclass
class SupportTicket:
    """Represents a customer support ticket"""

    id: str
    customer_name: str
    email: str
    subject: str
    message: str
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.NEW
    category: Optional[str] = None
    sentiment: Optional[str] = None
    response: Optional[str] = None


class KnowledgeBaseTool(Tool):
    """Searches the knowledge base for relevant articles"""

    def __init__(self):
        self.kb = {
            "password_reset": "To reset your password: 1) Go to login page 2) Click 'Forgot Password' 3) Enter your email 4) Check your inbox for reset link",  # noqa: E501
            "billing_issue": "For billing issues: 1) Check your account settings 2) Verify payment method 3) Contact billing@company.com if issue persists",  # noqa: E501
            "feature_request": "We appreciate feature requests! Please submit them via our feedback portal at feedback.company.com",  # noqa: E501
            "technical_issue": "For technical issues: 1) Clear browser cache 2) Try different browser 3) Check system status at status.company.com",  # noqa: E501
            "account_access": "If you can't access your account: 1) Verify your credentials 2) Check if account is active 3) Contact support if locked out",  # noqa: E501
            "refund_policy": "Our refund policy: Full refund within 30 days of purchase. Partial refund within 60 days. Contact billing for processing.",  # noqa: E501
        }

        super().__init__(
            name="search_knowledge_base",
            description="Search the knowledge base for solutions to common issues",
            parameters={
                "query": {"type": "string", "description": "Search query describing the issue"}
            },
        )

    async def execute(self, query: str) -> str:
        """Search knowledge base"""
        query_lower = query.lower()
        results = []

        for key, value in self.kb.items():
            if any(word in query_lower for word in key.split("_")):
                results.append(f"**{key.replace('_', ' ').title()}**\n{value}")

        if results:
            return "\n\n".join(results)
        return "No relevant articles found in knowledge base."


class TicketHistoryTool(Tool):
    """Retrieves customer's ticket history"""

    def __init__(self):
        self.history = {
            "john@example.com": [
                "Previous ticket: Password reset - Resolved",
                "Previous ticket: Billing question - Resolved",
            ],
            "jane@example.com": [
                "Previous ticket: Feature request - In Progress",
                "Previous ticket: Technical issue - Escalated",
            ],
        }

        super().__init__(
            name="get_ticket_history",
            description="Get customer's previous support tickets",
            parameters={"email": {"type": "string", "description": "Customer email address"}},
        )

    async def execute(self, email: str) -> str:
        """Get ticket history"""
        history = self.history.get(email, [])
        if history:
            return "\n".join(history)
        return "No previous tickets found for this customer."


class EscalationTool(Tool):
    """Escalates tickets to human agents"""

    def __init__(self):
        super().__init__(
            name="escalate_ticket",
            description="Escalate complex or urgent issues to human support agents",
            parameters={
                "ticket_id": {"type": "string", "description": "Ticket ID"},
                "reason": {"type": "string", "description": "Reason for escalation"},
            },
        )

    async def execute(self, ticket_id: str, reason: str) -> str:
        """Escalate ticket"""
        return f"Ticket {ticket_id} escalated to human agent. Reason: {reason}. Expected response time: 2 hours."


async def create_support_system() -> AgentMind:
    """Create the customer support multi - agent system"""

    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)

    # Create tools
    kb_tool = KnowledgeBaseTool()
    history_tool = TicketHistoryTool()
    escalation_tool = EscalationTool()

    # 1. Triage Agent - Classifies and prioritizes tickets
    triage_agent = Agent(
        name="Triage_Agent",
        role="ticket_classifier",
        system_prompt="""You are a ticket triage specialist. Your job is to:
        1. Classify tickets into categories (billing, technical, account, feature_request, other)
        2. Assess priority (low, medium, high, urgent)
        3. Detect sentiment (positive, neutral, negative, angry)
        4. Identify if immediate escalation is needed

        Be concise and accurate in your classification.""",
    )

    # 2. Knowledge Agent - Searches for solutions
    knowledge_agent = Agent(
        name="Knowledge_Agent",
        role="knowledge_specialist",
        system_prompt="""You are a knowledge base specialist. Your job is to:
        1. Search the knowledge base for relevant solutions
        2. Find the most applicable articles
        3. Summarize solutions clearly

        Always search the knowledge base before suggesting solutions.""",
        tools=[kb_tool, history_tool],
    )

    # 3. Response Agent - Crafts personalized responses
    response_agent = Agent(
        name="Response_Agent",
        role="response_writer",
        system_prompt="""You are a customer support response specialist. Your job is to:
        1. Write empathetic, professional responses
        2. Personalize based on customer history
        3. Provide clear, actionable solutions
        4. Match the tone to customer sentiment
        5. Be concise but thorough

        Always be helpful and customer - focused.""",
    )

    # 4. Escalation Agent - Handles complex cases
    escalation_agent = Agent(
        name="Escalation_Agent",
        role="escalation_specialist",
        system_prompt="""You are an escalation specialist. Your job is to:
        1. Identify cases that need human intervention
        2. Determine appropriate escalation reasons
        3. Provide context for human agents

        Escalate when: issue is complex, customer is angry, or automated solution isn't sufficient.""",
        tools=[escalation_tool],
    )

    mind.add_agent(triage_agent)
    mind.add_agent(knowledge_agent)
    mind.add_agent(response_agent)
    mind.add_agent(escalation_agent)

    return mind


async def process_ticket(mind: AgentMind, ticket: SupportTicket) -> SupportTicket:
    """Process a support ticket through the multi - agent system"""

    print(f"\n{'='*60}")
    print(f"Processing Ticket: {ticket.id}")
    print(f"Customer: {ticket.customer_name} ({ticket.email})")
    print(f"Subject: {ticket.subject}")
    print(f"Message: {ticket.message}")
    print(f"{'='*60}\n")

    # Create comprehensive context for agents
    context = """
    Ticket ID: {ticket.id}
    Customer: {ticket.customer_name} ({ticket.email})
    Subject: {ticket.subject}
    Message: {ticket.message}

    Please process this support ticket:
    1. Classify and prioritize
    2. Search for solutions
    3. Generate appropriate response
    4. Escalate if necessary
    """

    # Collaborate to resolve ticket
    result = await mind.collaborate(context, max_rounds=4)

    # Update ticket with results
    ticket.response = result
    ticket.status = TicketStatus.RESOLVED

    print(f"\n{'='*60}")
    print(f"Ticket {ticket.id} Processed")
    print(f"Status: {ticket.status}")
    print(f"\nResponse:\n{ticket.response}")
    print(f"{'='*60}\n")

    return ticket


async def example_simple_inquiry():
    """Example 1: Simple password reset request"""
    print("\n=== Example 1: Simple Password Reset ===\n")

    mind = await create_support_system()

    ticket = SupportTicket(
        id="TICK - 001",
        customer_name="John Doe",
        email="john@example.com",
        subject="Can't log in",
        message="Hi, I forgot my password and can't access my account. Can you help?",
    )

    await process_ticket(mind, ticket)


async def example_billing_issue():
    """Example 2: Billing complaint"""
    print("\n=== Example 2: Billing Issue ===\n")

    mind = await create_support_system()

    ticket = SupportTicket(
        id="TICK - 002",
        customer_name="Jane Smith",
        email="jane@example.com",
        subject="Charged twice!",
        message="I was charged twice this month! This is unacceptable. I want a refund immediately.",
    )

    await process_ticket(mind, ticket)


async def example_technical_issue():
    """Example 3: Technical problem"""
    print("\n=== Example 3: Technical Issue ===\n")

    mind = await create_support_system()

    ticket = SupportTicket(
        id="TICK - 003",
        customer_name="Bob Johnson",
        email="bob@example.com",
        subject="App keeps crashing",
        message="The mobile app crashes every time I try to upload a file. I've tried restarting but it doesn't help.",
    )

    await process_ticket(mind, ticket)


async def example_feature_request():
    """Example 4: Feature request"""
    print("\n=== Example 4: Feature Request ===\n")

    mind = await create_support_system()

    ticket = SupportTicket(
        id="TICK - 004",
        customer_name="Alice Williams",
        email="alice@example.com",
        subject="Feature suggestion",
        message="Love your product! Would be great if you could add dark mode. Many users would appreciate it.",
    )

    await process_ticket(mind, ticket)


async def example_complex_issue():
    """Example 5: Complex issue requiring escalation"""
    print("\n=== Example 5: Complex Issue (Escalation) ===\n")

    mind = await create_support_system()

    ticket = SupportTicket(
        id="TICK - 005",
        customer_name="Charlie Brown",
        email="charlie@example.com",
        subject="Data loss after update",
        message="After the latest update, all my data is gone! I had important files stored. This is a disaster. I need this fixed ASAP or I want a full refund and compensation.",  # noqa: E501
    )

    await process_ticket(mind, ticket)


async def example_batch_processing():
    """Example 6: Process multiple tickets in batch"""
    print("\n=== Example 6: Batch Processing ===\n")

    mind = await create_support_system()

    tickets = [
        SupportTicket(
            "TICK - 101",
            "User A",
            "usera@example.com",
            "Password reset",
            "Need to reset my password",
        ),
        SupportTicket(
            "TICK - 102",
            "User B",
            "userb@example.com",
            "Billing question",
            "What's my current plan?",
        ),
        SupportTicket(
            "TICK - 103",
            "User C",
            "userc@example.com",
            "Feature request",
            "Please add export feature",
        ),
    ]

    print(f"Processing {len(tickets)} tickets in batch...\n")

    # Process tickets concurrently
    tasks = [process_ticket(mind, ticket) for ticket in tickets]
    results = await asyncio.gather(*tasks)

    print(f"\nBatch processing complete! Processed {len(results)} tickets.")


async def main():
    """Run all customer support examples"""
    print("=" * 60)
    print("Customer Support Automation with AgentMind")
    print("=" * 60)

    await example_simple_inquiry()
    await example_billing_issue()
    await example_technical_issue()
    await example_feature_request()
    await example_complex_issue()
    await example_batch_processing()

    print("\n" + "=" * 60)
    print("Customer support examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
