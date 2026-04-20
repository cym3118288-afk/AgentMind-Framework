"""
Advanced Example: Self - Improving Agent

This example demonstrates an agent that learns from experience and improves over time:
- Performance tracking and analysis
- Strategy adaptation
- Knowledge accumulation
- Self - reflection and improvement
- Meta - learning capabilities

Estimated time: 30 minutes
Difficulty: Advanced
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime
from agentmind import Agent, Message
from agentmind.llm import OllamaProvider


class PerformanceTracker:
    """Tracks agent performance metrics"""

    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        self.success_rate = 0.0
        self.avg_quality_score = 0.0

    def record_task(
        self, task: str, result: str, success: bool, quality_score: float, duration: float
    ):
        """Record a completed task"""
        self.tasks.append(
            {
                "timestamp": datetime.now().isoformat(),
                "task": task,
                "result": result,
                "success": success,
                "quality_score": quality_score,
                "duration": duration,
            }
        )

        # Update metrics
        successful_tasks = sum(1 for t in self.tasks if t["success"])
        self.success_rate = successful_tasks / len(self.tasks)
        self.avg_quality_score = sum(t["quality_score"] for t in self.tasks) / len(self.tasks)

    def get_insights(self) -> Dict[str, Any]:
        """Analyze performance and generate insights"""
        if not self.tasks:
            return {"insights": "No data yet"}

        recent_tasks = self.tasks[-10:]
        recent_success = sum(1 for t in recent_tasks if t["success"]) / len(recent_tasks)

        return {
            "total_tasks": len(self.tasks),
            "success_rate": self.success_rate,
            "recent_success_rate": recent_success,
            "avg_quality": self.avg_quality_score,
            "trend": "improving" if recent_success > self.success_rate else "declining",
        }


class KnowledgeBase:
    """Stores learned knowledge and patterns"""

    def __init__(self):
        self.knowledge: Dict[str, List[str]] = {}
        self.patterns: List[Dict[str, Any]] = []

    def add_knowledge(self, category: str, item: str):
        """Add knowledge to a category"""
        if category not in self.knowledge:
            self.knowledge[category] = []
        if item not in self.knowledge[category]:
            self.knowledge[category].append(item)

    def add_pattern(self, pattern: Dict[str, Any]):
        """Record a successful pattern"""
        self.patterns.append({**pattern, "timestamp": datetime.now().isoformat(), "usage_count": 1})

    def get_relevant_knowledge(self, query: str) -> List[str]:
        """Retrieve relevant knowledge"""
        relevant = []
        query_lower = query.lower()

        for category, items in self.knowledge.items():
            if any(word in query_lower for word in category.lower().split()):
                relevant.extend(items)

        return relevant

    def get_best_patterns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most successful patterns"""
        sorted_patterns = sorted(self.patterns, key=lambda p: p.get("usage_count", 0), reverse=True)
        return sorted_patterns[:limit]


