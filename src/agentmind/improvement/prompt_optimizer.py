"""Prompt optimization for agent self-improvement.

Agents can generate and optimize their own role prompts based on performance feedback.
"""

from typing import Any, Dict, List, Optional

from ..core.types import Message, MessageRole
from ..llm.provider import LLMProvider


class PromptOptimizer:
    """Optimizes agent prompts based on performance and feedback.

    This class helps agents improve their system prompts by analyzing
    their performance on tasks and generating better prompts.

    Example:
        >>> optimizer = PromptOptimizer(llm_provider)
        >>> new_prompt = await optimizer.optimize_prompt(
        ...     current_prompt="You are a helpful assistant",
        ...     task_examples=[...],
        ...     feedback=["Be more concise", "Add technical depth"]
        ... )
    """

    def __init__(self, llm_provider: LLMProvider):
        """Initialize the prompt optimizer.

        Args:
            llm_provider: LLM provider for generating optimized prompts
        """
        self.llm_provider = llm_provider
        self.optimization_history: List[Dict[str, Any]] = []

    async def optimize_prompt(
        self,
        current_prompt: str,
        task_examples: List[Dict[str, str]],
        feedback: Optional[List[str]] = None,
        performance_metrics: Optional[Dict[str, float]] = None,
    ) -> str:
        """Generate an optimized version of the current prompt.

        Args:
            current_prompt: The current system prompt to optimize
            task_examples: Examples of tasks and responses
            feedback: Optional list of feedback comments
            performance_metrics: Optional performance metrics (accuracy, speed, etc.)

        Returns:
            Optimized system prompt
        """
        optimization_request = self._build_optimization_request(
            current_prompt, task_examples, feedback, performance_metrics
        )

        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="You are a prompt engineering expert. Optimize prompts for better performance.",
                sender="system",
            ),
            Message(
                role=MessageRole.USER,
                content=optimization_request,
                sender="optimizer",
            ),
        ]

        response = await self.llm_provider.generate(messages)
        optimized_prompt = self._extract_prompt(response.content)

        # Store in history
        self.optimization_history.append({
            "original": current_prompt,
            "optimized": optimized_prompt,
            "feedback": feedback,
            "metrics": performance_metrics,
        })

        return optimized_prompt

    def _build_optimization_request(
        self,
        current_prompt: str,
        task_examples: List[Dict[str, str]],
        feedback: Optional[List[str]],
        performance_metrics: Optional[Dict[str, float]],
    ) -> str:
        """Build the optimization request message."""
        request = f"""Optimize the following agent prompt based on the provided information.

Current Prompt:
{current_prompt}

Task Examples:
"""
        for i, example in enumerate(task_examples[:5], 1):
            request += f"\nExample {i}:\n"
            request += f"Task: {example.get('task', 'N/A')}\n"
            request += f"Response: {example.get('response', 'N/A')}\n"

        if feedback:
            request += "\n\nFeedback:\n"
            for item in feedback:
                request += f"- {item}\n"

        if performance_metrics:
            request += "\n\nPerformance Metrics:\n"
            for metric, value in performance_metrics.items():
                request += f"- {metric}: {value}\n"

        request += """

Generate an improved system prompt that:
1. Addresses the feedback points
2. Improves performance on similar tasks
3. Maintains clarity and specificity
4. Keeps the core role intact

Return ONLY the optimized prompt, no explanations."""

        return request

    def _extract_prompt(self, response: str) -> str:
        """Extract the optimized prompt from the response."""
        # Remove common wrapper text
        lines = response.strip().split("\n")
        cleaned_lines = []

        for line in lines:
            # Skip meta-commentary
            if line.startswith(("Here", "The optimized", "I've", "This prompt")):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    async def generate_role_prompt(
        self,
        role: str,
        capabilities: List[str],
        constraints: Optional[List[str]] = None,
    ) -> str:
        """Generate a new role prompt from scratch.

        Args:
            role: The role name (e.g., "analyst", "creative")
            capabilities: List of capabilities the agent should have
            constraints: Optional list of constraints or limitations

        Returns:
            Generated system prompt
        """
        request = f"""Generate a system prompt for an AI agent with the following specifications:

Role: {role}

Capabilities:
"""
        for cap in capabilities:
            request += f"- {cap}\n"

        if constraints:
            request += "\nConstraints:\n"
            for constraint in constraints:
                request += f"- {constraint}\n"

        request += """

Create a clear, specific system prompt that defines the agent's behavior, expertise, and communication style.
Return ONLY the system prompt, no explanations."""

        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="You are a prompt engineering expert specializing in agent design.",
                sender="system",
            ),
            Message(
                role=MessageRole.USER,
                content=request,
                sender="optimizer",
            ),
        ]

        response = await self.llm_provider.generate(messages)
        return self._extract_prompt(response.content)

    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Get the history of prompt optimizations.

        Returns:
            List of optimization records
        """
        return self.optimization_history
