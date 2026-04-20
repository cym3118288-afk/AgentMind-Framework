"""Tests for template system."""

import pytest
from agentmind.templates import TemplateLoader, TemplateRegistry, load_template, get_registry
from agentmind.templates.registry import AgentTemplate, TeamTemplate
from agentmind.core import CollaborationStrategy
from agentmind.llm import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, model="mock-model", **kwargs):
        super().__init__(model, **kwargs)

    async def generate(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock response."""
        return LLMResponse(
            content="Mock response", model=self.model, usage={"total_tokens": 10}, metadata={}
        )

    async def generate_stream(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock streaming response."""
        yield "Mock stream"


class TestTemplateRegistry:
    """Tests for TemplateRegistry."""

    def test_registry_initialization(self):
        """Test that registry initializes with built-in templates."""
        registry = TemplateRegistry()
        templates = registry.list_templates()

        assert len(templates) >= 20  # Should have 20+ built-in templates

    def test_get_template(self):
        """Test getting a template by name."""
        registry = TemplateRegistry()

        template = registry.get("research")
        assert template is not None
        assert template.name == "research"
        assert len(template.agents) == 3

    def test_get_nonexistent_template(self):
        """Test getting a template that doesn't exist."""
        registry = TemplateRegistry()

        template = registry.get("nonexistent")
        assert template is None

    def test_register_custom_template(self):
        """Test registering a custom template."""
        registry = TemplateRegistry()

        custom_template = TeamTemplate(
            name="custom",
            description="Custom team",
            agents=[
                AgentTemplate(
                    name="agent1", role="role1", system_prompt="Prompt 1", description="Agent 1"
                )
            ],
        )

        registry.register(custom_template)
        retrieved = registry.get("custom")

        assert retrieved is not None
        assert retrieved.name == "custom"

    def test_list_templates(self):
        """Test listing all templates."""
        registry = TemplateRegistry()
        templates = registry.list_templates()

        assert isinstance(templates, list)
        assert all("name" in t for t in templates)
        assert all("description" in t for t in templates)
        assert all("agents" in t for t in templates)

    def test_builtin_templates_exist(self):
        """Test that all expected built-in templates exist."""
        registry = TemplateRegistry()

        expected_templates = [
            "research",
            "code-generation",
            "startup-validator",
            "content-creation",
            "data-analysis",
            "customer-support",
            "product-design",
            "marketing-campaign",
            "legal-review",
            "education",
            "crisis-management",
            "scientific-research",
            "investment-analysis",
            "game-development",
            "healthcare-consultation",
            "debate",
            "translation",
            "security-audit",
            "creative-writing",
            "devops",
        ]

        for template_name in expected_templates:
            template = registry.get(template_name)
            assert template is not None, f"Template '{template_name}' not found"


class TestTemplateLoader:
    """Tests for TemplateLoader."""

    def test_loader_initialization(self):
        """Test loader initialization."""
        provider = MockLLMProvider()
        loader = TemplateLoader(llm_provider=provider)

        assert loader.llm_provider is provider
        assert loader.registry is not None

    def test_load_template(self):
        """Test loading a template."""
        provider = MockLLMProvider()
        loader = TemplateLoader(llm_provider=provider)

        mind = loader.load("research")

        assert mind is not None
        assert len(mind.agents) == 3

    def test_load_nonexistent_template(self):
        """Test loading a template that doesn't exist."""
        provider = MockLLMProvider()
        loader = TemplateLoader(llm_provider=provider)

        with pytest.raises(ValueError) as exc_info:
            loader.load("nonexistent")

        assert "not found" in str(exc_info.value).lower()

    def test_load_with_provider_override(self):
        """Test loading with provider override."""
        provider1 = MockLLMProvider(model="model1")
        provider2 = MockLLMProvider(model="model2")

        loader = TemplateLoader(llm_provider=provider1)
        mind = loader.load("research", llm_provider=provider2)

        # Should use provider2
        assert mind.llm_provider is provider2

    def test_list_templates(self):
        """Test listing templates through loader."""
        loader = TemplateLoader()
        templates = loader.list_templates()

        assert len(templates) >= 20

    def test_get_template_info(self):
        """Test getting template info."""
        loader = TemplateLoader()
        info = loader.get_template_info("research")

        assert info is not None
        assert info["name"] == "research"
        assert "description" in info
        assert "agents" in info
        assert len(info["agents"]) == 3

    def test_get_nonexistent_template_info(self):
        """Test getting info for nonexistent template."""
        loader = TemplateLoader()
        info = loader.get_template_info("nonexistent")

        assert info is None


class TestTemplateConvenienceFunction:
    """Tests for load_template convenience function."""

    def test_load_template_function(self):
        """Test load_template convenience function."""
        provider = MockLLMProvider()
        mind = load_template("research", llm_provider=provider)

        assert mind is not None
        assert len(mind.agents) == 3


class TestSpecificTemplates:
    """Test specific template configurations."""

    def test_research_template(self):
        """Test research template configuration."""
        registry = TemplateRegistry()
        template = registry.get("research")

        assert template.name == "research"
        assert len(template.agents) == 3
        assert template.strategy == CollaborationStrategy.ROUND_ROBIN

        agent_names = [a.name for a in template.agents]
        assert "researcher" in agent_names
        assert "analyst" in agent_names
        assert "synthesizer" in agent_names

    def test_code_generation_template(self):
        """Test code generation template configuration."""
        registry = TemplateRegistry()
        template = registry.get("code-generation")

        assert template.name == "code-generation"
        assert len(template.agents) == 3

        agent_names = [a.name for a in template.agents]
        assert "architect" in agent_names
        assert "coder" in agent_names
        assert "reviewer" in agent_names

    def test_startup_validator_template(self):
        """Test startup validator template configuration."""
        registry = TemplateRegistry()
        template = registry.get("startup-validator")

        assert template.name == "startup-validator"
        assert len(template.agents) == 3
        assert template.strategy == CollaborationStrategy.BROADCAST

    def test_debate_template(self):
        """Test debate template configuration."""
        registry = TemplateRegistry()
        template = registry.get("debate")

        assert template.name == "debate"
        assert len(template.agents) == 3

        agent_names = [a.name for a in template.agents]
        assert "proposition" in agent_names
        assert "opposition" in agent_names
        assert "judge" in agent_names


class TestTemplateAgentConfiguration:
    """Test agent configuration in templates."""

    def test_agent_template_fields(self):
        """Test that agent templates have all required fields."""
        registry = TemplateRegistry()
        template = registry.get("research")

        for agent in template.agents:
            assert agent.name is not None
            assert agent.role is not None
            assert agent.system_prompt is not None
            assert agent.description is not None
            assert isinstance(agent.tools, list)

    def test_agent_system_prompts(self):
        """Test that agents have meaningful system prompts."""
        registry = TemplateRegistry()
        template = registry.get("research")

        for agent in template.agents:
            assert len(agent.system_prompt) > 20
            assert "you" in agent.system_prompt.lower()


class TestTemplateEdgeCases:
    """Test edge cases in template system."""

    def test_empty_template_name(self):
        """Test loading with empty template name."""
        loader = TemplateLoader()

        with pytest.raises(ValueError):
            loader.load("")

    def test_template_with_no_agents(self):
        """Test template with no agents."""
        registry = TemplateRegistry()

        empty_template = TeamTemplate(name="empty", description="Empty team", agents=[])

        registry.register(empty_template)
        template = registry.get("empty")

        assert len(template.agents) == 0

    def test_global_registry_singleton(self):
        """Test that get_registry returns same instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2


class TestTemplatePerformance:
    """Test template system performance."""

    def test_load_all_templates(self):
        """Test loading all built-in templates."""
        provider = MockLLMProvider()
        loader = TemplateLoader(llm_provider=provider)

        templates = loader.list_templates()

        for template_info in templates:
            mind = loader.load(template_info["name"])
            assert mind is not None
            assert len(mind.agents) > 0

    def test_template_lookup_performance(self):
        """Test template lookup is fast."""
        import time

        registry = TemplateRegistry()

        start = time.time()
        for _ in range(1000):
            template = registry.get("research")
            assert template is not None
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should be very fast


class TestTemplateStrategies:
    """Test different collaboration strategies in templates."""

    def test_sequential_strategy_templates(self):
        """Test templates using round-robin strategy (sequential execution)."""
        registry = TemplateRegistry()

        sequential_templates = [
            "research",
            "code-generation",
            "content-creation",
            "data-analysis",
            "product-design",
            "marketing-campaign",
        ]

        for template_name in sequential_templates:
            template = registry.get(template_name)
            assert template.strategy == CollaborationStrategy.ROUND_ROBIN

    def test_broadcast_strategy_templates(self):
        """Test templates using broadcast strategy."""
        registry = TemplateRegistry()

        broadcast_templates = [
            "startup-validator",
            "legal-review",
            "investment-analysis",
            "security-audit",
        ]

        for template_name in broadcast_templates:
            template = registry.get(template_name)
            assert template.strategy == CollaborationStrategy.BROADCAST

    def test_hierarchical_strategy_templates(self):
        """Test templates using hierarchical strategy."""
        registry = TemplateRegistry()

        hierarchical_templates = ["customer-support", "crisis-management"]

        for template_name in hierarchical_templates:
            template = registry.get(template_name)
            assert template.strategy == CollaborationStrategy.HIERARCHICAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
