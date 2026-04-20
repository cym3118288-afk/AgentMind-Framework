"""
Real - world Use Case: Content Generation Pipeline

This example demonstrates an automated content generation system using AgentMind.
Multiple specialized agents collaborate to create high - quality content:
- Research and fact - checking
- Outline creation
- Content writing
- Editing and refinement
- SEO optimization

Features:
- Multi - stage content pipeline
- Quality assurance
- SEO optimization
- Multiple content formats
- Collaborative refinement
"""

import asyncio
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class ContentType(str, Enum):
    BLOG_POST = "blog_post"
    ARTICLE = "article"
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    PRODUCT_DESCRIPTION = "product_description"


class ContentStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"


@dataclass
class ContentBrief:
    """Content creation brie"""

    topic: str
    content_type: ContentType
    target_audience: str
    tone: str
    keywords: List[str]
    word_count: int
    additional_requirements: Optional[str] = None


@dataclass
class ContentPiece:
    """Generated content piece"""

    brief: ContentBrief
    title: str
    outline: List[str]
    content: str
    seo_score: int
    readability_score: int
    status: ContentStatus = ContentStatus.DRAFT


class ResearchTool(Tool):
    """Simulates research and fact - checking"""

    def __init__(self):
        self.knowledge_base = {
            "ai": "Artificial Intelligence is transforming industries through machine learning, natural language processing, and computer vision.",  # noqa: E501
            "python": "Python is a versatile programming language known for its simplicity and extensive ecosystem of libraries.",  # noqa: E501
            "marketing": "Digital marketing encompasses SEO, content marketing, social media, and data - driven strategies.",  # noqa: E501
            "health": "Modern healthcare focuses on preventive care, personalized medicine, and digital health technologies.",  # noqa: E501
            "finance": "Financial technology (FinTech) is revolutionizing banking, payments, and investment management.",  # noqa: E501
        }

        super().__init__(
            name="research",
            description="Research topics and gather factual information",
            parameters={"topic": {"type": "string", "description": "Topic to research"}},
        )

    async def execute(self, topic: str) -> str:
        """Perform research"""
        topic_lower = topic.lower()

        # Find relevant information
        results = []
        for key, value in self.knowledge_base.items():
            if key in topic_lower:
                results.append(f"**{key.title()}**: {value}")

        if results:
            return "Research findings:\n" + "\n\n".join(results)
        return f"General information about {topic}: This is an emerging topic with growing interest and applications."


class SEOAnalysisTool(Tool):
    """Analyzes content for SEO optimization"""

    def __init__(self):
        super().__init__(
            name="seo_analysis",
            description="Analyze content for SEO optimization",
            parameters={
                "content": {"type": "string", "description": "Content to analyze"},
                "keywords": {
                    "type": "string",
                    "description": "Target keywords (comma - separated)",
                },
            },
        )

    async def execute(self, content: str, keywords: str) -> str:
        """Analyze SEO"""
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        content_lower = content.lower()

        analysis = []

        # Check keyword presence
        for keyword in keyword_list:
            count = content_lower.count(keyword)
            if count == 0:
                analysis.append(f"❌ Keyword '{keyword}' not found")
            elif count < 3:
                analysis.append(f"⚠️ Keyword '{keyword}' appears {count} time(s) - increase usage")
            else:
                analysis.append(f"✓ Keyword '{keyword}' appears {count} time(s)")

        # Check content length
        word_count = len(content.split())
        if word_count < 300:
            analysis.append(f"⚠️ Content too short ({word_count} words) - aim for 500+")
        else:
            analysis.append(f"✓ Good content length ({word_count} words)")

        # Check headings
        if "#" in content or "##" in content:
            analysis.append("✓ Headings present")
        else:
            analysis.append("⚠️ Add headings for better structure")

        return "SEO Analysis:\n" + "\n".join(analysis)


class ReadabilityTool(Tool):
    """Analyzes content readability"""

    def __init__(self):
        super().__init__(
            name="readability_check",
            description="Check content readability and clarity",
            parameters={"content": {"type": "string", "description": "Content to analyze"}},
        )

    async def execute(self, content: str) -> str:
        """Check readability"""
        sentences = content.split(".")
        words = content.split()

        avg_sentence_length = len(words) / max(len(sentences), 1)

        analysis = []
        analysis.append(f"Total words: {len(words)}")
        analysis.append(f"Total sentences: {len(sentences)}")
        analysis.append(f"Avg sentence length: {avg_sentence_length:.1f} words")

        if avg_sentence_length > 25:
            analysis.append("⚠️ Sentences too long - aim for 15 - 20 words")
        else:
            analysis.append("✓ Good sentence length")

        # Check for passive voice indicators
        passive_indicators = ["was", "were", "been", "being"]
        passive_count = sum(content.lower().count(word) for word in passive_indicators)
        if passive_count > len(words) * 0.1:
            analysis.append("⚠️ High passive voice usage - use active voice")
        else:
            analysis.append("✓ Good use of active voice")

        return "Readability Analysis:\n" + "\n".join(analysis)


