"""Dynamic agent spawning based on task complexity."""

from typing import Any, Callable, Dict, List, Optional

from ..core.agent import Agent
from ..core.mind import AgentMind
from ..core.types import Message, MessageRole
from ..llm.provider import LLMProvider


class DynamicAgentSpawner:
    """Dynamically spawns agents based on task requirements.

    Analyzes tasks and creates specialized agents as needed.

    Example:
        >>> spawner = DynamicAgentSpawner(llm_provider)
        >>> agents = await spawner.spawn_for_task(
        ...     "Build a web application with authentication"
        ... )
    """

    def __init__(self, llm_provider: LLMProvider):
        """Initialize the dynamic spawner.

        Args:
            llm_provider: LLM provider for agent creation
        """
        self.llm_provider = llm_provider
        self.spawned_agents: List[Agent] = []
        self.spawn_history: List[Dict[str, Any]] = []

    async def spawn_for_task(
        self,
        task: str,
        max_agents: int = 5,
        existing_agents: Optional[List[Agent]] = None,
    ) -> List[Agent]:
        """Spawn agents appropriate for a task.

        Args:
            task: Task description
            max_agents: Maximum number of agents to spawn
            existing_agents: Optional list of existing agents to consider

        Returns:
            List of spawned agents
        """
        # Analyze task requirements
        requirements = await self._analyze_task(task)

        # Determine needed roles
        needed_roles = self._determine_roles(requirements, max_agents)

        # Check if existing agents can fulfill roles
        if existing_agents:
            needed_roles = self._filter_existing_roles(needed_roles, existing_agents)

        # Spawn new agents
        new_agents = []
        for role_spec in needed_roles:
            agent = self._create_agent(role_spec)
            new_agents.append(agent)
            self.spawned_agents.append(agent)

        # Record spawn event
        self.spawn_history.append({
            "task": task,
            "requirements": requirements,
            "spawned_count": len(new_agents),
            "roles": [a.role for a in new_agents],
        })

        return new_agents

    async def _analyze_task(self, task: str) -> Dict[str, Any]:
        """Analyze task to determine requirements.

        Args:
            task: Task description

        Returns:
            Dictionary with task requirements
        """
        analysis_prompt = f"""Analyze this task and identify requirements:

Task: {task}

Identify:
1. Domain (e.g., software, research, creative, business)
2. Complexity (low, medium, high)
3. Required skills (list 3-5 key skills)
4. Subtasks (list 2-4 main subtasks)

Format:
DOMAIN: [domain]
COMPLEXITY: [low/medium/high]
SKILLS: [skill1, skill2, skill3]
SUBTASKS: [subtask1, subtask2, subtask3]"""

        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="You are a task analysis expert.",
                sender="system",
            ),
            Message(
                role=MessageRole.USER,
                content=analysis_prompt,
                sender="spawner",
            ),
        ]

        response = await self.llm_provider.generate(messages)
        return self._parse_analysis(response.content)

    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse task analysis response.

        Args:
            response: Analysis response

        Returns:
            Parsed requirements
        """
        requirements = {
            "domain": "general",
            "complexity": "medium",
            "skills": [],
            "subtasks": [],
        }

        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("DOMAIN:"):
                requirements["domain"] = line.replace("DOMAIN:", "").strip()
            elif line.startswith("COMPLEXITY:"):
                requirements["complexity"] = line.replace("COMPLEXITY:", "").strip().lower()
            elif line.startswith("SKILLS:"):
                skills_text = line.replace("SKILLS:", "").strip()
                requirements["skills"] = [s.strip() for s in skills_text.split(",")]
            elif line.startswith("SUBTASKS:"):
                subtasks_text = line.replace("SUBTASKS:", "").strip()
                requirements["subtasks"] = [s.strip() for s in subtasks_text.split(",")]

        return requirements

    def _determine_roles(
        self,
        requirements: Dict[str, Any],
        max_agents: int,
    ) -> List[Dict[str, str]]:
        """Determine what agent roles are needed.

        Args:
            requirements: Task requirements
            max_agents: Maximum number of agents

        Returns:
            List of role specifications
        """
        complexity = requirements.get("complexity", "medium")
        skills = requirements.get("skills", [])

        # Base number of agents on complexity
        if complexity == "low":
            num_agents = min(2, max_agents)
        elif complexity == "high":
            num_agents = min(5, max_agents)
        else:
            num_agents = min(3, max_agents)

        # Create role specs based on skills
        roles = []
        role_templates = {
            "research": "You are a researcher who gathers and analyzes information.",
            "design": "You are a designer who creates plans and architectures.",
            "implementation": "You are an implementer who executes plans and builds solutions.",
            "review": "You are a reviewer who evaluates quality and identifies improvements.",
            "coordination": "You are a coordinator who manages workflow and integration.",
        }

        # Map skills to roles
        skill_to_role = {
            "research": "research",
            "analysis": "research",
            "design": "design",
            "architecture": "design",
            "coding": "implementation",
            "development": "implementation",
            "testing": "review",
            "review": "review",
        }

        assigned_roles = set()
        for skill in skills[:num_agents]:
            role = skill_to_role.get(skill.lower(), "implementation")
            if role not in assigned_roles:
                roles.append({
                    "name": f"{role}_{len(roles)+1}",
                    "role": role,
                    "system_prompt": role_templates.get(role, "You are a helpful assistant."),
                })
                assigned_roles.add(role)

        # Ensure minimum roles
        if not roles:
            roles.append({
                "name": "agent_1",
                "role": "assistant",
                "system_prompt": "You are a helpful assistant.",
            })

        return roles[:max_agents]

    def _filter_existing_roles(
        self,
        needed_roles: List[Dict[str, str]],
        existing_agents: List[Agent],
    ) -> List[Dict[str, str]]:
        """Filter out roles already covered by existing agents.

        Args:
            needed_roles: List of needed role specs
            existing_agents: List of existing agents

        Returns:
            Filtered list of role specs
        """
        existing_roles = {agent.role for agent in existing_agents}
        return [
            role_spec for role_spec in needed_roles
            if role_spec["role"] not in existing_roles
        ]

    def _create_agent(self, role_spec: Dict[str, str]) -> Agent:
        """Create an agent from a role specification.

        Args:
            role_spec: Role specification

        Returns:
            Created agent
        """
        agent = Agent(
            name=role_spec["name"],
            role=role_spec["role"],
            llm_provider=self.llm_provider,
        )

        # Set system prompt if config supports it
        if hasattr(agent.config, "system_prompt"):
            agent.config.system_prompt = role_spec["system_prompt"]

        return agent

    async def spawn_on_demand(
        self,
        mind: AgentMind,
        task: str,
        trigger_condition: Optional[Callable] = None,
    ) -> List[Agent]:
        """Spawn agents on-demand and add to AgentMind.

        Args:
            mind: AgentMind instance to add agents to
            task: Task description
            trigger_condition: Optional condition to check before spawning

        Returns:
            List of spawned agents
        """
        # Check trigger condition
        if trigger_condition and not trigger_condition():
            return []

        # Spawn agents
        new_agents = await self.spawn_for_task(task, existing_agents=mind.agents)

        # Add to mind
        for agent in new_agents:
            mind.add_agent(agent)

        return new_agents

    def get_spawn_history(self) -> List[Dict[str, Any]]:
        """Get history of agent spawning.

        Returns:
            List of spawn events
        """
        return self.spawn_history

    def cleanup_agents(self, mind: AgentMind) -> int:
        """Remove spawned agents from AgentMind.

        Args:
            mind: AgentMind instance

        Returns:
            Number of agents removed
        """
        removed = 0
        for agent in self.spawned_agents:
            if mind.remove_agent(agent.name):
                removed += 1

        self.spawned_agents = []
        return removed