class SelfImprovingAgent(Agent):
    """Agent that learns and improves from experience"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_tracker = PerformanceTracker()
        self.knowledge_base = KnowledgeBase()
        self.improvement_cycles = 0
        self.strategies: List[str] = ["analytical", "creative", "systematic", "intuitive"]
        self.current_strategy = "analytical"

    async def process_with_learning(self, task: str) -> Dict[str, Any]:
        """Process task and learn from the experience"""
        import time

        start_time = time.time()

        # Retrieve relevant knowledge
        relevant_knowledge = self.knowledge_base.get_relevant_knowledge(task)

        # Enhance task with learned knowledge
        enhanced_task = task
        if relevant_knowledge:
            enhanced_task += f"\n\nRelevant knowledge: {', '.join(relevant_knowledge[:3])}"

        # Process the task
        message = Message(content=enhanced_task, sender="system", role="user")
        response = await self.process_message(message)

        duration = time.time() - start_time

        # Evaluate result (simplified - in production, use more sophisticated evaluation)
        quality_score = self._evaluate_quality(response.content)
        success = quality_score > 0.6

        # Record performance
        self.performance_tracker.record_task(
            task=task,
            result=response.content,
            success=success,
            quality_score=quality_score,
            duration=duration,
        )

        # Extract and store new knowledge
        await self._extract_knowledge(task, response.content)

        return {
            "result": response.content,
            "quality_score": quality_score,
            "success": success,
            "duration": duration,
            "strategy_used": self.current_strategy,
        }

    def _evaluate_quality(self, result: str) -> float:
        """Evaluate quality of result (simplified)"""
        # In production, use more sophisticated evaluation
        score = 0.5

        # Length check
        if len(result) > 100:
            score += 0.1

        # Structure check
        if any(marker in result for marker in ["1.", "2.", "-", "*"]):
            score += 0.1

        # Completeness check
        if len(result.split()) > 50:
            score += 0.1

        # Coherence check (simplified)
        sentences = result.split(".")
        if len(sentences) > 3:
            score += 0.2

        return min(score, 1.0)

    async def _extract_knowledge(self, task: str, result: str):
        """Extract and store knowledge from task completion"""
        # Extract key concepts (simplified)
        task_words = task.lower().split()

        # Categorize knowledge
        if "analyze" in task_words or "analysis" in task_words:
            self.knowledge_base.add_knowledge("analysis", f"Approach: {result[:100]}")
        elif "create" in task_words or "design" in task_words:
            self.knowledge_base.add_knowledge("creation", f"Method: {result[:100]}")
        elif "solve" in task_words or "problem" in task_words:
            self.knowledge_base.add_knowledge("problem_solving", f"Solution: {result[:100]}")

    async def self_reflect(self) -> Dict[str, Any]:
        """Reflect on performance and identify improvements"""
        insights = self.performance_tracker.get_insights()

        reflection = {"insights": insights, "improvements_identified": [], "action_plan": []}

        # Identify areas for improvement
        if insights.get("success_rate", 0) < 0.7:
            reflection["improvements_identified"].append("Success rate below target")
            reflection["action_plan"].append("Adjust strategy selection")

        if insights.get("trend") == "declining":
            reflection["improvements_identified"].append("Performance declining")
            reflection["action_plan"].append("Review recent failures and adapt")

        if insights.get("avg_quality", 0) < 0.7:
            reflection["improvements_identified"].append("Quality below target")
            reflection["action_plan"].append("Enhance response generation")

        return reflection

    async def adapt_strategy(self):
        """Adapt strategy based on performance"""
        insights = self.performance_tracker.get_insights()

        # If performance is declining, try a different strategy
        if insights.get("trend") == "declining":
            current_idx = self.strategies.index(self.current_strategy)
            next_idx = (current_idx + 1) % len(self.strategies)
            self.current_strategy = self.strategies[next_idx]
            print(f"Adapting strategy to: {self.current_strategy}")

        self.improvement_cycles += 1

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learning progress"""
        return {
            "improvement_cycles": self.improvement_cycles,
            "knowledge_categories": len(self.knowledge_base.knowledge),
            "total_knowledge_items": sum(
                len(items) for items in self.knowledge_base.knowledge.values()
            ),
            "patterns_learned": len(self.knowledge_base.patterns),
            "current_strategy": self.current_strategy,
            "performance": self.performance_tracker.get_insights(),
        }


