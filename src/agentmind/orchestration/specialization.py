"""Agent specialization and skill matching."""

from typing import Any, Dict, List, Optional, Set

from ..core.agent import Agent


class AgentSkill:
    """Represents a skill that an agent possesses."""

    def __init__(
        self,
        name: str,
        proficiency: float = 0.5,
        description: str = "",
    ):
        """Initialize a skill.

        Args:
            name: Skill name
            proficiency: Proficiency level (0.0 to 1.0)
            description: Skill description
        """
        self.name = name
        self.proficiency = max(0.0, min(1.0, proficiency))
        self.description = description


class SpecializationEngine:
    """Manages agent specialization and skill development.

    Tracks agent skills and helps agents specialize over time.

    Example:
        >>> engine = SpecializationEngine()
        >>> engine.add_agent_skill(agent, "python", 0.8)
        >>> engine.improve_skill(agent, "python", 0.1)
    """

    def __init__(self):
        """Initialize the specialization engine."""
        self.agent_skills: Dict[str, List[AgentSkill]] = {}

    def add_agent_skill(
        self,
        agent: Agent,
        skill_name: str,
        proficiency: float = 0.5,
        description: str = "",
    ) -> None:
        """Add a skill to an agent.

        Args:
            agent: Agent to add skill to
            skill_name: Name of the skill
            proficiency: Initial proficiency level
            description: Skill description
        """
        if agent.name not in self.agent_skills:
            self.agent_skills[agent.name] = []

        skill = AgentSkill(skill_name, proficiency, description)
        self.agent_skills[agent.name].append(skill)

    def get_agent_skills(self, agent: Agent) -> List[AgentSkill]:
        """Get all skills for an agent.

        Args:
            agent: Agent to get skills for

        Returns:
            List of agent skills
        """
        return self.agent_skills.get(agent.name, [])

    def improve_skill(
        self,
        agent: Agent,
        skill_name: str,
        improvement: float = 0.1,
    ) -> bool:
        """Improve an agent's skill proficiency.

        Args:
            agent: Agent to improve
            skill_name: Name of skill to improve
            improvement: Amount to improve (0.0 to 1.0)

        Returns:
            True if skill was improved, False if not found
        """
        skills = self.agent_skills.get(agent.name, [])

        for skill in skills:
            if skill.name == skill_name:
                skill.proficiency = min(1.0, skill.proficiency + improvement)
                return True

        return False

    def get_skill_proficiency(self, agent: Agent, skill_name: str) -> Optional[float]:
        """Get an agent's proficiency in a skill.

        Args:
            agent: Agent to check
            skill_name: Name of skill

        Returns:
            Proficiency level or None if skill not found
        """
        skills = self.agent_skills.get(agent.name, [])

        for skill in skills:
            if skill.name == skill_name:
                return skill.proficiency

        return None

    def get_specialization_summary(self, agent: Agent) -> Dict[str, Any]:
        """Get a summary of an agent's specialization.

        Args:
            agent: Agent to summarize

        Returns:
            Dictionary with specialization info
        """
        skills = self.get_agent_skills(agent)

        if not skills:
            return {"agent": agent.name, "skills": [], "specialization": "generalist"}

        # Find primary specialization (highest proficiency)
        primary_skill = max(skills, key=lambda s: s.proficiency)

        return {
            "agent": agent.name,
            "skills": [
                {"name": s.name, "proficiency": s.proficiency}
                for s in skills
            ],
            "specialization": primary_skill.name,
            "primary_proficiency": primary_skill.proficiency,
        }


