# Software Development Swarm Example

"""
Software Development Swarm - Multi - agent collaboration for software development.

This example demonstrates:
- System architecture design
- Code implementation planning
- Security review
- Performance optimization
- DevOps and deployment strategy
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from agentmind import Agent, AgentMind  # noqa: E402
from agentmind.llm import OllamaProvider  # noqa: E402


async def run_software_dev_swarm(project_description: str, requirements: list):
    """Run a software development planning session."""

    print(f"\n{'=' * 80}")
    print("Software Development Swarm")
    print(f"{'=' * 80}\n")
    print(f"Project: {project_description}\n")
    print("Requirements:")
    for i, req in enumerate(requirements, 1):
        print(f"  {i}. {req}")
    print()

    # Initialize LLM provider
    try:
        llm = OllamaProvider(model="llama3.2")
        print("✓ Connected to Ollama")
    except Exception as e:
        print(f"⚠ Ollama not available: {e}")
        print("Using template responses for demonstration\n")
        llm = None

    # Create AgentMind
    mind = AgentMind(llm_provider=llm)

    # Create development team
    print("\nCreating development team...\n")

    architect = Agent(
        name="Software Architect",
        role="architecture",
        system_prompt="""You are a Senior Software Architect with 15+ years of experience.

        Your expertise includes:
        - System design and architecture patterns
        - Microservices and distributed systems
        - Database design and optimization
        - API design and integration
        - Scalability and performance

        You design robust, scalable systems that meet business requirements.
        Focus on maintainability, extensibility, and best practices.""",
        llm_provider=llm,
    )

    senior_engineer = Agent(
        name="Senior Engineer",
        role="implementation",
        system_prompt="""You are a Senior Software Engineer with expertise in multiple languages.

        Your expertise includes:
        - Clean code and design patterns
        - Test - driven development
        - Code review and refactoring
        - Framework and library selection
        - Technical documentation

        You write high - quality, maintainable code that follows best practices.
        Focus on code quality, testing, and documentation.""",
        llm_provider=llm,
    )

    security_engineer = Agent(
        name="Security Engineer",
        role="security",
        system_prompt="""You are a Security Engineer focused on application security.

        Your expertise includes:
        - OWASP Top 10 vulnerabilities
        - Authentication and authorization
        - Data encryption and protection
        - Security testing and auditing
        - Compliance requirements

        You identify security risks and implement robust defenses.
        Focus on secure coding practices and threat mitigation.""",
        llm_provider=llm,
    )

    devops_engineer = Agent(
        name="DevOps Engineer",
        role="devops",
        system_prompt="""You are a DevOps Engineer specializing in CI / CD and infrastructure.

        Your expertise includes:
        - Container orchestration (Docker, Kubernetes)
        - CI / CD pipeline design
        - Infrastructure as Code
        - Monitoring and observability
        - Cloud platforms (AWS, GCP, Azure)

        You ensure reliable, automated deployment and operations.
        Focus on automation, reliability, and scalability.""",
        llm_provider=llm,
    )

    qa_engineer = Agent(
        name="QA Engineer",
        role="quality_assurance",
        system_prompt="""You are a QA Engineer dedicated to software quality.

        Your expertise includes:
        - Test strategy and planning
        - Automated testing frameworks
        - Performance and load testing
        - Bug tracking and reporting
        - Quality metrics

        You ensure software meets quality standards before release.
        Focus on comprehensive testing and quality assurance.""",
        llm_provider=llm,
    )

    # Add agents to team
    mind.add_agent(architect)
    mind.add_agent(senior_engineer)
    mind.add_agent(security_engineer)
    mind.add_agent(devops_engineer)
    mind.add_agent(qa_engineer)

    print("✓ Software Architect - System design")
    print("✓ Senior Engineer - Implementation")
    print("✓ Security Engineer - Security review")
    print("✓ DevOps Engineer - Deployment strategy")
    print("✓ QA Engineer - Testing strategy")

    # Define development task
    # _requirements_text = "\n".join([f"- {req}" for req in requirements])
    task = """
    Design and plan the development of: {project_description}

    Requirements:
    {requirements_text}

    Please collaborate to create:
    1. System architecture and design
    2. Technology stack recommendations
    3. Implementation plan and milestones
    4. Security considerations and measures
    5. DevOps and deployment strategy
    6. Testing strategy and quality assurance
    7. Timeline and resource estimates

    Provide a comprehensive development plan.
    """

    # Run collaboration
    print("\n" + "=" * 80)
    print("Starting development planning collaboration...")
    print("=" * 80 + "\n")

    result = await mind.collaborate(task=task, max_rounds=6)

    # Display results
    print("\n" + "=" * 80)
    print("DEVELOPMENT PLAN")
    print("=" * 80 + "\n")
    print(result)

    # Display statistics
    print("\n" + "=" * 80)
    print("COLLABORATION STATISTICS")
    print("=" * 80 + "\n")
    print(f"Total Messages: {len(mind.conversation_history)}")
    print(f"Rounds Completed: {len(mind.conversation_history) // 5}")
    print("Agents Participated: 5")

    return result


async def main():
    """Main entry point."""

    # Example 1: E - commerce Platform
    print("\n" + "=" * 80)
    print("EXAMPLE 1: E - commerce Platform")
    print("=" * 80)

    await run_software_dev_swarm(
        project_description="Modern e - commerce platform with real - time inventory",
        requirements=[
            "User authentication and authorization",
            "Product catalog with search and filtering",
            "Shopping cart and checkout process",
            "Payment gateway integration",
            "Real - time inventory management",
            "Order tracking and notifications",
            "Admin dashboard for management",
            "Mobile - responsive design",
            "Support for 10,000+ concurrent users",
            "PCI DSS compliance",
        ],
    )

    # Example 2: Healthcare API
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Healthcare Data API")
    print("=" * 80)

    await run_software_dev_swarm(
        project_description="HIPAA - compliant healthcare data API",
        requirements=[
            "RESTful API with versioning",
            "Patient data management",
            "Medical records storage and retrieval",
            "Role - based access control",
            "Audit logging for all operations",
            "Data encryption at rest and in transit",
            "HIPAA compliance requirements",
            "Integration with EHR systems",
            "Rate limiting and throttling",
            "Comprehensive API documentation",
        ],
    )


if __name__ == "__main__":
    asyncio.run(main())
