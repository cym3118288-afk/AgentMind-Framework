"""
Advanced Example: Human - in - the - Loop Agent

This example demonstrates agents with human oversight:
- Approval workflows
- Human feedback integration
- Interactive decision making
- Escalation mechanisms
- Collaborative problem solving
- Adaptive behavior based on human input

Estimated time: 25 minutes
Difficulty: Advanced
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime
from agentmind import Agent, Message
from agentmind.llm import OllamaProvider


class ApprovalStatus(str, Enum):
    """Status of approval requests"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class EscalationLevel(str, Enum):
    """Escalation levels"""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequest:
    """Request for human approval"""

    def __init__(
        self,
        request_id: str,
        agent_name: str,
        action: str,
        context: Dict[str, Any],
        risk_level: EscalationLevel = EscalationLevel.LOW,
    ):
        self.request_id = request_id
        self.agent_name = agent_name
        self.action = action
        self.context = context
        self.risk_level = risk_level
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now()
        self.resolved_at: Optional[datetime] = None
        self.human_feedback: Optional[str] = None
        self.modified_action: Optional[str] = None


class HumanFeedback:
    """Human feedback on agent actions"""

    def __init__(
        self,
        feedback_id: str,
        agent_name: str,
        action: str,
        rating: int,  # 1 - 5
        comments: Optional[str] = None,
        suggestions: Optional[str] = None,
    ):
        self.feedback_id = feedback_id
        self.agent_name = agent_name
        self.action = action
        self.rating = rating
        self.comments = comments
        self.suggestions = suggestions
        self.timestamp = datetime.now()


