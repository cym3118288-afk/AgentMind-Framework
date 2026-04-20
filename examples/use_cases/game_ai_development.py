"""
Real - world Use Case: Game AI Development

This example demonstrates a game AI development system using AgentMind.
The system creates intelligent game agents with different behaviors, strategies,
and decision - making capabilities for various game genres.

Features:
- Multi - agent game AI design
- Behavior tree generation
- Strategy optimization
- Difficulty balancing
- Player behavior analysis
- Adaptive AI systems
"""

import asyncio
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class GameGenre(str, Enum):
    RPG = "rpg"
    STRATEGY = "strategy"
    FPS = "fps"
    PUZZLE = "puzzle"
    RACING = "racing"
    SPORTS = "sports"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class AIBehaviorType(str, Enum):
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    BALANCED = "balanced"
    ADAPTIVE = "adaptive"
    STRATEGIC = "strategic"


@dataclass
class GameState:
    """Represents the current game state"""

    player_position: Tuple[float, float]
    player_health: float
    player_resources: Dict[str, int]
    enemies: List[Dict]
    objectives: List[str]
    time_elapsed: float


@dataclass
class AIAgent:
    """Represents a game AI agent"""

    agent_id: str
    name: str
    behavior_type: AIBehaviorType
    difficulty: DifficultyLevel
    stats: Dict[str, float]
    decision_tree: Dict
    learning_enabled: bool = False


@dataclass
class GameAIDesign:
    """Complete game AI design"""

    game_genre: GameGenre
    ai_agents: List[AIAgent]
    behavior_trees: Dict[str, any]
    difficulty_scaling: Dict[str, any]
    balancing_parameters: Dict[str, float]
    adaptive_features: List[str]


# Custom Tools for Game AI


class BehaviorTreeGeneratorTool(Tool):
    """Generates behavior trees for game AI"""

    def __init__(self):
        super().__init__(
            name="generate_behavior_tree",
            description="Generate AI behavior tree for game agents",
            parameters={
                "agent_type": {"type": "string", "description": "Type of AI agent"},
                "behavior": {"type": "string", "description": "Desired behavior pattern"},
                "difficulty": {"type": "string", "description": "Difficulty level"},
            },
        )

    async def execute(self, agent_type: str, behavior: str, difficulty: str) -> str:
        """Generate behavior tree"""

        # Base behavior tree structure
        behavior_tree = {"root": "selector", "children": []}

        # Add behaviors based on type
        if behavior == "aggressive":
            behavior_tree["children"] = [
                {
                    "type": "sequence",
                    "name": "attack_sequence",
                    "children": [
                        {"action": "detect_player", "range": 50},
                        {
                            "action": "move_towards_player",
                            "speed": 1.5 if difficulty == "hard" else 1.0,
                        },
                        {"action": "attack", "damage": 20 if difficulty == "hard" else 10},
                    ],
                },
                {"type": "action", "name": "patrol", "waypoints": ["A", "B", "C"]},
            ]
        elif behavior == "defensive":
            behavior_tree["children"] = [
                {
                    "type": "sequence",
                    "name": "defend_sequence",
                    "children": [
                        {"condition": "health_below", "threshold": 0.5},
                        {"action": "retreat", "distance": 20},
                        {"action": "heal", "amount": 30},
                    ],
                },
                {"type": "action", "name": "guard_position"},
            ]
        elif behavior == "strategic":
            behavior_tree["children"] = [
                {
                    "type": "selector",
                    "name": "strategic_choice",
                    "children": [
                        {"condition": "has_advantage", "action": "aggressive_push"},
                        {"condition": "outnumbered", "action": "tactical_retreat"},
                        {"action": "flank_maneuver"},
                    ],
                }
            ]

        return f"Behavior Tree: {behavior_tree}"