async def example_1_basic_learning():
    """Example 1: Basic learning from experience"""
    print("\n=== Example 1: Basic Learning ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = SelfImprovingAgent(name="learner", role="analyst", llm_provider=llm)

    # Process several tasks
    tasks = [
        "Analyze the benefits of renewable energy",
        "Analyze the impact of AI on healthcare",
        "Analyze market trends in e - commerce",
    ]

    for task in tasks:
        result = await agent.process_with_learning(task)
        print(f"Task: {task}")
        print(f"Quality: {result['quality_score']:.2f}")
        print(f"Success: {result['success']}\n")

    # Show learning progress
    summary = agent.get_learning_summary()
    print("Learning Summary:")
    print(f"  Knowledge items: {summary['total_knowledge_items']}")
    print(f"  Performance: {summary['performance']['success_rate']:.2%}\n")


async def example_2_self_reflection():
    """Example 2: Self - reflection and improvement"""
    print("\n=== Example 2: Self - Reflection ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = SelfImprovingAgent(name="reflective", role="analyst", llm_provider=llm)

    # Process tasks
    for i in range(5):
        task = f"Analyze topic {i + 1}"
        await agent.process_with_learning(task)

    # Perform self - reflection
    reflection = await agent.self_reflect()
    print("Self - Reflection Results:")
    print(f"  Insights: {reflection['insights']}")
    print(f"  Improvements identified: {len(reflection['improvements_identified'])}")
    print(f"  Action items: {len(reflection['action_plan'])}\n")


async def example_3_strategy_adaptation():
    """Example 3: Strategy adaptation"""
    print("\n=== Example 3: Strategy Adaptation ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = SelfImprovingAgent(name="adaptive", role="analyst", llm_provider=llm)

    print(f"Initial strategy: {agent.current_strategy}\n")

    # Simulate performance decline
    for i in range(3):
        task = f"Complex task {i + 1}"
        await agent.process_with_learning(task)

    # Adapt strategy
    await agent.adapt_strategy()
    print(f"Adapted strategy: {agent.current_strategy}\n")


async def example_4_knowledge_accumulation():
    """Example 4: Knowledge accumulation"""
    print("\n=== Example 4: Knowledge Accumulation ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = SelfImprovingAgent(name="knowledge_seeker", role="researcher", llm_provider=llm)

    # Process diverse tasks
    tasks = [
        "Analyze data patterns",
        "Create a design proposal",
        "Solve optimization problem",
        "Analyze user behavior",
    ]

    for task in tasks:
        await agent.process_with_learning(task)

    # Show accumulated knowledge
    summary = agent.get_learning_summary()
    print("Knowledge Accumulation:")
    print(f"  Categories: {summary['knowledge_categories']}")
    print(f"  Total items: {summary['total_knowledge_items']}")
    print(f"  Patterns: {summary['patterns_learned']}\n")


async def example_5_continuous_improvement():
    """Example 5: Continuous improvement cycle"""
    print("\n=== Example 5: Continuous Improvement ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = SelfImprovingAgent(name="improver", role="analyst", llm_provider=llm)

    print("Running improvement cycles...\n")

    for cycle in range(3):
        print(f"Cycle {cycle + 1}:")

        # Process tasks
        for i in range(3):
            task = f"Task {i + 1} in cycle {cycle + 1}"
            await agent.process_with_learning(task)

        # Reflect and adapt
        await agent.self_reflect()
        await agent.adapt_strategy()

        summary = agent.get_learning_summary()
        print(f"  Success rate: {summary['performance']['success_rate']:.2%}")
        print(f"  Strategy: {summary['current_strategy']}\n")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("Advanced Example: Self - Improving Agent")
    print("=" * 60)

    await example_1_basic_learning()
    await example_2_self_reflection()
    await example_3_strategy_adaptation()
    await example_4_knowledge_accumulation()
    await example_5_continuous_improvement()

    print("\n" + "=" * 60)
    print("Example Complete!")
    print("=" * 60)
    print("\nKey Concepts:")
    print("1. Performance tracking enables learning")
    print("2. Knowledge accumulation improves future performance")
    print("3. Self - reflection identifies improvement areas")
    print("4. Strategy adaptation responds to performance trends")
    print("5. Continuous improvement cycles drive long - term growth")


if __name__ == "__main__":
    asyncio.run(main())