class HumanInterface:
    """Interface for human interaction"""

    def __init__(self):
        self.pending_approvals: List[ApprovalRequest] = []
        self.feedback_history: List[HumanFeedback] = []
        self.approval_callback: Optional[Callable] = None

    async def request_approval(self, request: ApprovalRequest) -> ApprovalStatus:
        """Request human approval"""
        self.pending_approvals.append(request)

        print(f"\n{'=' * 60}")
        print(f"APPROVAL REQUEST #{request.request_id}")
        print(f"{'=' * 60}")
        print(f"Agent: {request.agent_name}")
        print(f"Action: {request.action}")
        print(f"Risk Level: {request.risk_level.value}")
        print(f"Context: {request.context}")
        print("\nOptions:")
        print("  1. Approve")
        print("  2. Reject")
        print("  3. Modify")
        print(f"{'=' * 60}\n")

        # Simulate human decision (in production, this would be actual user input)
        # For demo purposes, auto - approve low risk, escalate high risk
        if request.risk_level in [EscalationLevel.LOW, EscalationLevel.MEDIUM]:
            decision = ApprovalStatus.APPROVED
            print("[Simulated Human Decision: APPROVED]\n")
        else:
            decision = ApprovalStatus.PENDING
            print("[Simulated Human Decision: PENDING - Requires review]\n")

        request.status = decision
        request.resolved_at = datetime.now()

        return decision

    async def get_feedback(self, agent_name: str, action: str, result: str) -> HumanFeedback:
        """Get human feedback on action"""
        print(f"\n{'=' * 60}")
        print("FEEDBACK REQUEST")
        print(f"{'=' * 60}")
        print(f"Agent: {agent_name}")
        print(f"Action: {action}")
        print(f"Result: {result[:100]}...")
        print("\nPlease rate (1 - 5) and provide feedback:")
        print(f"{'=' * 60}\n")

        # Simulate feedback (in production, get actual user input)
        feedback = HumanFeedback(
            feedback_id=f"fb_{len(self.feedback_history)}",
            agent_name=agent_name,
            action=action,
            rating=4,  # Simulated rating
            comments="Good work, but could be more detailed",
            suggestions="Add more examples",
        )

        self.feedback_history.append(feedback)
        print(f"[Simulated Feedback: Rating {feedback.rating}/5]\n")

        return feedback

    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval statistics"""
        total = len(self.pending_approvals)
        if total == 0:
            return {"total": 0}

        approved = sum(1 for r in self.pending_approvals if r.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for r in self.pending_approvals if r.status == ApprovalStatus.REJECTED)

        return {
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": approved / total if total > 0 else 0,
        }


class HumanInLoopAgent(Agent):
    """Agent with human - in - the - loop capabilities"""

    def __init__(
        self,
        *args,
        human_interface: HumanInterface,
        require_approval_for: List[str] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.human_interface = human_interface
        self.require_approval_for = require_approval_for or []
        self.approval_requests = 0
        self.feedback_received = 0

    async def execute_with_approval(
        self,
        action: str,
        context: Dict[str, Any],
        risk_level: EscalationLevel = EscalationLevel.LOW,
    ) -> Dict[str, Any]:
        """Execute action with human approval"""

        # Check if approval is required
        needs_approval = risk_level in [EscalationLevel.HIGH, EscalationLevel.CRITICAL] or any(
            keyword in action.lower() for keyword in self.require_approval_for
        )

        if needs_approval:
            # Request approval
            request = ApprovalRequest(
                request_id=f"req_{self.approval_requests}",
                agent_name=self.name,
                action=action,
                context=context,
                risk_level=risk_level,
            )

            self.approval_requests += 1
            status = await self.human_interface.request_approval(request)

            if status == ApprovalStatus.REJECTED:
                return {"success": False, "message": "Action rejected by human", "action": action}
            elif status == ApprovalStatus.MODIFIED:
                action = request.modified_action or action

        # Execute the action
        message = Message(content=action, sender="system", role="user")
        response = await self.process_message(message)

        return {
            "success": True,
            "result": response.content,
            "action": action,
            "approved": needs_approval,
        }

    async def execute_with_feedback(self, action: str) -> Dict[str, Any]:
        """Execute action and collect human feedback"""

        # Execute action
        message = Message(content=action, sender="system", role="user")
        response = await self.process_message(message)

        # Get human feedback
        feedback = await self.human_interface.get_feedback(self.name, action, response.content)

        self.feedback_received += 1

        # Adapt based on feedback
        if feedback.rating < 3:
            print(f"[Agent {self.name}]: Noted - will improve future responses")

        return {
            "result": response.content,
            "feedback": {
                "rating": feedback.rating,
                "comments": feedback.comments,
                "suggestions": feedback.suggestions,
            },
        }

    def get_interaction_stats(self) -> Dict[str, Any]:
        """Get human interaction statistics"""
        return {
            "approval_requests": self.approval_requests,
            "feedback_received": self.feedback_received,
        }


async def example_1_approval_workflow():
    """Example 1: Basic approval workflow"""
    print("\n=== Example 1: Approval Workflow ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    human_interface = HumanInterface()

    agent = HumanInLoopAgent(
        name="assistant",
        role="assistant",
        llm_provider=llm,
        human_interface=human_interface,
        require_approval_for=["delete", "modify", "send"],
    )

    # Execute action requiring approval
    result = await agent.execute_with_approval(
        action="Delete old user records",
        context={"records": 100, "age": "90 days"},
        risk_level=EscalationLevel.HIGH,
    )

    print(f"Action result: {result['success']}")
    print(f"Required approval: {result.get('approved', False)}\n")


async def example_2_risk_based_escalation():
    """Example 2: Risk - based escalation"""
    print("\n=== Example 2: Risk - Based Escalation ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    human_interface = HumanInterface()

    agent = HumanInLoopAgent(
        name="security_agent", role="security", llm_provider=llm, human_interface=human_interface
    )

    # Test different risk levels
    actions = [
        ("Read system logs", EscalationLevel.LOW),
        ("Modify firewall rules", EscalationLevel.MEDIUM),
        ("Grant admin access", EscalationLevel.HIGH),
        ("Shutdown production server", EscalationLevel.CRITICAL),
    ]

    for action, risk_level in actions:
        print(f"Action: {action} (Risk: {risk_level.value})")
        result = await agent.execute_with_approval(
            action=action, context={"timestamp": datetime.now().isoformat()}, risk_level=risk_level
        )
        print(f"  Approved: {result.get('approved', False)}\n")


async def example_3_feedback_loop():
    """Example 3: Human feedback loop"""
    print("\n=== Example 3: Feedback Loop ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    human_interface = HumanInterface()

    agent = HumanInLoopAgent(
        name="writer", role="writer", llm_provider=llm, human_interface=human_interface
    )

    # Execute with feedback
    result = await agent.execute_with_feedback("Write a brief introduction to machine learning")

    print(f"Feedback rating: {result['feedback']['rating']}/5")
    print(f"Comments: {result['feedback']['comments']}\n")


async def example_4_collaborative_refinement():
    """Example 4: Collaborative refinement"""
    print("\n=== Example 4: Collaborative Refinement ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    human_interface = HumanInterface()

    agent = HumanInLoopAgent(
        name="designer", role="creative", llm_provider=llm, human_interface=human_interface
    )

    print("Iterative refinement with human feedback:\n")

    # Multiple iterations with feedback
    for iteration in range(3):
        print(f"Iteration {iteration + 1}:")
        result = await agent.execute_with_feedback(
            f"Design a logo concept (iteration {iteration + 1})"
        )
        print(f"  Rating: {result['feedback']['rating']}/5\n")


async def example_5_approval_statistics():
    """Example 5: Approval statistics"""
    print("\n=== Example 5: Approval Statistics ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    human_interface = HumanInterface()

    agent = HumanInLoopAgent(
        name="operator", role="operator", llm_provider=llm, human_interface=human_interface
    )

    # Execute multiple actions
    actions = [
        ("Action 1", EscalationLevel.LOW),
        ("Action 2", EscalationLevel.MEDIUM),
        ("Action 3", EscalationLevel.LOW),
    ]

    for action, risk in actions:
        await agent.execute_with_approval(action=action, context={}, risk_level=risk)

    # Get statistics
    stats = human_interface.get_approval_stats()
    agent_stats = agent.get_interaction_stats()

    print("Approval Statistics:")
    print(f"  Total requests: {stats['total']}")
    print(f"  Approved: {stats['approved']}")
    print(f"  Approval rate: {stats['approval_rate']:.1%}")
    print("\nAgent Statistics:")
    print(f"  Approval requests: {agent_stats['approval_requests']}")
    print(f"  Feedback received: {agent_stats['feedback_received']}\n")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("Advanced Example: Human - in - the - Loop Agent")
    print("=" * 60)

    await example_1_approval_workflow()
    await example_2_risk_based_escalation()
    await example_3_feedback_loop()
    await example_4_collaborative_refinement()
    await example_5_approval_statistics()

    print("\n" + "=" * 60)
    print("Example Complete!")
    print("=" * 60)
    print("\nKey Concepts:")
    print("1. Human approval ensures oversight of critical actions")
    print("2. Risk - based escalation prioritizes human attention")
    print("3. Feedback loops enable continuous improvement")
    print("4. Collaborative refinement produces better results")
    print("5. Statistics track human - agent interaction patterns")


if __name__ == "__main__":
    asyncio.run(main())