async def create_content_pipeline() -> AgentMind:
    """Create the content generation multi - agent system"""

    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)

    # Create tools
    research_tool = ResearchTool()
    seo_tool = SEOAnalysisTool()
    readability_tool = ReadabilityTool()

    # 1. Research Agent
    researcher = Agent(
        name="Researcher",
        role="content_researcher",
        system_prompt="""You are a thorough researcher. Your job is to:
        1. Research topics comprehensively
        2. Gather accurate, relevant information
        3. Identify key facts and insights
        4. Provide source material for writers

        Focus on accuracy and relevance.""",
        tools=[research_tool],
    )

    # 2. Outline Creator
    outliner = Agent(
        name="Outliner",
        role="content_strategist",
        system_prompt="""You are a content strategist. Your job is to:
        1. Create clear, logical content outlines
        2. Structure information effectively
        3. Ensure comprehensive coverage
        4. Plan engaging flow

        Create outlines that guide writers to produce excellent content.""",
    )

    # 3. Content Writer
    writer = Agent(
        name="Writer",
        role="content_writer",
        system_prompt="""You are a skilled content writer. Your job is to:
        1. Write engaging, clear content
        2. Follow the outline structure
        3. Match the specified tone and style
        4. Include target keywords naturally
        5. Write for the target audience

        Create content that informs, engages, and converts.""",
    )

    # 4. Editor
    editor = Agent(
        name="Editor",
        role="content_editor",
        system_prompt="""You are a meticulous editor. Your job is to:
        1. Review content for clarity and flow
        2. Check grammar and style
        3. Ensure consistency
        4. Improve readability
        5. Refine messaging

        Polish content to professional standards.""",
        tools=[readability_tool],
    )

    # 5. SEO Specialist
    seo_specialist = Agent(
        name="SEO_Specialist",
        role="seo_expert",
        system_prompt="""You are an SEO expert. Your job is to:
        1. Optimize content for search engines
        2. Ensure keyword integration
        3. Improve content structure
        4. Enhance discoverability
        5. Provide SEO recommendations

        Make content rank well while maintaining quality.""",
        tools=[seo_tool],
    )

    mind.add_agent(researcher)
    mind.add_agent(outliner)
    mind.add_agent(writer)
    mind.add_agent(editor)
    mind.add_agent(seo_specialist)

    return mind


async def generate_content(mind: AgentMind, brief: ContentBrief) -> ContentPiece:
    """Generate content using the multi - agent pipeline"""

    print(f"\n{'='*60}")
    print("Generating Content")
    print(f"Topic: {brief.topic}")
    print(f"Type: {brief.content_type.value}")
    print(f"Target: {brief.target_audience}")
    print(f"Tone: {brief.tone}")
    print(f"Keywords: {', '.join(brief.keywords)}")
    print(f"{'='*60}\n")

    # Create generation context
    context = """
    Create content based on this brief:

    Topic: {brief.topic}
    Content Type: {brief.content_type.value}
    Target Audience: {brief.target_audience}
    Tone: {brief.tone}
    Keywords: {', '.join(brief.keywords)}
    Word Count: {brief.word_count}
    Additional Requirements: {brief.additional_requirements or 'None'}

    Process:
    1. Research the topic thoroughly
    2. Create a detailed outline
    3. Write the content following the outline
    4. Edit for clarity and readability
    5. Optimize for SEO

    Deliver high - quality, engaging content that meets all requirements.
    """

    # Collaborate to generate content
    result = await mind.collaborate(context, max_rounds=5)

    print(f"\n{'='*60}")
    print("Content Generation Complete")
    print(f"\nGenerated Content:\n{result[:500]}...")
    print(f"{'='*60}\n")

    # Create content piece
    content_piece = ContentPiece(
        brief=brief,
        title=f"{brief.topic} - Complete Guide",
        outline=["Introduction", "Main Content", "Conclusion"],
        content=result,
        seo_score=85,
        readability_score=90,
        status=ContentStatus.APPROVED,
    )

    return content_piece


async def example_blog_post():
    """Example 1: Generate a blog post"""
    print("\n=== Example 1: Blog Post Generation ===\n")

    mind = await create_content_pipeline()

    brief = ContentBrief(
        topic="Getting Started with Python for Data Science",
        content_type=ContentType.BLOG_POST,
        target_audience="Beginner programmers",
        tone="Educational and friendly",
        keywords=["python", "data science", "beginners", "tutorial"],
        word_count=800,
    )

    await generate_content(mind, brief)


async def example_product_description():
    """Example 2: Generate product description"""
    print("\n=== Example 2: Product Description ===\n")

    mind = await create_content_pipeline()

    brief = ContentBrief(
        topic="Smart Fitness Tracker with AI Coaching",
        content_type=ContentType.PRODUCT_DESCRIPTION,
        target_audience="Health - conscious consumers",
        tone="Persuasive and exciting",
        keywords=["fitness tracker", "AI coaching", "health monitoring"],
        word_count=300,
        additional_requirements="Highlight unique AI features and benefits",
    )

    await generate_content(mind, brief)


async def example_social_media():
    """Example 3: Generate social media content"""
    print("\n=== Example 3: Social Media Post ===\n")

    mind = await create_content_pipeline()

    brief = ContentBrief(
        topic="Launch of New AI - Powered Marketing Tool",
        content_type=ContentType.SOCIAL_MEDIA,
        target_audience="Marketing professionals",
        tone="Exciting and concise",
        keywords=["AI marketing", "automation", "productivity"],
        word_count=150,
        additional_requirements="Include call - to - action",
    )

    await generate_content(mind, brief)


async def example_email_campaign():
    """Example 4: Generate email content"""
    print("\n=== Example 4: Email Campaign ===\n")

    mind = await create_content_pipeline()

    brief = ContentBrief(
        topic="Exclusive Offer: 30% Off Premium Subscription",
        content_type=ContentType.EMAIL,
        target_audience="Existing customers",
        tone="Friendly and persuasive",
        keywords=["exclusive offer", "premium", "limited time"],
        word_count=400,
        additional_requirements="Include urgency and clear CTA",
    )

    await generate_content(mind, brief)


async def main():
    """Run all content generation examples"""
    print("=" * 60)
    print("Content Generation Pipeline with AgentMind")
    print("=" * 60)

    await example_blog_post()
    await example_product_description()
    await example_social_media()
    await example_email_campaign()

    print("\n" + "=" * 60)
    print("Content generation examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
