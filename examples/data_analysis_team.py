"""Data Analysis Team Example

Demonstrates a practical multi-agent system for analyzing datasets.
This example shows how to use AgentMind for real data analysis tasks.

Team composition:
- Data Analyst: Examines data patterns and statistics
- Domain Expert: Provides context and business insights
- Visualizer: Suggests appropriate visualizations
- Summarizer: Creates actionable recommendations
"""

import asyncio
from pathlib import Path

from agentmind import Agent, AgentMind
from agentmind.core.types import CollaborationStrategy
from agentmind.llm import OllamaProvider


async def analyze_dataset(dataset_description: str, model: str = "llama3.2"):
    """Run a data analysis team on a dataset description.

    Args:
        dataset_description: Description of the dataset to analyze
        model: Ollama model to use (default: llama3.2)

    Returns:
        Analysis results from the team
    """
    # Initialize LLM provider
    llm = OllamaProvider(model=model)

    # Create AgentMind with round-robin strategy for structured analysis
    mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN, llm_provider=llm)

    # Create specialized agents
    analyst = Agent(name="DataAnalyst", role="analyst", llm_provider=llm)
    analyst.config.system_prompt = """You are a data analyst expert.
Analyze datasets for patterns, outliers, and statistical insights.
Focus on data quality, distributions, and key metrics."""

    expert = Agent(name="DomainExpert", role="expert", llm_provider=llm)
    expert.config.system_prompt = """You are a domain expert.
Provide business context and interpret findings.
Connect data insights to real-world implications."""

    visualizer = Agent(name="Visualizer", role="creative", llm_provider=llm)
    visualizer.config.system_prompt = """You are a data visualization expert.
Suggest the best charts and visualizations for the data.
Recommend tools and specific visualization approaches."""

    summarizer = Agent(name="Summarizer", role="coordinator", llm_provider=llm)
    summarizer.config.system_prompt = """You are a synthesis expert.
Create clear, actionable summaries from team discussions.
Provide concrete next steps and recommendations."""

    # Add agents in analysis order
    mind.add_agent(analyst)
    mind.add_agent(expert)
    mind.add_agent(visualizer)
    mind.add_agent(summarizer)

    # Run collaboration
    print("\n" + "=" * 60)
    print("DATA ANALYSIS TEAM - Starting Analysis")
    print("=" * 60 + "\n")

    result = await mind.collaborate(
        task=f"Analyze this dataset: {dataset_description}", max_rounds=2
    )

    return result


async def main():
    """Run example data analysis scenarios."""

    # Example 1: E-commerce sales data
    print("\n### Example 1: E-commerce Sales Analysis ###\n")

    dataset1 = """
    E-commerce sales data for Q1 2024:
    - 50,000 transactions
    - Average order value: $85
    - 30% increase in mobile purchases
    - Top category: Electronics (40% of revenue)
    - Cart abandonment rate: 68%
    - Peak sales: Weekends between 2-4 PM
    """

    result1 = await analyze_dataset(dataset1)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nFinal Result:\n{result1.final_output}")
    print(f"\nRounds: {result1.rounds}")
    print(f"Participants: {', '.join(result1.participants)}")

    # Example 2: Customer churn data
    print("\n\n### Example 2: Customer Churn Analysis ###\n")

    dataset2 = """
    Customer churn data:
    - 10,000 customers tracked over 12 months
    - Overall churn rate: 15%
    - High churn in first 3 months (25%)
    - Customers with support tickets: 40% churn
    - Customers using premium features: 5% churn
    - Average customer lifetime: 18 months
    """

    result2 = await analyze_dataset(dataset2)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nFinal Result:\n{result2.final_output}")
    print(f"\nRounds: {result2.rounds}")


if __name__ == "__main__":
    asyncio.run(main())
