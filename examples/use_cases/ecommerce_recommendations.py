"""
E-commerce Recommendation System

A production-ready multi-agent system for personalized product recommendations.
Combines user behavior analysis, inventory management, and personalization.

Features:
- User preference analysis
- Product matching and ranking
- Inventory-aware recommendations
- A/B testing support
- Real-time personalization

Usage:
    python examples/use_cases/ecommerce_recommendations.py
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


@dataclass
class Product:
    """Product information"""

    id: str
    name: str
    category: str
    price: float
    stock: int
    rating: float
    tags: List[str]
    description: str


@dataclass
class UserProfile:
    """User profile and behavior"""

    user_id: str
    purchase_history: List[str]
    browsing_history: List[str]
    preferences: Dict[str, Any]
    budget_range: tuple[float, float]


# Sample data
PRODUCTS = [
    Product(
        "P001",
        "Wireless Headphones",
        "Electronics",
        79.99,
        50,
        4.5,
        ["audio", "wireless", "bluetooth"],
        "High-quality wireless headphones with noise cancellation",
    ),
    Product(
        "P002",
        "Running Shoes",
        "Sports",
        89.99,
        30,
        4.7,
        ["footwear", "running", "athletic"],
        "Comfortable running shoes for daily training",
    ),
    Product(
        "P003",
        "Coffee Maker",
        "Home",
        129.99,
        20,
        4.3,
        ["kitchen", "appliance", "coffee"],
        "Programmable coffee maker with thermal carafe",
    ),
    Product(
        "P004",
        "Yoga Mat",
        "Sports",
        29.99,
        100,
        4.6,
        ["fitness", "yoga", "exercise"],
        "Non-slip yoga mat with carrying strap",
    ),
    Product(
        "P005",
        "Smart Watch",
        "Electronics",
        199.99,
        15,
        4.4,
        ["wearable", "fitness", "smart"],
        "Fitness tracking smartwatch with heart rate monitor",
    ),
    Product(
        "P006",
        "Backpack",
        "Accessories",
        49.99,
        60,
        4.5,
        ["travel", "storage", "outdoor"],
        "Durable backpack with laptop compartment",
    ),
    Product(
        "P007",
        "Blender",
        "Home",
        69.99,
        40,
        4.2,
        ["kitchen", "appliance", "smoothie"],
        "High-speed blender for smoothies and soups",
    ),
    Product(
        "P008",
        "Desk Lamp",
        "Home",
        39.99,
        80,
        4.4,
        ["lighting", "office", "led"],
        "Adjustable LED desk lamp with USB charging",
    ),
]


class ProductSearchTool(Tool):
    """Search products by category, tags, or price range"""

    def __init__(self, products: List[Product]):
        self.products = products
        super().__init__(
            name="search_products",
            description="Search products by category, tags, or price range",
            parameters={
                "category": {"type": "string", "description": "Product category"},
                "tags": {"type": "array", "description": "Product tags to match"},
                "min_price": {"type": "number", "description": "Minimum price"},
                "max_price": {"type": "number", "description": "Maximum price"},
            },
        )

    async def execute(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> str:
        """Search products based on criteria"""
        results = self.products

        if category:
            results = [p for p in results if p.category.lower() == category.lower()]

        if tags:
            results = [p for p in results if any(tag in p.tags for tag in tags)]

        if min_price is not None:
            results = [p for p in results if p.price >= min_price]

        if max_price is not None:
            results = [p for p in results if p.price <= max_price]

        # Sort by rating
        results.sort(key=lambda p: p.rating, reverse=True)

        return json.dumps(
            [
                {
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "price": p.price,
                    "stock": p.stock,
                    "rating": p.rating,
                    "tags": p.tags,
                    "description": p.description,
                }
                for p in results[:10]
            ],
            indent=2,
        )


class InventoryCheckTool(Tool):
    """Check product availability and stock levels"""

    def __init__(self, products: List[Product]):
        self.products = {p.id: p for p in products}
        super().__init__(
            name="check_inventory",
            description="Check if products are in stock",
            parameters={
                "product_ids": {"type": "array", "description": "List of product IDs to check"}
            },
        )

    async def execute(self, product_ids: List[str]) -> str:
        """Check inventory for given product IDs"""
        results = []
        for pid in product_ids:
            if pid in self.products:
                p = self.products[pid]
                results.append(
                    {
                        "id": p.id,
                        "name": p.name,
                        "stock": p.stock,
                        "available": p.stock > 0,
                        "stock_status": (
                            "In Stock"
                            if p.stock > 10
                            else "Low Stock" if p.stock > 0 else "Out of Stock"
                        ),
                    }
                )

        return json.dumps(results, indent=2)


class UserHistoryTool(Tool):
    """Retrieve user purchase and browsing history"""

    def __init__(self, user_profile: UserProfile):
        self.profile = user_profile
        super().__init__(
            name="get_user_history",
            description="Get user's purchase and browsing history",
            parameters={},
        )

    async def execute(self) -> str:
        """Get user history"""
        return json.dumps(
            {
                "user_id": self.profile.user_id,
                "purchase_history": self.profile.purchase_history,
                "browsing_history": self.profile.browsing_history,
                "preferences": self.profile.preferences,
                "budget_range": self.profile.budget_range,
            },
            indent=2,
        )


async def generate_recommendations(user_profile: UserProfile, context: str = "") -> Dict[str, Any]:
    """
    Generate personalized product recommendations using multi-agent system

    Args:
        user_profile: User profile with history and preferences
        context: Additional context (e.g., "birthday gift", "workout gear")

    Returns:
        Recommendation results with products and reasoning
    """
    # Initialize LLM provider
    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)

    # Create tools
    search_tool = ProductSearchTool(PRODUCTS)
    inventory_tool = InventoryCheckTool(PRODUCTS)
    history_tool = UserHistoryTool(user_profile)

    # Create specialized agents
    analyst = Agent(
        name="UserAnalyst",
        role="user_behavior_analyst",
        system_prompt="""You are a user behavior analyst for an e-commerce platform.
        Analyze user purchase history, browsing patterns, and preferences to understand
        their needs and interests. Identify patterns and make insights about what products
        they might be interested in.""",
        tools=[history_tool],
    )

    product_expert = Agent(
        name="ProductExpert",
        role="product_specialist",
        system_prompt="""You are a product specialist who knows the entire catalog.
        Search for products that match user preferences, considering categories, tags,
        price ranges, and ratings. Focus on high-quality products that fit the user's needs.""",
        tools=[search_tool],
    )

    inventory_manager = Agent(
        name="InventoryManager",
        role="inventory_specialist",
        system_prompt="""You are an inventory manager who ensures recommended products
        are actually available. Check stock levels and prioritize in-stock items.
        Flag low-stock items and suggest alternatives if needed.""",
        tools=[inventory_tool],
    )

    recommender = Agent(
        name="Recommender",
        role="recommendation_engine",
        system_prompt="""You are the final recommendation engine. Synthesize insights
        from the analyst, product matches from the expert, and inventory data to create
        a final ranked list of 3-5 product recommendations. Provide clear reasoning for
        each recommendation and explain why it fits the user's needs.""",
        tools=[],
    )

    # Add agents to mind
    mind.add_agent(analyst)
    mind.add_agent(product_expert)
    mind.add_agent(inventory_manager)
    mind.add_agent(recommender)

    # Create task
    task = f"""Generate personalized product recommendations for the user.

    Context: {context if context else 'General recommendations'}

    Steps:
    1. Analyze user's purchase and browsing history to understand preferences
    2. Search for products matching user interests and budget
    3. Verify inventory availability for recommended products
    4. Create final ranked recommendations with reasoning

    Provide 3-5 specific product recommendations with clear explanations."""

    # Collaborate
    print(f"\n{'='*60}")
    print(f"Generating recommendations for user {user_profile.user_id}")
    print(f"Context: {context if context else 'General recommendations'}")
    print(f"{'='*60}\n")

    result = await mind.collaborate(task, max_rounds=4)

    return {
        "user_id": user_profile.user_id,
        "context": context,
        "recommendations": result,
        "timestamp": datetime.now().isoformat(),
    }


