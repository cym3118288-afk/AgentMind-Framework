"""Consensus mechanisms for multi-agent decision making."""

import asyncio
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..core.agent import Agent
from ..core.types import Message, MessageRole


class VotingMechanism(Enum):
    """Voting mechanisms for consensus."""

    MAJORITY = "majority"
    UNANIMOUS = "unanimous"
    WEIGHTED = "weighted"
    RANKED_CHOICE = "ranked_choice"


class ConsensusOrchestrator:
    """Orchestrates consensus-based decision making among agents.

    Agents vote on proposals and reach consensus through various mechanisms.

    Example:
        >>> orchestrator = ConsensusOrchestrator(agents)
        >>> result = await orchestrator.reach_consensus(
        ...     "Should we implement feature X?",
        ...     mechanism=VotingMechanism.MAJORITY
        ... )
    """

    def __init__(self, agents: List[Agent]):
        """Initialize the consensus orchestrator.

        Args:
            agents: List of agents participating in consensus
        """
        self.agents = agents
        self.consensus_history: List[Dict[str, Any]] = []

    async def reach_consensus(
        self,
        proposal: str,
        mechanism: VotingMechanism = VotingMechanism.MAJORITY,
        weights: Optional[Dict[str, float]] = None,
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Reach consensus on a proposal.

        Args:
            proposal: The proposal to vote on
            mechanism: Voting mechanism to use
            weights: Optional weights for weighted voting (agent_name -> weight)
            threshold: Threshold for consensus (0.0 to 1.0)

        Returns:
            Dictionary with consensus result
        """
        # Collect votes from all agents
        votes = await self._collect_votes(proposal)

        # Calculate consensus based on mechanism
        if mechanism == VotingMechanism.MAJORITY:
            result = self._majority_vote(votes, threshold)
        elif mechanism == VotingMechanism.UNANIMOUS:
            result = self._unanimous_vote(votes)
        elif mechanism == VotingMechanism.WEIGHTED:
            result = self._weighted_vote(votes, weights or {}, threshold)
        elif mechanism == VotingMechanism.RANKED_CHOICE:
            result = self._ranked_choice_vote(votes)
        else:
            result = {"consensus": False, "reason": "Unknown mechanism"}

        # Store in history
        consensus_record = {
            "proposal": proposal,
            "mechanism": mechanism.value,
            "votes": votes,
            "result": result,
        }
        self.consensus_history.append(consensus_record)

        return consensus_record

    async def _collect_votes(self, proposal: str) -> Dict[str, Dict[str, Any]]:
        """Collect votes from all agents.

        Args:
            proposal: The proposal to vote on

        Returns:
            Dictionary mapping agent names to their votes
        """
        votes = {}

        for agent in self.agents:
            vote_prompt = f"""Vote on this proposal: {proposal}

Respond with:
1. Your vote: YES, NO, or ABSTAIN
2. Your reasoning (1-2 sentences)
3. Your confidence level (0-100)

Format:
VOTE: [YES/NO/ABSTAIN]
REASONING: [your reasoning]
CONFIDENCE: [0-100]"""

            message = Message(
                role=MessageRole.USER,
                content=vote_prompt,
                sender="consensus_orchestrator",
            )

            response = await agent.process_message(message)

            if response:
                vote_data = self._parse_vote(response.content)
                votes[agent.name] = vote_data

        return votes

    def _parse_vote(self, response: str) -> Dict[str, Any]:
        """Parse vote from agent response.

        Args:
            response: Agent's response

        Returns:
            Dictionary with vote, reasoning, and confidence
        """
        lines = response.strip().split("\n")
        vote = "ABSTAIN"
        reasoning = ""
        confidence = 50

        for line in lines:
            line = line.strip()
            if line.startswith("VOTE:"):
                vote_text = line.replace("VOTE:", "").strip().upper()
                if vote_text in ["YES", "NO", "ABSTAIN"]:
                    vote = vote_text
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = int(line.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    confidence = 50

        return {
            "vote": vote,
            "reasoning": reasoning,
            "confidence": confidence,
        }

    def _majority_vote(self, votes: Dict[str, Dict[str, Any]], threshold: float) -> Dict[str, Any]:
        """Calculate majority vote.

        Args:
            votes: Dictionary of votes
            threshold: Threshold for consensus

        Returns:
            Consensus result
        """
        yes_votes = sum(1 for v in votes.values() if v["vote"] == "YES")
        no_votes = sum(1 for v in votes.values() if v["vote"] == "NO")
        total_votes = yes_votes + no_votes

        if total_votes == 0:
            return {"consensus": False, "reason": "No votes cast"}

        yes_ratio = yes_votes / total_votes

        return {
            "consensus": yes_ratio >= threshold,
            "decision": "YES" if yes_ratio >= threshold else "NO",
            "yes_votes": yes_votes,
            "no_votes": no_votes,
            "ratio": yes_ratio,
        }

    def _unanimous_vote(self, votes: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate unanimous vote.

        Args:
            votes: Dictionary of votes

        Returns:
            Consensus result
        """
        all_yes = all(v["vote"] == "YES" for v in votes.values())
        all_no = all(v["vote"] == "NO" for v in votes.values())

        return {
            "consensus": all_yes or all_no,
            "decision": "YES" if all_yes else "NO" if all_no else "NO_CONSENSUS",
            "unanimous": all_yes or all_no,
        }

    def _weighted_vote(
        self,
        votes: Dict[str, Dict[str, Any]],
        weights: Dict[str, float],
        threshold: float,
    ) -> Dict[str, Any]:
        """Calculate weighted vote.

        Args:
            votes: Dictionary of votes
            weights: Agent weights
            threshold: Threshold for consensus

        Returns:
            Consensus result
        """
        total_weight = 0.0
        yes_weight = 0.0

        for agent_name, vote_data in votes.items():
            weight = weights.get(agent_name, 1.0)
            total_weight += weight

            if vote_data["vote"] == "YES":
                yes_weight += weight

        if total_weight == 0:
            return {"consensus": False, "reason": "No weighted votes"}

        yes_ratio = yes_weight / total_weight

        return {
            "consensus": yes_ratio >= threshold,
            "decision": "YES" if yes_ratio >= threshold else "NO",
            "weighted_ratio": yes_ratio,
        }

    def _ranked_choice_vote(self, votes: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate ranked choice vote (simplified).

        Args:
            votes: Dictionary of votes

        Returns:
            Consensus result
        """
        # Simplified: weight by confidence
        yes_confidence = sum(
            v["confidence"] for v in votes.values() if v["vote"] == "YES"
        )
        no_confidence = sum(
            v["confidence"] for v in votes.values() if v["vote"] == "NO"
        )

        total_confidence = yes_confidence + no_confidence

        if total_confidence == 0:
            return {"consensus": False, "reason": "No confidence scores"}

        return {
            "consensus": True,
            "decision": "YES" if yes_confidence > no_confidence else "NO",
            "yes_confidence": yes_confidence,
            "no_confidence": no_confidence,
        }

    async def multi_round_consensus(
        self,
        proposal: str,
        max_rounds: int = 3,
        mechanism: VotingMechanism = VotingMechanism.MAJORITY,
    ) -> Dict[str, Any]:
        """Reach consensus through multiple rounds of voting and discussion.

        Args:
            proposal: The proposal to vote on
            max_rounds: Maximum number of voting rounds
            mechanism: Voting mechanism to use

        Returns:
            Final consensus result
        """
        rounds = []

        for round_num in range(1, max_rounds + 1):
            # Vote
            result = await self.reach_consensus(proposal, mechanism)
            rounds.append(result)

            # Check if consensus reached
            if result["result"].get("consensus"):
                return {
                    "consensus_reached": True,
                    "rounds": round_num,
                    "final_result": result,
                    "all_rounds": rounds,
                }

            # If not final round, allow discussion
            if round_num < max_rounds:
                await self._facilitate_discussion(proposal, result)

        return {
            "consensus_reached": False,
            "rounds": max_rounds,
            "final_result": rounds[-1],
            "all_rounds": rounds,
        }

    async def _facilitate_discussion(
        self,
        proposal: str,
        previous_result: Dict[str, Any],
    ) -> None:
        """Facilitate discussion between agents after a vote.

        Args:
            proposal: The proposal being discussed
            previous_result: Result from previous voting round
        """
        discussion_prompt = f"""The vote on "{proposal}" did not reach consensus.

Previous votes:
"""
        for agent_name, vote_data in previous_result["votes"].items():
            discussion_prompt += f"\n{agent_name}: {vote_data['vote']} - {vote_data['reasoning']}"

        discussion_prompt += "\n\nDiscuss your position and consider others' viewpoints. Be open to changing your vote if convinced."

        # Let agents discuss
        for agent in self.agents:
            message = Message(
                role=MessageRole.USER,
                content=discussion_prompt,
                sender="consensus_orchestrator",
            )
            await agent.process_message(message)

    def get_consensus_history(self) -> List[Dict[str, Any]]:
        """Get history of consensus decisions.

        Returns:
            List of consensus records
        """
        return self.consensus_history
