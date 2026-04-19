"""Parallel task decomposition for multi-agent systems."""

import asyncio
from typing import Any, Dict, List, Optional

from ..core.agent import Agent
from ..core.types import Message, MessageRole
from ..llm.provider import LLMProvider


class ParallelTaskDecomposer:
    """Decomposes complex tasks into parallel subtasks.

    Analyzes tasks and creates independent subtasks that can be executed
    concurrently by different agents.

    Example:
        >>> decomposer = ParallelTaskDecomposer(llm_provider)
        >>> subtasks = await decomposer.decompose(
        ...     "Research and write a report on AI trends"
        ... )
        >>> results = await decomposer.execute_parallel(subtasks, agents)
    """

    def __init__(self, llm_provider: LLMProvider):
        """Initialize the task decomposer.

        Args:
            llm_provider: LLM provider for task analysis
        """
        self.llm_provider = llm_provider
        self.decomposition_history: List[Dict[str, Any]] = []

    async def decompose(
        self,
        task: str,
        max_subtasks: int = 5,
        min_subtasks: int = 2,
    ) -> List[Dict[str, Any]]:
        """Decompose a task into parallel subtasks.

        Args:
            task: Main task to decompose
            max_subtasks: Maximum number of subtasks
            min_subtasks: Minimum number of subtasks

        Returns:
            List of subtask specifications
        """
        decomposition_prompt = f"""Decompose this task into {min_subtasks}-{max_subtasks} independent subtasks that can be executed in parallel:

Task: {task}

For each subtask, provide:
1. A clear description
2. Dependencies (if any)
3. Estimated complexity (low/medium/high)

Format each subtask as:
SUBTASK: [description]
DEPENDENCIES: [none or list of other subtasks]
COMPLEXITY: [low/medium/high]

Ensure subtasks are as independent as possible for parallel execution."""

        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="You are a task decomposition expert who breaks down complex tasks into parallelizable subtasks.",
                sender="system",
            ),
            Message(
                role=MessageRole.USER,
                content=decomposition_prompt,
                sender="decomposer",
            ),
        ]

        response = await self.llm_provider.generate(messages)
        subtasks = self._parse_subtasks(response.content)

        # Store in history
        self.decomposition_history.append({
            "original_task": task,
            "subtasks": subtasks,
            "count": len(subtasks),
        })

        return subtasks

    def _parse_subtasks(self, response: str) -> List[Dict[str, Any]]:
        """Parse subtasks from response.

        Args:
            response: Decomposition response

        Returns:
            List of subtask specifications
        """
        subtasks = []
        current_subtask = {}

        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()

            if line.startswith("SUBTASK:"):
                if current_subtask:
                    subtasks.append(current_subtask)
                current_subtask = {
                    "description": line.replace("SUBTASK:", "").strip(),
                    "dependencies": [],
                    "complexity": "medium",
                }
            elif line.startswith("DEPENDENCIES:"):
                deps_text = line.replace("DEPENDENCIES:", "").strip().lower()
                if deps_text != "none":
                    current_subtask["dependencies"] = [
                        d.strip() for d in deps_text.split(",")
                    ]
            elif line.startswith("COMPLEXITY:"):
                current_subtask["complexity"] = line.replace("COMPLEXITY:", "").strip().lower()

        if current_subtask:
            subtasks.append(current_subtask)

        return subtasks

    async def execute_parallel(
        self,
        subtasks: List[Dict[str, Any]],
        agents: List[Agent],
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute subtasks in parallel using available agents.

        Args:
            subtasks: List of subtask specifications
            agents: List of agents to execute subtasks
            timeout: Optional timeout for execution

        Returns:
            Dictionary with execution results
        """
        if not agents:
            return {"error": "No agents available"}

        # Assign subtasks to agents
        assignments = self._assign_subtasks(subtasks, agents)

        # Execute in parallel
        tasks = []
        for agent, subtask in assignments:
            task = self._execute_subtask(agent, subtask, timeout)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile results
        execution_results = {
            "total_subtasks": len(subtasks),
            "completed": sum(1 for r in results if not isinstance(r, Exception)),
            "failed": sum(1 for r in results if isinstance(r, Exception)),
            "results": [],
        }

        for i, (agent, subtask) in enumerate(assignments):
            result = results[i]
            execution_results["results"].append({
                "agent": agent.name,
                "subtask": subtask["description"],
                "success": not isinstance(result, Exception),
                "result": str(result) if isinstance(result, Exception) else result,
            })

        return execution_results

    def _assign_subtasks(
        self,
        subtasks: List[Dict[str, Any]],
        agents: List[Agent],
    ) -> List[tuple]:
        """Assign subtasks to agents.

        Args:
            subtasks: List of subtasks
            agents: List of agents

        Returns:
            List of (agent, subtask) tuples
        """
        assignments = []

        # Simple round-robin assignment
        for i, subtask in enumerate(subtasks):
            agent = agents[i % len(agents)]
            assignments.append((agent, subtask))

        return assignments

    async def _execute_subtask(
        self,
        agent: Agent,
        subtask: Dict[str, Any],
        timeout: Optional[float],
    ) -> str:
        """Execute a single subtask.

        Args:
            agent: Agent to execute the subtask
            subtask: Subtask specification
            timeout: Optional timeout

        Returns:
            Subtask result
        """
        message = Message(
            role=MessageRole.USER,
            content=subtask["description"],
            sender="task_decomposer",
        )

        if timeout:
            response = await asyncio.wait_for(
                agent.process_message(message),
                timeout=timeout,
            )
        else:
            response = await agent.process_message(message)

        return response.content if response else "No response"

    async def decompose_and_execute(
        self,
        task: str,
        agents: List[Agent],
        max_subtasks: int = 5,
    ) -> Dict[str, Any]:
        """Decompose and execute a task in one call.

        Args:
            task: Task to decompose and execute
            agents: Agents to use for execution
            max_subtasks: Maximum number of subtasks

        Returns:
            Execution results
        """
        # Decompose
        subtasks = await self.decompose(task, max_subtasks)

        # Execute
        results = await self.execute_parallel(subtasks, agents)

        return {
            "task": task,
            "subtasks": subtasks,
            "execution": results,
        }

    def get_dependency_graph(self, subtasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build a dependency graph from subtasks.

        Args:
            subtasks: List of subtasks

        Returns:
            Dictionary mapping subtask indices to their dependencies
        """
        graph = {}

        for i, subtask in enumerate(subtasks):
            deps = subtask.get("dependencies", [])
            graph[str(i)] = deps

        return graph

    def get_execution_order(self, subtasks: List[Dict[str, Any]]) -> List[List[int]]:
        """Determine execution order respecting dependencies.

        Args:
            subtasks: List of subtasks

        Returns:
            List of execution waves (each wave can run in parallel)
        """
        # Simple topological sort
        remaining = set(range(len(subtasks)))
        waves = []

        while remaining:
            # Find subtasks with no dependencies in remaining set
            wave = []
            for i in remaining:
                deps = subtasks[i].get("dependencies", [])
                # Check if all dependencies are satisfied
                if not deps or all(d not in remaining for d in deps):
                    wave.append(i)

            if not wave:
                # Circular dependency or error - add all remaining
                wave = list(remaining)

            waves.append(wave)
            remaining -= set(wave)

        return waves

    def get_decomposition_history(self) -> List[Dict[str, Any]]:
        """Get history of task decompositions.

        Returns:
            List of decomposition records
        """
        return self.decomposition_history