class DifficultyBalancerTool(Tool):
    """Balances game difficulty dynamically"""

    def __init__(self):
        super().__init__(
            name="balance_difficulty",
            description="Adjust game difficulty based on player performance",
            parameters={
                "player_stats": {"type": "object", "description": "Player performance statistics"},
                "current_difficulty": {"type": "string", "description": "Current difficulty level"},
            },
        )

    async def execute(self, player_stats: Dict, current_difficulty: str) -> str:
        """Balance difficulty"""

        # Analyze player performance
        win_rate = player_stats.get("win_rate", 0.5)
        player_stats.get("avg_completion_time", 300)
        deaths = player_stats.get("deaths", 5)

        # Calculate difficulty adjustment
        adjustment = {"current_difficulty": current_difficulty, "recommended_adjustment": "none"}

        # Too easy - player winning too much
        if win_rate > 0.75 and deaths < 2:
            adjustment["recommended_adjustment"] = "increase"
            adjustment["changes"] = {
                "enemy_health": "+20%",
                "enemy_damage": "+15%",
                "enemy_count": "+1",
                "player_resources": "-10%",
            }
        # Too hard - player struggling
        elif win_rate < 0.3 or deaths > 10:
            adjustment["recommended_adjustment"] = "decrease"
            adjustment["changes"] = {
                "enemy_health": "-20%",
                "enemy_damage": "-15%",
                "player_health_regen": "+25%",
                "hint_frequency": "+50%",
            }
        else:
            adjustment["recommended_adjustment"] = "maintain"
            adjustment["changes"] = {}

        return f"Difficulty Adjustment: {adjustment}"


class PlayerBehaviorAnalyzerTool(Tool):
    """Analyzes player behavior patterns"""

    def __init__(self):
        super().__init__(
            name="analyze_player_behavior",
            description="Analyze player behavior and play style",
            parameters={
                "gameplay_data": {"type": "object", "description": "Player gameplay data"},
                "session_count": {"type": "integer", "description": "Number of sessions"},
            },
        )

    async def execute(self, gameplay_data: Dict, session_count: int = 1) -> str:
        """Analyze player behavior"""

        analysis = {
            "play_style": "unknown",
            "skill_level": "intermediate",
            "preferences": [],
            "weaknesses": [],
            "recommendations": [],
        }

        # Determine play style
        aggression = gameplay_data.get("attacks_per_minute", 5)
        exploration = gameplay_data.get("areas_explored", 50)
        stealth = gameplay_data.get("stealth_kills", 0)

        if aggression > 10:
            analysis["play_style"] = "aggressive"
            analysis["recommendations"].append("Provide more combat challenges")
        elif stealth > 5:
            analysis["play_style"] = "stealthy"
            analysis["recommendations"].append("Add more stealth opportunities")
        elif exploration > 80:
            analysis["play_style"] = "explorer"
            analysis["recommendations"].append("Include hidden areas and secrets")
        else:
            analysis["play_style"] = "balanced"

        # Assess skill level
        accuracy = gameplay_data.get("accuracy", 0.5)
        reaction_time = gameplay_data.get("avg_reaction_time", 500)

        if accuracy > 0.7 and reaction_time < 300:
            analysis["skill_level"] = "expert"
        elif accuracy > 0.5 and reaction_time < 500:
            analysis["skill_level"] = "advanced"
        elif accuracy < 0.3 or reaction_time > 700:
            analysis["skill_level"] = "beginner"

        return f"Player Analysis: {analysis}"