async def main():
    """Run example recommendation scenarios"""

    # Example user profile
    user = UserProfile(
        user_id="U12345",
        purchase_history=["Running Shoes", "Fitness Tracker", "Water Bottle"],
        browsing_history=["Yoga Mat", "Resistance Bands", "Protein Powder", "Smart Watch"],
        preferences={
            "categories": ["Sports", "Electronics", "Health"],
            "interests": ["fitness", "running", "wellness"],
            "preferred_brands": ["Nike", "Fitbit", "Apple"],
        },
        budget_range=(30.0, 150.0),
    )

    # Scenario 1: General recommendations
    print("\n" + "=" * 60)
    print("SCENARIO 1: General Recommendations")
    print("=" * 60)
    result1 = await generate_recommendations(user)
    print("\nRecommendations:")
    print(result1["recommendations"])

    # Scenario 2: Specific context
    print("\n" + "=" * 60)
    print("SCENARIO 2: Home Workout Setup")
    print("=" * 60)
    result2 = await generate_recommendations(
        user, context="User wants to set up a home workout space"
    )
    print("\nRecommendations:")
    print(result2["recommendations"])

    # Scenario 3: Gift recommendations
    print("\n" + "=" * 60)
    print("SCENARIO 3: Gift for Fitness Enthusiast")
    print("=" * 60)
    result3 = await generate_recommendations(
        user, context="Looking for a birthday gift for a fitness enthusiast friend"
    )
    print("\nRecommendations:")
    print(result3["recommendations"])


if __name__ == "__main__":
    print(
        """
    ╔══════════════════════════════════════════════════════════╗
    ║   E-commerce Recommendation System - AgentMind Demo     ║
    ║                                                          ║
    ║   Multi-agent system for personalized recommendations   ║
    ╚══════════════════════════════════════════════════════════╝
    """
    )

    asyncio.run(main())
