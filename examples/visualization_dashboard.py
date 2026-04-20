"""Example: Using the visualization dashboard."""

import asyncio

from agentmind.core import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.visualization import launch_dashboard


async def setup_mind():
    """Set up an AgentMind instance for the dashboard."""
    # Initialize LLM provider
    llm = OllamaProvider(model="llama3.2")

    # Create AgentMind
    mind = AgentMind(llm_provider=llm)

    # Add agents
    mind.add_agent(
        Agent(
            name="researcher",
            role="researcher",
            llm_provider=llm,
        )
    )

    mind.add_agent(
        Agent(
            name="analyst",
            role="analyst",
            llm_provider=llm,
        )
    )

    mind.add_agent(
        Agent(
            name="writer",
            role="writer",
            llm_provider=llm,
        )
    )

    return mind


def main():
    """Launch the dashboard."""
    print("Setting up AgentMind...")
    mind = asyncio.run(setup_mind())

    print("\nLaunching dashboard...")
    print("The dashboard will open in your browser.")
    print("Press Ctrl + C to stop the server.")

    # Launch dashboard
    # Set share=True to create a public link
    launch_dashboard(mind, share=False)


if __name__ == "__main__":
    main()
