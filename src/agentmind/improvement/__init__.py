"""Self-improvement mechanisms for AgentMind agents.

This module provides capabilities for agents to improve their own performance
through prompt optimization, debate-based refinement, and feedback loops.
"""

from .debate import DebateImprover
from .feedback import FeedbackLoop
from .prompt_optimizer import PromptOptimizer

__all__ = ["DebateImprover", "FeedbackLoop", "PromptOptimizer"]