class SkillMatcher:
    """Matches tasks to agents based on required skills.

    Example:
        >>> matcher = SkillMatcher(specialization_engine)
        >>> best_agent = matcher.find_best_agent(
        ...     agents, ["python", "testing"]
        ... )
    """

    def __init__(self, specialization_engine: SpecializationEngine):
        """Initialize the skill matcher.

        Args:
            specialization_engine: Engine managing agent skills
        """
        self.engine = specialization_engine

    def find_best_agent(
        self,
        agents: List[Agent],
        required_skills: List[str],
        min_proficiency: float = 0.5,
    ) -> Optional[Agent]:
        """Find the best agent for required skills.

        Args:
            agents: List of candidate agents
            required_skills: List of required skill names
            min_proficiency: Minimum acceptable proficiency

        Returns:
            Best matching agent or None
        """
        best_agent = None
        best_score = -1.0

        for agent in agents:
            score = self._calculate_match_score(agent, required_skills, min_proficiency)
            if score > best_score:
                best_score = score
                best_agent = agent

        return best_agent if best_score >= 0 else None

    def _calculate_match_score(
        self,
        agent: Agent,
        required_skills: List[str],
        min_proficiency: float,
    ) -> float:
        """Calculate how well an agent matches required skills.

        Args:
            agent: Agent to evaluate
            required_skills: Required skills
            min_proficiency: Minimum proficiency threshold

        Returns:
            Match score (higher is better, -1 if doesn't meet minimum)
        """
        if not required_skills:
            return 0.0

        total_proficiency = 0.0
        matched_skills = 0

        for skill_name in required_skills:
            proficiency = self.engine.get_skill_proficiency(agent, skill_name)

            if proficiency is None:
                continue

            if proficiency < min_proficiency:
                return -1.0  # Doesn't meet minimum

            total_proficiency += proficiency
            matched_skills += 1

        if matched_skills == 0:
            return -1.0

        # Average proficiency across matched skills
        return total_proficiency / len(required_skills)

    def match_agents_to_tasks(
        self,
        agents: List[Agent],
        tasks: List[Dict[str, Any]],
    ) -> Dict[str, Optional[Agent]]:
        """Match multiple tasks to best agents.

        Args:
            agents: List of available agents
            tasks: List of task specifications with 'required_skills'

        Returns:
            Dictionary mapping task descriptions to assigned agents
        """
        assignments = {}

        for task in tasks:
            task_desc = task.get("description", "")
            required_skills = task.get("required_skills", [])

            best_agent = self.find_best_agent(agents, required_skills)
            assignments[task_desc] = best_agent

        return assignments

    def get_skill_coverage(
        self,
        agents: List[Agent],
        required_skills: List[str],
    ) -> Dict[str, Any]:
        """Analyze skill coverage across agents.

        Args:
            agents: List of agents
            required_skills: List of required skills

        Returns:
            Dictionary with coverage analysis
        """
        coverage = {}

        for skill in required_skills:
            agents_with_skill = []

            for agent in agents:
                proficiency = self.engine.get_skill_proficiency(agent, skill)
                if proficiency is not None and proficiency > 0:
                    agents_with_skill.append({
                        "agent": agent.name,
                        "proficiency": proficiency,
                    })

            coverage[skill] = {
                "covered": len(agents_with_skill) > 0,
                "agents": agents_with_skill,
                "max_proficiency": max(
                    (a["proficiency"] for a in agents_with_skill),
                    default=0.0,
                ),
            }

        return coverage

    def recommend_training(
        self,
        agents: List[Agent],
        required_skills: List[str],
    ) -> List[Dict[str, Any]]:
        """Recommend skill training for agents.

        Args:
            agents: List of agents
            required_skills: List of required skills

        Returns:
            List of training recommendations
        """
        recommendations = []
        coverage = self.get_skill_coverage(agents, required_skills)

        for skill, info in coverage.items():
            if not info["covered"]:
                recommendations.append({
                    "skill": skill,
                    "priority": "high",
                    "reason": "No agents have this skill",
                    "suggested_agents": [a.name for a in agents[:2]],
                })
            elif info["max_proficiency"] < 0.7:
                recommendations.append({
                    "skill": skill,
                    "priority": "medium",
                    "reason": f"Low proficiency (max: {info['max_proficiency']:.2f})",
                    "suggested_agents": [a["agent"] for a in info["agents"]],
                })

        return recommendations
