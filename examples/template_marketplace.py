"""Example: Using the template marketplace."""

import asyncio

from agentmind.llm import OllamaProvider
from agentmind.templates import TemplateLoader, load_template


async def main():
    """Demonstrate template usage."""
    # Initialize LLM provider
    llm = OllamaProvider(model="llama3.2")

    # Method 1: Using the loader
    loader = TemplateLoader(llm)

    # List available templates
    print("Available Templates:")
    print("=" * 60)
    for template in loader.list_templates():
        print(f"\n{template['name']}")
        print(f"  Description: {template['description']}")
        print(f"  Agents: {template['agents']}")
        print(f"  Strategy: {template['strategy']}")

    # Get detailed info about a template
    print("\n\nResearch Template Details:")
    print("=" * 60)
    info = loader.get_template_info("research")
    if info:
        print(f"Name: {info['name']}")
        print(f"Description: {info['description']}")
        print(f"Strategy: {info['strategy']}")
        print("\nAgents:")
        for agent in info["agents"]:
            print(f"  - {agent['name']} ({agent['role']}): {agent['description']}")

    # Method 2: Quick load using convenience function
    print("\n\nLoading Research Team:")
    print("=" * 60)
    mind = load_template("research", llm)

    # Use the team
    result = await mind.collaborate(
        "Research the latest developments in quantum computing and their practical applications",
        max_rounds=3,
    )

    print("\n\nCollaboration Result:")
    print("=" * 60)
    print(result)

    # Try another template
    print("\n\nLoading Code Generation Team:")
    print("=" * 60)
    code_team = load_template("code - generation", llm)

    result = await code_team.collaborate(
        "Design and implement a simple REST API for a todo list application",
        max_rounds=3,
    )

    print("\n\nCode Generation Result:")
    print("=" * 60)
    print(result)

    # Try startup validator
    print("\n\nLoading Startup Validator Team:")
    print("=" * 60)
    validator = load_template("startup - validator", llm)

    result = await validator.collaborate(
        "Validate this startup idea: An AI - powered personal finance assistant that automatically categorizes expenses and provides investment recommendations",  # noqa: E501
        max_rounds=2,
    )

    print("\n\nValidation Result:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
