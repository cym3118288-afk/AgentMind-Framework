"""Template loader for creating agent teams from templates."""

from typing import Any, Dict, Optional

from ..core.agent import Agent
from ..core.mind import AgentMind
from ..llm.provider import LLMProvider
from .registry import TeamTemplate, get_registry


class TemplateLoader:
    """Loads and instantiates agent teams from templates.

    Example:
        >>> loader = TemplateLoader(llm_provider)
        >>> mind = loader.load("research")
        >>> result = await mind.collaborate("Research quantum computing")
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize the template loader.

        Args:
            llm_provider: Optional LLM provider for agents
        """
        self.llm_provider = llm_provider
        self.registry = get_registry()

    def load(
        self,
        template_name: str,
        llm_provider: Optional[LLMProvider] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
    ) -> AgentMind:
        """Load a team template and create an AgentMind instance.

        Args:
            template_name: Name of the template to load
            llm_provider: Optional LLM provider (overrides instance provider)
            config_overrides: Optional configuration overrides

        Returns:
            Configured AgentMind instance with agents

        Raises:
            ValueError: If template not found
        """
        template = self.registry.get(template_name)
        if not template:
            available = [t["name"] for t in self.registry.list_templates()]
            raise ValueError(
                f"Template '{template_name}' not found. Available: {', '.join(available)}"
            )

        provider = llm_provider or self.llm_provider
        mind = AgentMind(strategy=template.strategy, llm_provider=provider)

        # Create agents from template
        for agent_template in template.agents:
            config_dict = {
                "name": agent_template.name,
                "role": agent_template.role,
                "system_prompt": agent_template.system_prompt,
                "tools": agent_template.tools,
            }

            # Apply overrides
            if config_overrides and agent_template.name in config_overrides:
                config_dict.update(config_overrides[agent_template.name])

            agent = Agent(
                name=agent_template.name,
                role=agent_template.role,
                llm_provider=provider,
            )
            # Set system prompt
            if hasattr(agent.config, "system_prompt"):
                agent.config.system_prompt = agent_template.system_prompt

            mind.add_agent(agent)

        return mind

    def list_templates(self) -> list:
        """List all available templates.

        Returns:
            List of template information dictionaries
        """
        return self.registry.list_templates()

    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a template.

        Args:
            template_name: Name of the template

        Returns:
            Template information dictionary or None if not found
        """
        template = self.registry.get(template_name)
        if not template:
            return None

        return {
            "name": template.name,
            "description": template.description,
            "strategy": template.strategy.value,
            "agents": [
                {
                    "name": agent.name,
                    "role": agent.role,
                    "description": agent.description,
                    "tools": agent.tools,
                }
                for agent in template.agents
            ],
            "metadata": template.metadata,
        }


def load_template(
    template_name: str,
    llm_provider: Optional[LLMProvider] = None,
) -> AgentMind:
    """Convenience function to load a template.

    Args:
        template_name: Name of the template to load
        llm_provider: Optional LLM provider

    Returns:
        Configured AgentMind instance

    Example:
        >>> from agentmind.templates import load_template
        >>> mind = load_template("research", llm_provider)
        >>> result = await mind.collaborate("Research AI safety")
    """
    loader = TemplateLoader(llm_provider)
    return loader.load(template_name)
