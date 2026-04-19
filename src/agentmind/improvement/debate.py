"""Debate-based output improvement for multi-agent systems.

Agents can debate and refine outputs through structured argumentation.
"""

import asyncio
from typing import Any, Dict, List, Optional

from ..core.agent import Agent
from ..core.types import Message, MessageRole
from ..llm.provider import LLMProvider


class DebateImprover:
    """Improves outputs through multi-agent debate.

    Multiple agents debate a topic or solution, critiquing each other's
    arguments to arrive at a better final answer.

    Example:
        >>> improver = DebateImprover(llm_provider)
        >>> result = await improver.debate(
        ...     topic="Best approach to solve X",
        ...     agents=[agent1, agent2, agent3],
        ...     rounds=3
        ... )
    """

    def __init__(self, llm_provider: LLMProvider):
        """Initialize the debate improver.

        Args:
            llm_provider: LLM provider for generating debate responses
        """
        self.llm_provider = llm_provider
        self.debate_history: List[Dict[str, Any]] = []

    async def debate(
        self,
        topic: str,
        agents: List[Agent],
        rounds: int = 3,
        judge_agent: Optional[Agent] = None,
    ) -> Dict[str, Any]:
        """Run a debate between agents to improve an output.

        Args:
            topic: The topic or question to debate
            agents: List of agents participating in the debate
            rounds: Number of debate rounds
            judge_agent: Optional judge agent to evaluate arguments

        Returns:
            Dictionary containing debate transcript and final consensus
        """
        if len(agents) < 2:
            raise ValueError("At least 2 agents required for debate")

        debate_transcript: List[Dict[str, str]] = []
        positions: Dict[str, str] = {}

        # Initial positions
        for agent in agents:
            prompt = f"State your position on: {topic}\nBe clear and concise."
            message = Message(
                role=MessageRole.USER,
                content=prompt,
                sender="debate_moderator",
            )
            response = await agent.process_message(message)
            if response:
                positions[agent.name] = response.content
                debate_transcript.append({
                    "round": 0,
                    "agent": agent.name,
                    "type": "initial_position",
                    "content": response.content,
                })

        # Debate rounds
        for round_num in range(1, rounds + 1):
            for i, agent in enumerate(agents):
                # Get other agents' positions
                other_positions = [
                    f"{name}: {pos}"
                    for name, pos in positions.items()
                    if name != agent.name
                ]

                critique_prompt = f"""Round {round_num} of debate on: {topic}

Your current position: {positions[agent.name]}

Other positions:
{chr(10).join(other_positions)}

Critique the other positions and refine your own. Be constructive and specific."""

                message = Message(
                    role=MessageRole.USER,
                    content=critique_prompt,
                    sender="debate_moderator",
                )
                response = await agent.process_message(message)

                if response:
                    positions[agent.name] = response.content
                    debate_transcript.append({
                        "round": round_num,
                        "agent": agent.name,
                        "type": "critique",
                        "content": response.content,
                    })

        # Generate consensus
        consensus = await self._generate_consensus(topic, positions, judge_agent or agents[0])

        result = {
            "topic": topic,
            "transcript": debate_transcript,
            "final_positions": positions,
            "consensus": consensus,
            "rounds": rounds,
            "participants": [a.name for a in agents],
        }

        self.debate_history.append(result)
        return result

    async def _generate_consensus(
        self,
        topic: str,
        positions: Dict[str, str],
        judge: Agent,
    ) -> str:
        """Generate a consensus from the debate positions.

        Args:
            topic: The debate topic
            positions: Final positions from all agents
            judge: Agent to synthesize the consensus

        Returns:
            Consensus statement
        """
        positions_text = "\n\n".join([
            f"{name}'s position:\n{pos}"
            for name, pos in positions.items()
        ])

        consensus_prompt = f"""As a judge, synthesize a consensus from this debate.

Topic: {topic}

Positions:
{positions_text}

Provide a balanced consensus that incorporates the strongest arguments from each position.
Be objective and comprehensive."""

        message = Message(
            role=MessageRole.USER,
            content=consensus_prompt,
            sender="debate_moderator",
        )
        response = await judge.process_message(message)

        return response.content if response else "No consensus reached"

    async def improve_output(
        self,
        original_output: str,
        critic_agents: List[Agent],
        improvement_rounds: int = 2,
    ) -> Dict[str, Any]:
        """Improve an output through iterative criticism.

        Args:
            original_output: The output to improve
            critic_agents: Agents that will critique the output
            improvement_rounds: Number of improvement iterations

        Returns:
            Dictionary with improvement history and final output
        """
        current_output = original_output
        improvement_history = [{"round": 0, "output": original_output}]

        for round_num in range(1, improvement_rounds + 1):
            critiques = []

            # Gather critiques
            for agent in critic_agents:
                critique_prompt = f"""Critique this output and suggest specific improvements:

{current_output}

Focus on:
- Accuracy and correctness
- Clarity and structure
- Completeness
- Practical value

Provide actionable suggestions."""

                message = Message(
                    role=MessageRole.USER,
                    content=critique_prompt,
                    sender="improvement_system",
                )
                response = await agent.process_message(message)
                if response:
                    critiques.append({
                        "agent": agent.name,
                        "critique": response.content,
                    })

            # Generate improved version
            if critiques:
                improvement_prompt = f"""Improve this output based on the critiques:

Original:
{current_output}

Critiques:
"""
                for c in critiques:
                    improvement_prompt += f"\n{c['agent']}: {c['critique']}\n"

                improvement_prompt += "\nProvide an improved version that addresses the critiques."

                message = Message(
                    role=MessageRole.USER,
                    content=improvement_prompt,
                    sender="improvement_system",
                )
                response = await critic_agents[0].process_message(message)

                if response:
                    current_output = response.content
                    improvement_history.append({
                        "round": round_num,
                        "critiques": critiques,
                        "output": current_output,
                    })

        return {
            "original": original_output,
            "final": current_output,
            "history": improvement_history,
            "rounds": improvement_rounds,
        }

    def get_debate_history(self) -> List[Dict[str, Any]]:
        """Get the history of all debates.

        Returns:
            List of debate records
        """
        return self.debate_history
