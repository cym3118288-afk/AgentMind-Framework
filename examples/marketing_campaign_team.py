# Marketing Campaign Team Example

"""
Marketing Campaign Team - Multi-agent collaboration for campaign planning.

This example demonstrates:
- Marketing strategy development
- Creative concept generation
- Content planning and SEO
- Campaign execution planning
- Performance metrics definition
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider


async def run_marketing_campaign(product: str, target_audience: str, budget: str):
    """Run a marketing campaign planning session."""

    print(f"\n{'='*80}")
    print(f"Marketing Campaign Planning")
    print(f"{'='*80}\n")
    print(f"Product: {product}")
    print(f"Target Audience: {target_audience}")
    print(f"Budget: {budget}\n")

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

    # Create marketing team
    print("\nCreating marketing team...\n")

    marketing_manager = Agent(
        name="Marketing Manager",
        role="marketing_strategy",
        system_prompt="""You are a Marketing Manager with 10+ years of experience in digital marketing.

        Your expertise includes:
        - Marketing strategy and planning
        - Campaign management and execution
        - Customer segmentation and targeting
        - Marketing analytics and ROI
        - Budget allocation and optimization

        You develop comprehensive marketing strategies that drive customer acquisition and retention.
        Focus on data-driven decisions and measurable outcomes.""",
        llm_provider=llm,
    )

    creative_director = Agent(
        name="Creative Director",
        role="creative_direction",
        system_prompt="""You are a Creative Director with a portfolio of award-winning campaigns.

        Your expertise includes:
        - Creative concept development
        - Brand storytelling and messaging
        - Visual identity and design direction
        - Campaign ideation
        - Multi-channel creative execution

        You bring bold, original ideas that capture attention and resonate with audiences.
        Focus on emotional connection and brand differentiation.""",
        llm_provider=llm,
    )

    content_strategist = Agent(
        name="Content Strategist",
        role="content_strategy",
        system_prompt="""You are a Content Strategist specializing in engaging, SEO-optimized content.

        Your expertise includes:
        - Content planning and calendaring
        - SEO and keyword strategy
        - Audience analysis and personas
        - Content distribution strategy
        - Performance metrics and optimization

        You create content strategies that attract, engage, and convert audiences.
        Focus on search visibility and user engagement.""",
        llm_provider=llm,
    )

    social_media_manager = Agent(
        name="Social Media Manager",
        role="social_media",
        system_prompt="""You are a Social Media Manager expert in building engaged communities.

        Your expertise includes:
        - Social media strategy across platforms
        - Community management and engagement
        - Influencer partnerships
        - Social advertising and targeting
        - Analytics and reporting

        You build authentic connections and drive conversations around brands.
        Focus on engagement, reach, and community growth.""",
        llm_provider=llm,
    )

    # Add agents to team
    mind.add_agent(marketing_manager)
    mind.add_agent(creative_director)
    mind.add_agent(content_strategist)
    mind.add_agent(social_media_manager)

    print("✓ Marketing Manager - Strategy and planning")
    print("✓ Creative Director - Creative concepts")
    print("✓ Content Strategist - Content and SEO")
    print("✓ Social Media Manager - Social engagement")

    # Define campaign task
    task = f"""
    Plan a comprehensive marketing campaign for: {product}

    Target Audience: {target_audience}
    Budget: {budget}

    Please develop:
    1. Overall marketing strategy and objectives
    2. Creative concept and messaging
    3. Content plan with SEO strategy
    4. Social media strategy and tactics
    5. Timeline and milestones
    6. Success metrics and KPIs
    7. Budget allocation across channels

    Collaborate to create a cohesive, executable campaign plan.
    """

    # Run collaboration
    print("\n" + "=" * 80)
    print("Starting campaign planning collaboration...")
    print("=" * 80 + "\n")

    result = await mind.collaborate(task=task, max_rounds=5)

    # Display results
    print("\n" + "=" * 80)
    print("CAMPAIGN PLAN")
    print("=" * 80 + "\n")
    print(result)

    # Display statistics
    print("\n" + "=" * 80)
    print("COLLABORATION STATISTICS")
    print("=" * 80 + "\n")
    print(f"Total Messages: {len(mind.conversation_history)}")
    print(f"Rounds Completed: {len(mind.conversation_history) // 4}")
    print(f"Agents Participated: 4")

    return result


async def main():
    """Main entry point."""

    # Example 1: SaaS Product Launch
    print("\n" + "=" * 80)
    print("EXAMPLE 1: SaaS Product Launch")
    print("=" * 80)

    await run_marketing_campaign(
        product="AI-powered project management tool for remote teams",
        target_audience="Tech-savvy project managers and team leads at SMBs (25-500 employees)",
        budget="$50,000 for 3-month campaign",
    )

    # Example 2: E-commerce Product
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: E-commerce Product Launch")
    print("=" * 80)

    await run_marketing_campaign(
        product="Sustainable, eco-friendly yoga mats made from recycled materials",
        target_audience="Health-conscious millennials and Gen Z (25-40 years old) interested in sustainability",
        budget="$25,000 for 2-month campaign",
    )


if __name__ == "__main__":
    asyncio.run(main())
