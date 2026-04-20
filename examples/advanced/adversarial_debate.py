"""
Advanced Example: Adversarial Debate System

This example demonstrates agents engaging in structured debates:
- Multiple perspectives and viewpoints
- Argument construction and counter-arguments
- Evidence-based reasoning
- Moderator-guided discussion
- Consensus building
- Critical thinking and analysis

Estimated time: 30 minutes
Difficulty: Advanced
"""

import asyncio
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
from agentmind import Agent, AgentMind, Message
from agentmind.llm import OllamaProvider


class DebatePosition(str, Enum):
    """Debate positions"""
    FOR = "for"
    AGAINST = "against"
    NEUTRAL = "neutral"


class ArgumentType(str, Enum):
    """Types of arguments"""
    OPENING = "opening"
    REBUTTAL = "rebuttal"
    EVIDENCE = "evidence"
    CLOSING = "closing"


class Argument:
    """Represents a debate argument"""

    def __init__(
        self,
        speaker: str,
        position: DebatePosition,
        argument_type: ArgumentType,
        content: str,
        evidence: Optional[List[str]] = None
    ):
        self.speaker = speaker
        self.position = position
        self.argument_type = argument_type
        self.content = content
        self.evidence = evidence or []
        self.timestamp = datetime.now()
        self.rebuttals: List['Argument'] = []

    def add_rebuttal(self, rebuttal: 'Argument'):
        """Add a rebuttal to this argument"""
        self.rebuttals.append(rebuttal)


class DebateRound:
    """Represents a round in the debate"""

    def __init__(self, round_number: int, topic: str):
        self.round_number = round_number
        self.topic = topic
        self.arguments: List[Argument] = []
        self.started_at = datetime.now()
        self.ended_at: Optional[datetime] = None

    def add_argument(self, argument: Argument):
        """Add argument to this round"""
        self.arguments.append(argument)

    def get_summary(self) -> Dict[str, Any]:
        """Get round summary"""
        return {
            "round": self.round_number,
            "topic": self.topic,
            "arguments": len(self.arguments),
            "for_position": sum(1 for a in self.arguments if a.position == DebatePosition.FOR),
            "against_position": sum(1 for a in self.arguments if a.position == DebatePosition.AGAINST)
        }


