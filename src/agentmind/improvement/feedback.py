"""Feedback loop mechanisms for continuous agent improvement.

Tracks performance metrics and adjusts agent behavior based on feedback.
"""

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from ..core.agent import Agent
from ..core.types import Message


class FeedbackLoop:
    """Manages feedback loops for agent improvement.

    Collects performance data, user feedback, and automatically adjusts
    agent behavior to improve over time.

    Example:
        >>> loop = FeedbackLoop()
        >>> loop.add_agent(agent)
        >>> loop.record_interaction(agent.name, task, response, rating=4.5)
        >>> suggestions = loop.get_improvement_suggestions(agent.name)
    """

    def __init__(self):
        """Initialize the feedback loop system."""
        self.agents: Dict[str, Agent] = {}
        self.interaction_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.performance_metrics: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {
                "avg_rating": 0.0,
                "total_interactions": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
            }
        )
        self.feedback_callbacks: List[Callable] = []

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the feedback loop.

        Args:
            agent: Agent to track
        """
        self.agents[agent.name] = agent

    def record_interaction(
        self,
        agent_name: str,
        task: str,
        response: str,
        rating: Optional[float] = None,
        success: Optional[bool] = None,
        response_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an agent interaction for feedback analysis.

        Args:
            agent_name: Name of the agent
            task: The task or input
            response: The agent's response
            rating: Optional rating (0-5)
            success: Optional success indicator
            response_time: Optional response time in seconds
            metadata: Optional additional metadata
        """
        interaction = {
            "task": task,
            "response": response,
            "rating": rating,
            "success": success,
            "response_time": response_time,
            "metadata": metadata or {},
        }

        self.interaction_history[agent_name].append(interaction)
        self._update_metrics(agent_name, interaction)

        # Trigger callbacks
        for callback in self.feedback_callbacks:
            callback(agent_name, interaction)

    def _update_metrics(self, agent_name: str, interaction: Dict[str, Any]) -> None:
        """Update performance metrics for an agent."""
        metrics = self.performance_metrics[agent_name]
        history = self.interaction_history[agent_name]

        metrics["total_interactions"] = len(history)

        # Update average rating
        ratings = [i["rating"] for i in history if i["rating"] is not None]
        if ratings:
            metrics["avg_rating"] = sum(ratings) / len(ratings)

        # Update success rate
        successes = [i["success"] for i in history if i["success"] is not None]
        if successes:
            metrics["success_rate"] = sum(successes) / len(successes)

        # Update average response time
        times = [i["response_time"] for i in history if i["response_time"] is not None]
        if times:
            metrics["avg_response_time"] = sum(times) / len(times)

    def get_performance_metrics(self, agent_name: str) -> Dict[str, float]:
        """Get performance metrics for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary of performance metrics
        """
        return dict(self.performance_metrics[agent_name])

    def get_improvement_suggestions(
        self,
        agent_name: str,
        min_interactions: int = 5,
    ) -> List[str]:
        """Generate improvement suggestions based on feedback.

        Args:
            agent_name: Name of the agent
            min_interactions: Minimum interactions needed for suggestions

        Returns:
            List of improvement suggestions
        """
        history = self.interaction_history[agent_name]
        if len(history) < min_interactions:
            return ["Not enough data for suggestions (need at least {min_interactions} interactions)"]

        metrics = self.performance_metrics[agent_name]
        suggestions = []

        # Analyze ratings
        if metrics["avg_rating"] < 3.0:
            suggestions.append("Low average rating - consider reviewing response quality and relevance")

        # Analyze success rate
        if metrics["success_rate"] < 0.7:
            suggestions.append("Low success rate - review task understanding and execution")

        # Analyze response time
        if metrics["avg_response_time"] > 5.0:
            suggestions.append("Slow response time - optimize processing or use faster models")

        # Analyze recent trend
        recent = history[-5:]
        recent_ratings = [i["rating"] for i in recent if i["rating"] is not None]
        if len(recent_ratings) >= 3:
            avg_recent = sum(recent_ratings) / len(recent_ratings)
            if avg_recent < metrics["avg_rating"] - 0.5:
                suggestions.append("Recent performance decline detected - investigate recent changes")

        # Analyze common failure patterns
        failures = [i for i in history if i.get("success") is False]
        if len(failures) > len(history) * 0.3:
            suggestions.append("High failure rate on specific task types - consider specialized training")

        if not suggestions:
            suggestions.append("Performance is good - continue current approach")

        return suggestions

    def get_interaction_history(
        self,
        agent_name: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get interaction history for an agent.

        Args:
            agent_name: Name of the agent
            limit: Optional limit on number of interactions to return

        Returns:
            List of interaction records
        """
        history = self.interaction_history[agent_name]
        if limit:
            return history[-limit:]
        return history

    def add_feedback_callback(self, callback: Callable) -> None:
        """Add a callback function triggered on each interaction.

        Args:
            callback: Function that takes (agent_name, interaction) as arguments
        """
        self.feedback_callbacks.append(callback)

    def get_comparative_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get comparative metrics across all agents.

        Returns:
            Dictionary mapping agent names to their metrics
        """
        return {
            name: dict(metrics)
            for name, metrics in self.performance_metrics.items()
        }

    def reset_agent_metrics(self, agent_name: str) -> None:
        """Reset metrics for a specific agent.

        Args:
            agent_name: Name of the agent
        """
        self.interaction_history[agent_name] = []
        self.performance_metrics[agent_name] = {
            "avg_rating": 0.0,
            "total_interactions": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
        }