class StrategyOptimizerTool(Tool):
    """Optimizes AI strategies"""

    def __init__(self):
        super().__init__(
            name="optimize_strategy",
            description="Optimize AI strategy based on game state",
            parameters={
                "game_state": {"type": "object", "description": "Current game state"},
                "ai_resources": {"type": "object", "description": "AI available resources"},
                "objective": {"type": "string", "description": "AI objective"},
            },
        )

    async def execute(self, game_state: Dict, ai_resources: Dict, objective: str) -> str:
        """Optimize strategy"""

        strategy = {
            "objective": objective,
            "priority_actions": [],
            "resource_allocation": {},
            "tactical_decisions": [],
        }

        # Analyze game state
        player_strength = game_state.get("player_health", 100) * game_state.get("player_level", 1)
        ai_strength = sum(ai_resources.values())

        # Determine strategy
        if ai_strength > player_strength * 1.5:
            strategy["priority_actions"] = [
                "Direct assault",
                "Overwhelm with numbers",
                "Cut off escape routes",
            ]
            strategy["tactical_decisions"].append("Aggressive push")
        elif ai_strength < player_strength * 0.7:
            strategy["priority_actions"] = [
                "Defensive positioning",
                "Call reinforcements",
                "Set traps",
            ]
            strategy["tactical_decisions"].append("Defensive stance")
        else:
            strategy["priority_actions"] = [
                "Tactical positioning",
                "Exploit weaknesses",
                "Coordinate attacks",
            ]
            strategy["tactical_decisions"].append("Balanced approach")

        # Resource allocation
        total_resources = sum(ai_resources.values())
        strategy["resource_allocation"] = {
            "offense": 0.4 * total_resources,
            "defense": 0.3 * total_resources,
            "support": 0.2 * total_resources,
            "reserve": 0.1 * total_resources,
        }

        return f"Optimized Strategy: {strategy}"


# Agent System Setup


async def create_game_ai_system(llm_provider) -> AgentMind:
    """Create the game AI development agent system"""

    mind = AgentMind(llm_provider=llm_provider)

    # Behavior Designer Agent
    behavior_designer = Agent(
        name="Behavior_Designer",
        role="behavior_design",
        system_prompt="""You are a game AI behavior designer. Your role is to:
        1. Design engaging AI behaviors
        2. Create behavior trees and state machines
        3. Ensure AI feels intelligent but fair
        4. Add personality to AI characters
        5. Balance challenge with fun

        Make AI that is challenging but not frustrating.""",
        tools=[BehaviorTreeGeneratorTool()],
    )

    # Difficulty Balancer Agent
    difficulty_balancer = Agent(
        name="Difficulty_Balancer",
        role="difficulty_balancing",
        system_prompt="""You are a game difficulty balancer. Your role is to:
        1. Analyze player performance data
        2. Adjust difficulty dynamically
        3. Maintain optimal challenge level
        4. Prevent frustration and boredom
        5. Create smooth difficulty curves

        Keep players in the flow state - challenged but not overwhelmed.""",
        tools=[DifficultyBalancerTool()],
    )

    # Player Analyst Agent
    player_analyst = Agent(
        name="Player_Analyst",
        role="player_analysis",
        system_prompt="""You are a player behavior analyst. Your role is to:
        1. Analyze player behavior patterns
        2. Identify play styles and preferences
        3. Detect skill levels
        4. Find pain points and frustrations
        5. Recommend personalized experiences

        Understand what makes each player tick.""",
        tools=[PlayerBehaviorAnalyzerTool()],
    )

    # Strategy Optimizer Agent
    strategy_optimizer = Agent(
        name="Strategy_Optimizer",
        role="strategy_optimization",
        system_prompt="""You are an AI strategy optimizer. Your role is to:
        1. Develop optimal AI strategies
        2. Adapt tactics to game situations
        3. Coordinate multiple AI agents
        4. Make strategic decisions
        5. Learn from player actions

        Create AI that thinks strategically and adapts.""",
        tools=[StrategyOptimizerTool()],
    )

    # AI Architect Agent
    ai_architect = Agent(
        name="AI_Architect",
        role="ai_architecture",
        system_prompt="""You are a game AI architect. Your role is to:
        1. Design overall AI system architecture
        2. Integrate different AI components
        3. Ensure performance and scalability
        4. Implement learning and adaptation
        5. Create cohesive AI experience

        Build AI systems that are robust, efficient, and engaging.""",
    )

    # Add all agents
    mind.add_agent(behavior_designer)
    mind.add_agent(difficulty_balancer)
    mind.add_agent(player_analyst)
    mind.add_agent(strategy_optimizer)
    mind.add_agent(ai_architect)

    return mind


