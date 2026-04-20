"""Template registry for managing agent team templates."""

from typing import Any, Dict, List, Optional

from ..core.types import CollaborationStrategy


class AgentTemplate:
    """Template for creating a pre-configured agent."""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        description: str,
        tools: Optional[List[str]] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.description = description
        self.tools = tools or []
        self.config_overrides = config_overrides or {}


class TeamTemplate:
    """Template for creating a pre-configured agent team."""

    def __init__(
        self,
        name: str,
        description: str,
        agents: List[AgentTemplate],
        strategy: CollaborationStrategy = CollaborationStrategy.BROADCAST,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.agents = agents
        self.strategy = strategy
        self.metadata = metadata or {}


class TemplateRegistry:
    """Registry for agent and team templates."""

    def __init__(self):
        self.templates: Dict[str, TeamTemplate] = {}
        self._register_builtin_templates()

    def register(self, template: TeamTemplate) -> None:
        """Register a new team template.

        Args:
            template: The team template to register
        """
        self.templates[template.name] = template

    def get(self, name: str) -> Optional[TeamTemplate]:
        """Get a template by name.

        Args:
            name: Template name

        Returns:
            TeamTemplate if found, None otherwise
        """
        return self.templates.get(name)

    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates.

        Returns:
            List of template info dictionaries
        """
        return [
            {
                "name": name,
                "description": template.description,
                "agents": len(template.agents),
                "strategy": template.strategy.value,
            }
            for name, template in self.templates.items()
        ]

    def _register_builtin_templates(self) -> None:
        """Register all built-in templates."""

        # 1. Research Team
        self.register(
            TeamTemplate(
                name="research",
                description="Deep research team with researcher, analyst, and synthesizer",
                agents=[
                    AgentTemplate(
                        name="researcher",
                        role="researcher",
                        system_prompt=(
                            "You are a thorough researcher who finds "
                            "accurate information from multiple sources. "
                            "Focus on facts, data, and credible sources."
                        ),
                        description="Finds and gathers information",
                    ),
                    AgentTemplate(
                        name="analyst",
                        role="analyst",
                        system_prompt=(
                            "You are a critical analyst who evaluates "
                            "information quality, identifies patterns, and "
                            "assesses credibility. Be skeptical and thorough."
                        ),
                        description="Analyzes and validates information",
                    ),
                    AgentTemplate(
                        name="synthesizer",
                        role="synthesizer",
                        system_prompt=(
                            "You are a synthesizer who combines insights from "
                            "multiple sources into coherent, well-structured "
                            "reports. Focus on clarity and actionability."
                        ),
                        description="Synthesizes findings into reports",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 2. Code Generation Team
        self.register(
            TeamTemplate(
                name="code-generation",
                description="Software development team with architect, coder, and reviewer",
                agents=[
                    AgentTemplate(
                        name="architect",
                        role="architect",
                        system_prompt=(
                            "You are a software architect who designs clean, "
                            "scalable solutions. Focus on architecture, "
                            "patterns, and best practices."
                        ),
                        description="Designs software architecture",
                    ),
                    AgentTemplate(
                        name="coder",
                        role="coder",
                        system_prompt=(
                            "You are an expert programmer who writes clean, "
                            "efficient, well-documented code. Follow best "
                            "practices and write tests."
                        ),
                        description="Implements the code",
                    ),
                    AgentTemplate(
                        name="reviewer",
                        role="reviewer",
                        system_prompt=(
                            "You are a code reviewer who checks for bugs, "
                            "security issues, performance problems, and code "
                            "quality. Be thorough and constructive."
                        ),
                        description="Reviews and improves code",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 3. Startup Idea Validator
        self.register(
            TeamTemplate(
                name="startup-validator",
                description="Validates startup ideas from market, technical, and financial perspectives",
                agents=[
                    AgentTemplate(
                        name="market_analyst",
                        role="analyst",
                        system_prompt="You analyze market opportunities, competition, and customer needs. Focus on market size, trends, and competitive advantages.",
                        description="Analyzes market viability",
                    ),
                    AgentTemplate(
                        name="tech_evaluator",
                        role="evaluator",
                        system_prompt="You evaluate technical feasibility, scalability, and implementation challenges. Focus on technology stack, architecture, and risks.",
                        description="Evaluates technical feasibility",
                    ),
                    AgentTemplate(
                        name="financial_advisor",
                        role="advisor",
                        system_prompt="You assess financial viability, funding needs, and revenue models. Focus on costs, pricing, and path to profitability.",
                        description="Assesses financial viability",
                    ),
                ],
                strategy=CollaborationStrategy.BROADCAST,
            )
        )

        # 4. Content Creation Team
        self.register(
            TeamTemplate(
                name="content-creation",
                description="Creates high-quality content with writer, editor, and SEO specialist",
                agents=[
                    AgentTemplate(
                        name="writer",
                        role="writer",
                        system_prompt="You are a creative writer who crafts engaging, informative content. Focus on storytelling, clarity, and audience engagement.",
                        description="Writes initial content",
                    ),
                    AgentTemplate(
                        name="editor",
                        role="editor",
                        system_prompt="You are an editor who improves clarity, structure, and flow. Fix grammar, enhance readability, and ensure consistency.",
                        description="Edits and refines content",
                    ),
                    AgentTemplate(
                        name="seo_specialist",
                        role="specialist",
                        system_prompt="You optimize content for search engines while maintaining quality. Focus on keywords, meta descriptions, and readability.",
                        description="Optimizes for SEO",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 5. Data Analysis Team
        self.register(
            TeamTemplate(
                name="data-analysis",
                description="Analyzes data with statistician, visualizer, and interpreter",
                agents=[
                    AgentTemplate(
                        name="statistician",
                        role="analyst",
                        system_prompt="You are a statistician who analyzes data using statistical methods. Focus on patterns, correlations, and significance.",
                        description="Performs statistical analysis",
                    ),
                    AgentTemplate(
                        name="visualizer",
                        role="visualizer",
                        system_prompt="You create clear, informative data visualizations. Focus on choosing the right chart types and making data accessible.",
                        description="Creates visualizations",
                    ),
                    AgentTemplate(
                        name="interpreter",
                        role="interpreter",
                        system_prompt="You interpret data findings for non-technical audiences. Focus on insights, implications, and actionable recommendations.",
                        description="Interprets findings",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 6. Customer Support Team
        self.register(
            TeamTemplate(
                name="customer-support",
                description="Handles customer inquiries with support agent, technical expert, and escalation handler",
                agents=[
                    AgentTemplate(
                        name="support_agent",
                        role="support",
                        system_prompt="You are a friendly customer support agent who helps users with their questions. Be empathetic, clear, and solution-oriented.",
                        description="Handles general inquiries",
                    ),
                    AgentTemplate(
                        name="technical_expert",
                        role="expert",
                        system_prompt="You are a technical expert who solves complex technical issues. Provide detailed, accurate solutions with step-by-step guidance.",
                        description="Handles technical issues",
                    ),
                    AgentTemplate(
                        name="escalation_handler",
                        role="handler",
                        system_prompt="You handle escalated issues and complaints. Be diplomatic, find solutions, and ensure customer satisfaction.",
                        description="Manages escalations",
                    ),
                ],
                strategy=CollaborationStrategy.HIERARCHICAL,
            )
        )

        # 7. Product Design Team
        self.register(
            TeamTemplate(
                name="product-design",
                description="Designs products with UX researcher, designer, and prototyper",
                agents=[
                    AgentTemplate(
                        name="ux_researcher",
                        role="researcher",
                        system_prompt="You research user needs, behaviors, and pain points. Focus on user interviews, surveys, and usability insights.",
                        description="Researches user needs",
                    ),
                    AgentTemplate(
                        name="designer",
                        role="designer",
                        system_prompt="You design intuitive, beautiful user interfaces. Focus on usability, accessibility, and visual hierarchy.",
                        description="Designs interfaces",
                    ),
                    AgentTemplate(
                        name="prototyper",
                        role="prototyper",
                        system_prompt="You create interactive prototypes to test designs. Focus on functionality, user flows, and feedback collection.",
                        description="Creates prototypes",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 8. Marketing Campaign Team
        self.register(
            TeamTemplate(
                name="marketing-campaign",
                description="Plans and executes marketing campaigns",
                agents=[
                    AgentTemplate(
                        name="strategist",
                        role="strategist",
                        system_prompt="You develop marketing strategies and campaign plans. Focus on target audience, messaging, and channels.",
                        description="Develops strategy",
                    ),
                    AgentTemplate(
                        name="copywriter",
                        role="writer",
                        system_prompt="You write compelling marketing copy that converts. Focus on benefits, emotional appeal, and clear CTAs.",
                        description="Writes marketing copy",
                    ),
                    AgentTemplate(
                        name="performance_analyst",
                        role="analyst",
                        system_prompt="You analyze campaign performance and optimize for better results. Focus on metrics, A/B testing, and ROI.",
                        description="Analyzes performance",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 9. Legal Review Team
        self.register(
            TeamTemplate(
                name="legal-review",
                description="Reviews documents from legal, compliance, and risk perspectives",
                agents=[
                    AgentTemplate(
                        name="legal_analyst",
                        role="analyst",
                        system_prompt="You review documents for legal issues and compliance. Focus on contracts, terms, and regulatory requirements.",
                        description="Reviews legal aspects",
                    ),
                    AgentTemplate(
                        name="compliance_officer",
                        role="officer",
                        system_prompt="You ensure compliance with regulations and standards. Focus on industry-specific requirements and best practices.",
                        description="Checks compliance",
                    ),
                    AgentTemplate(
                        name="risk_assessor",
                        role="assessor",
                        system_prompt="You identify and assess legal and business risks. Focus on potential liabilities and mitigation strategies.",
                        description="Assesses risks",
                    ),
                ],
                strategy=CollaborationStrategy.BROADCAST,
            )
        )

        # 10. Education Team
        self.register(
            TeamTemplate(
                name="education",
                description="Creates educational content with instructor, curriculum designer, and assessor",
                agents=[
                    AgentTemplate(
                        name="instructor",
                        role="instructor",
                        system_prompt="You teach concepts clearly and engagingly. Focus on explanations, examples, and student understanding.",
                        description="Teaches concepts",
                    ),
                    AgentTemplate(
                        name="curriculum_designer",
                        role="designer",
                        system_prompt="You design effective learning paths and curricula. Focus on learning objectives, progression, and engagement.",
                        description="Designs curriculum",
                    ),
                    AgentTemplate(
                        name="assessor",
                        role="assessor",
                        system_prompt="You create assessments and evaluate learning. Focus on fair, comprehensive evaluation of understanding.",
                        description="Creates assessments",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # Additional templates (11-20)
        self._register_additional_templates()

    def _register_additional_templates(self) -> None:
        """Register additional built-in templates."""

        # 11. Crisis Management
        self.register(
            TeamTemplate(
                name="crisis-management",
                description="Handles crises with coordinator, communicator, and resolver",
                agents=[
                    AgentTemplate(
                        name="coordinator",
                        role="coordinator",
                        system_prompt="You coordinate crisis response efforts. Focus on prioritization, resource allocation, and team coordination.",
                        description="Coordinates response",
                    ),
                    AgentTemplate(
                        name="communicator",
                        role="communicator",
                        system_prompt="You manage crisis communications. Focus on transparency, timeliness, and stakeholder management.",
                        description="Manages communications",
                    ),
                    AgentTemplate(
                        name="resolver",
                        role="resolver",
                        system_prompt="You solve the underlying crisis issues. Focus on root causes, solutions, and prevention.",
                        description="Resolves issues",
                    ),
                ],
                strategy=CollaborationStrategy.HIERARCHICAL,
            )
        )

        # 12. Scientific Research
        self.register(
            TeamTemplate(
                name="scientific-research",
                description="Conducts scientific research with hypothesis generator, experimenter, and peer reviewer",
                agents=[
                    AgentTemplate(
                        name="hypothesis_generator",
                        role="researcher",
                        system_prompt="You generate scientific hypotheses based on existing research. Focus on novelty, testability, and significance.",
                        description="Generates hypotheses",
                    ),
                    AgentTemplate(
                        name="experimenter",
                        role="experimenter",
                        system_prompt="You design and analyze experiments. Focus on methodology, controls, and statistical validity.",
                        description="Designs experiments",
                    ),
                    AgentTemplate(
                        name="peer_reviewer",
                        role="reviewer",
                        system_prompt="You critically review research for validity and rigor. Focus on methodology, conclusions, and reproducibility.",
                        description="Reviews research",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 13. Investment Analysis
        self.register(
            TeamTemplate(
                name="investment-analysis",
                description="Analyzes investments with fundamental analyst, technical analyst, and risk manager",
                agents=[
                    AgentTemplate(
                        name="fundamental_analyst",
                        role="analyst",
                        system_prompt="You analyze company fundamentals and intrinsic value. Focus on financials, competitive position, and growth prospects.",
                        description="Analyzes fundamentals",
                    ),
                    AgentTemplate(
                        name="technical_analyst",
                        role="analyst",
                        system_prompt="You analyze price patterns and market trends. Focus on charts, indicators, and market sentiment.",
                        description="Analyzes technicals",
                    ),
                    AgentTemplate(
                        name="risk_manager",
                        role="manager",
                        system_prompt="You assess investment risks and portfolio balance. Focus on diversification, downside protection, and risk-adjusted returns.",
                        description="Manages risk",
                    ),
                ],
                strategy=CollaborationStrategy.BROADCAST,
            )
        )

        # 14. Game Development
        self.register(
            TeamTemplate(
                name="game-development",
                description="Develops games with designer, programmer, and playtester",
                agents=[
                    AgentTemplate(
                        name="game_designer",
                        role="designer",
                        system_prompt="You design game mechanics, levels, and player experiences. Focus on fun, balance, and engagement.",
                        description="Designs game mechanics",
                    ),
                    AgentTemplate(
                        name="game_programmer",
                        role="programmer",
                        system_prompt="You implement game systems and features. Focus on performance, maintainability, and game feel.",
                        description="Implements game code",
                    ),
                    AgentTemplate(
                        name="playtester",
                        role="tester",
                        system_prompt="You test games for bugs, balance, and fun. Focus on player experience, difficulty curve, and issues.",
                        description="Tests gameplay",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 15. Healthcare Consultation
        self.register(
            TeamTemplate(
                name="healthcare-consultation",
                description="Provides healthcare insights with diagnostician, treatment planner, and wellness advisor",
                agents=[
                    AgentTemplate(
                        name="diagnostician",
                        role="diagnostician",
                        system_prompt="You analyze symptoms and suggest possible diagnoses. Focus on differential diagnosis and evidence-based medicine. Always recommend consulting real healthcare professionals.",
                        description="Analyzes symptoms",
                    ),
                    AgentTemplate(
                        name="treatment_planner",
                        role="planner",
                        system_prompt="You suggest treatment options and care plans. Focus on evidence-based treatments and patient-centered care. Always recommend consulting real healthcare professionals.",
                        description="Plans treatment",
                    ),
                    AgentTemplate(
                        name="wellness_advisor",
                        role="advisor",
                        system_prompt="You provide wellness and prevention advice. Focus on lifestyle, nutrition, and preventive care.",
                        description="Advises on wellness",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 16-20: More specialized templates
        self._register_specialized_templates()

    def _register_specialized_templates(self) -> None:
        """Register specialized templates."""

        # 16. Debate Team
        self.register(
            TeamTemplate(
                name="debate",
                description="Structured debate with proposition, opposition, and judge",
                agents=[
                    AgentTemplate(
                        name="proposition",
                        role="debater",
                        system_prompt="You argue for the proposition. Build strong arguments with evidence and logic.",
                        description="Argues for the motion",
                    ),
                    AgentTemplate(
                        name="opposition",
                        role="debater",
                        system_prompt="You argue against the proposition. Counter arguments with evidence and identify weaknesses.",
                        description="Argues against the motion",
                    ),
                    AgentTemplate(
                        name="judge",
                        role="judge",
                        system_prompt="You evaluate debate arguments objectively. Focus on logic, evidence, and persuasiveness.",
                        description="Judges the debate",
                    ),
                ],
                strategy=CollaborationStrategy.BROADCAST,
            )
        )

        # 17. Translation Team
        self.register(
            TeamTemplate(
                name="translation",
                description="Translates content with translator, cultural adapter, and quality checker",
                agents=[
                    AgentTemplate(
                        name="translator",
                        role="translator",
                        system_prompt="You translate text accurately while preserving meaning. Focus on accuracy and natural language.",
                        description="Translates content",
                    ),
                    AgentTemplate(
                        name="cultural_adapter",
                        role="adapter",
                        system_prompt="You adapt content for cultural context. Focus on idioms, references, and cultural appropriateness.",
                        description="Adapts culturally",
                    ),
                    AgentTemplate(
                        name="quality_checker",
                        role="checker",
                        system_prompt="You verify translation quality and consistency. Focus on accuracy, fluency, and terminology.",
                        description="Checks quality",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 18. Security Audit Team
        self.register(
            TeamTemplate(
                name="security-audit",
                description="Audits security with penetration tester, code auditor, and compliance checker",
                agents=[
                    AgentTemplate(
                        name="penetration_tester",
                        role="tester",
                        system_prompt="You identify security vulnerabilities through testing. Focus on common vulnerabilities and attack vectors.",
                        description="Tests for vulnerabilities",
                    ),
                    AgentTemplate(
                        name="code_auditor",
                        role="auditor",
                        system_prompt="You audit code for security issues. Focus on injection flaws, authentication, and data protection.",
                        description="Audits code security",
                    ),
                    AgentTemplate(
                        name="compliance_checker",
                        role="checker",
                        system_prompt="You verify security compliance with standards. Focus on GDPR, SOC2, ISO27001, and industry requirements.",
                        description="Checks compliance",
                    ),
                ],
                strategy=CollaborationStrategy.BROADCAST,
            )
        )

        # 19. Creative Writing Team
        self.register(
            TeamTemplate(
                name="creative-writing",
                description="Creates fiction with plotter, writer, and editor",
                agents=[
                    AgentTemplate(
                        name="plotter",
                        role="plotter",
                        system_prompt="You develop story plots, characters, and arcs. Focus on structure, conflict, and character development.",
                        description="Develops plot",
                    ),
                    AgentTemplate(
                        name="fiction_writer",
                        role="writer",
                        system_prompt="You write engaging fiction with vivid descriptions. Focus on voice, pacing, and emotional impact.",
                        description="Writes the story",
                    ),
                    AgentTemplate(
                        name="fiction_editor",
                        role="editor",
                        system_prompt="You edit fiction for clarity and impact. Focus on pacing, consistency, and emotional resonance.",
                        description="Edits the story",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )

        # 20. DevOps Team
        self.register(
            TeamTemplate(
                name="devops",
                description="Manages infrastructure with infrastructure engineer, CI/CD specialist, and monitoring expert",
                agents=[
                    AgentTemplate(
                        name="infrastructure_engineer",
                        role="engineer",
                        system_prompt="You design and manage infrastructure. Focus on scalability, reliability, and cost optimization.",
                        description="Manages infrastructure",
                    ),
                    AgentTemplate(
                        name="cicd_specialist",
                        role="specialist",
                        system_prompt="You build and optimize CI/CD pipelines. Focus on automation, testing, and deployment speed.",
                        description="Builds CI/CD",
                    ),
                    AgentTemplate(
                        name="monitoring_expert",
                        role="expert",
                        system_prompt="You set up monitoring and alerting. Focus on observability, incident response, and performance.",
                        description="Sets up monitoring",
                    ),
                ],
                strategy=CollaborationStrategy.ROUND_ROBIN,
            )
        )


# Global registry instance
_global_registry: Optional[TemplateRegistry] = None


def get_registry() -> TemplateRegistry:
    """Get the global template registry.

    Returns:
        The global TemplateRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = TemplateRegistry()
    return _global_registry