class DebateAgent(Agent):
    """Agent specialized for debate participation"""

    def __init__(
        self,
        *args,
        position: DebatePosition,
        expertise: List[str] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.position = position
        self.expertise = expertise or []
        self.arguments_made: List[Argument] = []
        self.rebuttals_made = 0

    async def make_argument(
        self,
        topic: str,
        argument_type: ArgumentType,
        context: Optional[str] = None
    ) -> Argument:
        """Make an argument on the topic"""

        # Construct prompt based on position and type
        prompt = self._construct_prompt(topic, argument_type, context)

        # Generate argument
        message = Message(content=prompt, sender="moderator", role="user")
        response = await self.process_message(message)

        # Create argument
        argument = Argument(
            speaker=self.name,
            position=self.position,
            argument_type=argument_type,
            content=response.content,
            evidence=self._extract_evidence(response.content)
        )

        self.arguments_made.append(argument)
        return argument

    def _construct_prompt(
        self,
        topic: str,
        argument_type: ArgumentType,
        context: Optional[str]
    ) -> str:
        """Construct debate prompt"""
        position_text = "in favor of" if self.position == DebatePosition.FOR else "against"

        if argument_type == ArgumentType.OPENING:
            prompt = f"Make an opening argument {position_text} the following topic: {topic}"
        elif argument_type == ArgumentType.REBUTTAL:
            prompt = f"Make a rebuttal {position_text} the topic: {topic}\n\nOpposing argument: {context}"
        elif argument_type == ArgumentType.EVIDENCE:
            prompt = f"Provide evidence {position_text} the topic: {topic}"
        else:  # CLOSING
            prompt = f"Make a closing argument {position_text} the topic: {topic}\n\nDebate context: {context}"

        return prompt

    def _extract_evidence(self, content: str) -> List[str]:
        """Extract evidence from argument (simplified)"""
        # In production, use more sophisticated extraction
        evidence = []
        if "study" in content.lower() or "research" in content.lower():
            evidence.append("research_based")
        if "data" in content.lower() or "statistics" in content.lower():
            evidence.append("data_driven")
        return evidence

    def get_stats(self) -> Dict[str, Any]:
        """Get debate statistics"""
        return {
            "name": self.name,
            "position": self.position.value,
            "arguments_made": len(self.arguments_made),
            "rebuttals_made": self.rebuttals_made,
            "expertise": self.expertise
        }


class Moderator(Agent):
    """Moderator agent for debate management"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debates_moderated = 0

    async def introduce_topic(self, topic: str) -> str:
        """Introduce the debate topic"""
        prompt = f"As a debate moderator, introduce this topic: {topic}"
        message = Message(content=prompt, sender="system", role="user")
        response = await self.process_message(message)
        return response.content

    async def summarize_round(self, debate_round: DebateRound) -> str:
        """Summarize a debate round"""
        summary = debate_round.get_summary()
        prompt = f"Summarize this debate round: {summary}"
        message = Message(content=prompt, sender="system", role="user")
        response = await self.process_message(message)
        return response.content

    async def declare_winner(
        self,
        arguments_for: List[Argument],
        arguments_against: List[Argument]
    ) -> Dict[str, Any]:
        """Analyze arguments and provide assessment"""
        prompt = f"""Analyze these debate arguments and provide an assessment:

Arguments FOR: {len(arguments_for)} arguments
Arguments AGAINST: {len(arguments_against)} arguments

Evaluate based on:
1. Strength of reasoning
2. Quality of evidence
3. Persuasiveness
4. Logical consistency
"""
        message = Message(content=prompt, sender="system", role="user")
        response = await self.process_message(message)

        return {
            "assessment": response.content,
            "arguments_for": len(arguments_for),
            "arguments_against": len(arguments_against)
        }


class DebateSystem:
    """System for managing structured debates"""

    def __init__(self, topic: str, moderator: Moderator):
        self.topic = topic
        self.moderator = moderator
        self.participants: List[DebateAgent] = []
        self.rounds: List[DebateRound] = []
        self.current_round: Optional[DebateRound] = None

    def add_participant(self, agent: DebateAgent):
        """Add debate participant"""
        self.participants.append(agent)

    async def start_debate(self, num_rounds: int = 3):
        """Start the debate"""
        print(f"\n{'='*60}")
        print(f"DEBATE: {self.topic}")
        print(f"{'='*60}\n")

        # Introduction
        intro = await self.moderator.introduce_topic(self.topic)
        print(f"Moderator: {intro}\n")

        # Conduct rounds
        for round_num in range(1, num_rounds + 1):
            await self._conduct_round(round_num)

        # Final assessment
        await self._final_assessment()

    async def _conduct_round(self, round_num: int):
        """Conduct a debate round"""
        print(f"\n{'='*60}")
        print(f"ROUND {round_num}")
        print(f"{'='*60}\n")

        debate_round = DebateRound(round_num, self.topic)
        self.current_round = debate_round

        # Determine argument type
        if round_num == 1:
            arg_type = ArgumentType.OPENING
        elif round_num == len(self.rounds) + 1:
            arg_type = ArgumentType.CLOSING
        else:
            arg_type = ArgumentType.REBUTTAL

        # Each participant makes an argument
        context = None
        for participant in self.participants:
            argument = await participant.make_argument(
                self.topic,
                arg_type,
                context
            )
            debate_round.add_argument(argument)

            print(f"{participant.name} ({participant.position.value}):")
            print(f"{argument.content[:200]}...\n")

            # Use this argument as context for rebuttals
            if arg_type == ArgumentType.REBUTTAL:
                context = argument.content

        debate_round.ended_at = datetime.now()
        self.rounds.append(debate_round)

        # Moderator summary
        summary = await self.moderator.summarize_round(debate_round)
        print(f"Moderator Summary: {summary[:150]}...\n")

    async def _final_assessment(self):
        """Provide final debate assessment"""
        print(f"\n{'='*60}")
        print(f"FINAL ASSESSMENT")
        print(f"{'='*60}\n")

        # Collect all arguments
        arguments_for = []
        arguments_against = []

        for debate_round in self.rounds:
            for argument in debate_round.arguments:
                if argument.position == DebatePosition.FOR:
                    arguments_for.append(argument)
                elif argument.position == DebatePosition.AGAINST:
                    arguments_against.append(argument)

        # Get moderator assessment
        assessment = await self.moderator.declare_winner(
            arguments_for,
            arguments_against
        )

        print(f"Assessment: {assessment['assessment'][:300]}...\n")
        print(f"Total Arguments FOR: {assessment['arguments_for']}")
        print(f"Total Arguments AGAINST: {assessment['arguments_against']}\n")

    def get_debate_stats(self) -> Dict[str, Any]:
        """Get debate statistics"""
        return {
            "topic": self.topic,
            "rounds": len(self.rounds),
            "participants": len(self.participants),
            "total_arguments": sum(len(r.arguments) for r in self.rounds),
            "participant_stats": [p.get_stats() for p in self.participants]
        }


async def example_1_simple_debate():
    """Example 1: Simple two-sided debate"""
    print("\n=== Example 1: Simple Debate ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create moderator
    moderator = Moderator(
        name="moderator",
        role="moderator",
        llm_provider=llm
    )

    # Create debate system
    debate = DebateSystem(
        topic="Should AI development be regulated?",
        moderator=moderator
    )

    # Add participants
    proponent = DebateAgent(
        name="proponent",
        role="debater",
        llm_provider=llm,
        position=DebatePosition.FOR,
        expertise=["AI ethics", "policy"]
    )

    opponent = DebateAgent(
        name="opponent",
        role="debater",
        llm_provider=llm,
        position=DebatePosition.AGAINST,
        expertise=["innovation", "technology"]
    )

    debate.add_participant(proponent)
    debate.add_participant(opponent)

    # Start debate
    await debate.start_debate(num_rounds=2)


async def example_2_multi_perspective_debate():
    """Example 2: Multi-perspective debate"""
    print("\n=== Example 2: Multi-Perspective Debate ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    moderator = Moderator(name="moderator", role="moderator", llm_provider=llm)

    debate = DebateSystem(
        topic="Remote work vs. office work",
        moderator=moderator
    )

    # Multiple perspectives
    perspectives = [
        ("remote_advocate", DebatePosition.FOR, ["productivity", "flexibility"]),
        ("office_advocate", DebatePosition.AGAINST, ["collaboration", "culture"]),
    ]

    for name, position, expertise in perspectives:
        agent = DebateAgent(
            name=name,
            role="debater",
            llm_provider=llm,
            position=position,
            expertise=expertise
        )
        debate.add_participant(agent)

    await debate.start_debate(num_rounds=2)

    # Show statistics
    stats = debate.get_debate_stats()
    print(f"\nDebate Statistics:")
    print(f"  Total rounds: {stats['rounds']}")
    print(f"  Total arguments: {stats['total_arguments']}\n")


async def example_3_evidence_based_debate():
    """Example 3: Evidence-based debate"""
    print("\n=== Example 3: Evidence-Based Debate ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create agents focused on evidence
    proponent = DebateAgent(
        name="researcher_pro",
        role="researcher",
        llm_provider=llm,
        position=DebatePosition.FOR,
        expertise=["research", "data analysis"]
    )

    opponent = DebateAgent(
        name="researcher_con",
        role="researcher",
        llm_provider=llm,
        position=DebatePosition.AGAINST,
        expertise=["research", "statistics"]
    )

    # Make evidence-based arguments
    topic = "Climate change requires immediate action"

    arg_pro = await proponent.make_argument(topic, ArgumentType.EVIDENCE)
    print(f"Evidence FOR:")
    print(f"  {arg_pro.content[:150]}...")
    print(f"  Evidence types: {arg_pro.evidence}\n")

    arg_con = await opponent.make_argument(topic, ArgumentType.EVIDENCE)
    print(f"Evidence AGAINST:")
    print(f"  {arg_con.content[:150]}...")
    print(f"  Evidence types: {arg_con.evidence}\n")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("Advanced Example: Adversarial Debate System")
    print("=" * 60)

    await example_1_simple_debate()
    await example_2_multi_perspective_debate()
    await example_3_evidence_based_debate()

    print("\n" + "=" * 60)
    print("Example Complete!")
    print("=" * 60)
    print("\nKey Concepts:")
    print("1. Structured debates explore multiple perspectives")
    print("2. Moderators guide discussion and maintain structure")
    print("3. Evidence-based arguments strengthen positions")
    print("4. Rebuttals challenge opposing viewpoints")
    print("5. Critical analysis leads to better understanding")


if __name__ == "__main__":
    asyncio.run(main())