async def design_game_ai(
    game_genre: GameGenre, game_description: str, llm_provider
) -> GameAIDesign:
    """Design complete game AI system"""

    print(f"\n{'=' * 60}")
    print("Designing Game AI")
    print(f"Genre: {game_genre.value}")
    print(f"{'=' * 60}\n")

    # Create the game AI system
    mind = await create_game_ai_system(llm_provider)

    # Format the design request
    design_request = """
Game AI Design Project:

Game Genre: {game_genre.value}
Game Description: {game_description}

Please design a comprehensive game AI system including:

1. AI BEHAVIOR DESIGN
   - Design behavior trees for different AI types
   - Create personality and decision - making patterns
   - Ensure variety and unpredictability

2. DIFFICULTY BALANCING
   - Design difficulty levels (Easy, Medium, Hard, Expert)
   - Create dynamic difficulty adjustment system
   - Balance challenge with accessibility

3. PLAYER ANALYSIS
   - Design player behavior tracking
   - Identify play styles and preferences
   - Personalize AI responses

4. STRATEGY OPTIMIZATION
   - Develop AI strategic thinking
   - Create tactical decision systems
   - Implement adaptive strategies

5. SYSTEM ARCHITECTURE
   - Design overall AI architecture
   - Ensure performance and scalability
   - Integrate all components

Provide a complete, implementable game AI design.
"""

    # Collaborate to design AI
    result = await mind.collaborate(task=design_request, max_rounds=5)

    print(f"\n{'=' * 60}")
    print("Game AI Design Complete")
    print(f"{'=' * 60}\n")
    print(result)

    # Create AI design
    design = GameAIDesign(
        game_genre=game_genre,
        ai_agents=[],
        behavior_trees={},
        difficulty_scaling={},
        balancing_parameters={},
        adaptive_features=[],
    )

    return design


# Example Game AI Projects


async def example_rpg_boss_ai():
    """Example: RPG boss AI"""

    game_description = """
    Fantasy RPG with boss battles. Need intelligent boss AI that:
    - Has multiple attack phases
    - Adapts to player strategy
    - Uses environment tactically
    - Provides fair but challenging fight
    - Has memorable attack patterns
    """

    llm = OllamaProvider(model="llama3.2")
    design = await design_game_ai(GameGenre.RPG, game_description, llm)
    return design


async def example_strategy_game_ai():
    """Example: Strategy game AI"""

    game_description = """
    Real - time strategy game. Need AI that:
    - Manages economy and resources
    - Builds bases strategically
    - Commands armies tactically
    - Adapts to player strategies
    - Provides different difficulty levels
    - Feels like playing against human
    """

    llm = OllamaProvider(model="llama3.2")
    design = await design_game_ai(GameGenre.STRATEGY, game_description, llm)
    return design


async def example_fps_enemy_ai():
    """Example: FPS enemy AI"""

    game_description = """
    First - person shooter. Need enemy AI that:
    - Uses cover intelligently
    - Flanks and coordinates with teammates
    - Varies tactics based on situation
    - Provides appropriate challenge
    - Feels realistic but not unfair
    - Has different enemy types with unique behaviors
    """

    llm = OllamaProvider(model="llama3.2")
    design = await design_game_ai(GameGenre.FPS, game_description, llm)
    return design


async def main():
    """Run example game AI designs"""

    print("Game AI Development System")
    print("=" * 60)

    # Example 1: RPG Boss AI
    print("\n\nExample 1: RPG Boss AI Design")
    await example_rpg_boss_ai()

    # Example 2: Strategy Game AI
    print("\n\nExample 2: Strategy Game AI Design")
    await example_strategy_game_ai()

    # Example 3: FPS Enemy AI
    print("\n\nExample 3: FPS Enemy AI Design")
    await example_fps_enemy_ai()


if __name__ == "__main__":
    asyncio.run(main())
