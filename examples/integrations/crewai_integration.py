"""
CrewAI Integration Example

This example demonstrates integration between AgentMind and CrewAI:
- Converting CrewAI crews to AgentMind teams
- Task-based workflows
- Role-based agent collaboration
- Process orchestration

Note: This is a compatibility example. Install crewai with:
pip install crewai
"""

import asyncio
from typing import Dict, List, Any, Optional
from enum import Enum
from agentmind import Agent, AgentMind, Message
from agentmind.llm import OllamaProvider


class ProcessType(str, Enum):
    """CrewAI-style process types"""
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"
    CONSENSUS = "consensus"


class Task:
    """CrewAI-style task"""

    def __init__(
        self,
        description: str,
        agent: Optional['CrewAgent'] = None,
        expected_output: Optional[str] = None,
        context: Optional[List['Task']] = None
    ):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
        self.context = context or []
        self.output: Optional[str] = None
        self.completed = False

    async def execute(self) -> str:
        """Execute the task"""
        if not self.agent:
            raise ValueError("Task must have an assigned agent")

        # Build context from previous tasks
        context_text = ""
        if self.context:
            context_text = "\n\nContext from previous tasks:\n"
            for task in self.context:
                if task.output:
                    context_text += f"- {task.output[:100]}...\n"

        # Execute task
        full_description = self.description + context_text
        message = Message(content=full_description, sender="crew", role="user")
        response = await self.agent.process_message(message)

        self.output = response.content
        self.completed = True
        return self.output


class CrewAgent(Agent):
    """AgentMind agent with CrewAI-style interface"""

    def __init__(
        self,
        *args,
        role: str,
        goal: str,
        backstory: str,
        verbose: bool = False,
        **kwargs
    ):
        super().__init__(*args, role=role, **kwargs)
        self.goal = goal
        self.backstory = backstory
        self.verbose = verbose
        self.tasks_completed = 0

    async def execute_task(self, task: Task) -> str:
        """Execute a CrewAI-style task"""
        if self.verbose:
            print(f"\n[{self.name}] Starting task: {task.description[:50]}...")

        result = await task.execute()
        self.tasks_completed += 1

        if self.verbose:
            print(f"[{self.name}] Completed task. Output: {result[:100]}...")

        return result

    def get_profile(self) -> Dict[str, Any]:
        """Get agent profile"""
        return {
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory,
            "tasks_completed": self.tasks_completed
        }


class Crew:
    """CrewAI-style crew"""

    def __init__(
        self,
        agents: List[CrewAgent],
        tasks: List[Task],
        process: ProcessType = ProcessType.SEQUENTIAL,
        verbose: bool = False
    ):
        self.agents = agents
        self.tasks = tasks
        self.process = process
        self.verbose = verbose
        self.results: List[str] = []

    async def kickoff(self) -> Dict[str, Any]:
        """Start the crew's work"""
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Starting Crew with {len(self.agents)} agents")
            print(f"Process: {self.process.value}")
            print(f"Tasks: {len(self.tasks)}")
            print(f"{'='*60}\n")

        if self.process == ProcessType.SEQUENTIAL:
            return await self._sequential_process()
        elif self.process == ProcessType.HIERARCHICAL:
            return await self._hierarchical_process()
        else:
            return await self._consensus_process()

    async def _sequential_process(self) -> Dict[str, Any]:
        """Execute tasks sequentially"""
        for i, task in enumerate(self.tasks):
            if self.verbose:
                print(f"\nTask {i+1}/{len(self.tasks)}: {task.description[:50]}...")

            # Assign agent if not already assigned
            if not task.agent:
                task.agent = self.agents[i % len(self.agents)]

            # Execute task
            result = await task.agent.execute_task(task)
            self.results.append(result)

        return {
            "process": self.process.value,
            "tasks_completed": len(self.tasks),
            "final_output": self.results[-1] if self.results else "",
            "all_outputs": self.results
        }

    async def _hierarchical_process(self) -> Dict[str, Any]:
        """Execute tasks hierarchically"""
        # Manager is first agent
        manager = self.agents[0]
        workers = self.agents[1:]

        # Manager delegates tasks
        for i, task in enumerate(self.tasks):
            worker = workers[i % len(workers)] if workers else manager
            task.agent = worker
            result = await worker.execute_task(task)
            self.results.append(result)

        return {
            "process": self.process.value,
            "manager": manager.name,
            "workers": [w.name for w in workers],
            "tasks_completed": len(self.tasks),
            "final_output": self.results[-1] if self.results else ""
        }

    async def _consensus_process(self) -> Dict[str, Any]:
        """Execute tasks with consensus"""
        for task in self.tasks:
            # All agents work on the task
            outputs = []
            for agent in self.agents:
                task.agent = agent
                result = await agent.execute_task(task)
                outputs.append(result)

            # Combine outputs (simplified consensus)
            task.output = f"Consensus from {len(outputs)} agents: " + outputs[0]
            self.results.append(task.output)

        return {
            "process": self.process.value,
            "consensus_rounds": len(self.tasks),
            "final_output": self.results[-1] if self.results else ""
        }


async def example_1_basic_crew():
    """Example 1: Basic CrewAI-style crew"""
    print("\n=== Example 1: Basic Crew ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create agents
    researcher = CrewAgent(
        name="researcher",
        role="researcher",
        goal="Research and gather information",
        backstory="Expert researcher with years of experience",
        llm_provider=llm,
        verbose=True
    )

    writer = CrewAgent(
        name="writer",
        role="writer",
        goal="Write compelling content",
        backstory="Professional writer with strong communication skills",
        llm_provider=llm,
        verbose=True
    )

    # Create tasks
    tasks = [
        Task(
            description="Research the benefits of renewable energy",
            agent=researcher,
            expected_output="Comprehensive research summary"
        ),
        Task(
            description="Write an article based on the research",
            agent=writer,
            expected_output="Well-written article"
        )
    ]

    # Link tasks
    tasks[1].context = [tasks[0]]

    # Create crew
    crew = Crew(
        agents=[researcher, writer],
        tasks=tasks,
        process=ProcessType.SEQUENTIAL,
        verbose=True
    )

    # Execute
    result = await crew.kickoff()
    print(f"\nCrew completed {result['tasks_completed']} tasks")


async def example_2_hierarchical_crew():
    """Example 2: Hierarchical crew"""
    print("\n=== Example 2: Hierarchical Crew ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create hierarchical team
    manager = CrewAgent(
        name="manager",
        role="project_manager",
        goal="Coordinate team and ensure quality",
        backstory="Experienced project manager",
        llm_provider=llm
    )

    developer = CrewAgent(
        name="developer",
        role="developer",
        goal="Write high-quality code",
        backstory="Senior software developer",
        llm_provider=llm
    )

    tester = CrewAgent(
        name="tester",
        role="qa_engineer",
        goal="Ensure software quality",
        backstory="Quality assurance specialist",
        llm_provider=llm
    )

    # Create tasks
    tasks = [
        Task(description="Design the system architecture"),
        Task(description="Implement the core features"),
        Task(description="Test the implementation")
    ]

    # Create hierarchical crew
    crew = Crew(
        agents=[manager, developer, tester],
        tasks=tasks,
        process=ProcessType.HIERARCHICAL,
        verbose=True
    )

    result = await crew.kickoff()
    print(f"\nManager: {result['manager']}")
    print(f"Workers: {', '.join(result['workers'])}")


async def example_3_task_dependencies():
    """Example 3: Tasks with dependencies"""
    print("\n=== Example 3: Task Dependencies ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create agents
    analyst = CrewAgent(
        name="analyst",
        role="analyst",
        goal="Analyze data and trends",
        backstory="Data analyst",
        llm_provider=llm
    )

    strategist = CrewAgent(
        name="strategist",
        role="strategist",
        goal="Develop strategies",
        backstory="Business strategist",
        llm_provider=llm
    )

    # Create dependent tasks
    task1 = Task(
        description="Analyze market trends",
        agent=analyst
    )

    task2 = Task(
        description="Develop market entry strategy",
        agent=strategist,
        context=[task1]  # Depends on task1
    )

    crew = Crew(
        agents=[analyst, strategist],
        tasks=[task1, task2],
        process=ProcessType.SEQUENTIAL
    )

    result = await crew.kickoff()
    print(f"Completed workflow with {result['tasks_completed']} dependent tasks\n")


async def example_4_crewai_to_agentmind():
    """Example 4: Converting CrewAI to AgentMind"""
    print("\n=== Example 4: CrewAI to AgentMind ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create CrewAI-style agents
    crew_agents = [
        CrewAgent(
            name="agent1",
            role="researcher",
            goal="Research topics",
            backstory="Researcher",
            llm_provider=llm
        ),
        CrewAgent(
            name="agent2",
            role="writer",
            goal="Write content",
            backstory="Writer",
            llm_provider=llm
        )
    ]

    # Use with AgentMind orchestration
    mind = AgentMind(strategy="round_robin")
    for agent in crew_agents:
        mind.add_agent(agent)

    result = await mind.start_collaboration(
        "Research and write about AI trends",
        max_rounds=2
    )

    print("Using AgentMind orchestration with CrewAI-style agents:")
    print(f"Result: {result.final_output[:200]}...\n")


async def example_5_crew_profiles():
    """Example 5: Agent profiles and statistics"""
    print("\n=== Example 5: Crew Profiles ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create crew
    agents = [
        CrewAgent(
            name="specialist",
            role="specialist",
            goal="Provide expert analysis",
            backstory="Domain expert with 10 years experience",
            llm_provider=llm
        )
    ]

    # Show profile
    profile = agents[0].get_profile()
    print("Agent Profile:")
    print(f"  Name: {profile['name']}")
    print(f"  Role: {profile['role']}")
    print(f"  Goal: {profile['goal']}")
    print(f"  Backstory: {profile['backstory']}")
    print(f"  Tasks completed: {profile['tasks_completed']}\n")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("CrewAI Integration Example")
    print("=" * 60)

    await example_1_basic_crew()
    await example_2_hierarchical_crew()
    await example_3_task_dependencies()
    await example_4_crewai_to_agentmind()
    await example_5_crew_profiles()

    print("\n" + "=" * 60)
    print("Example Complete!")
    print("=" * 60)
    print("\nKey Concepts:")
    print("1. CrewAI-style crews work with AgentMind")
    print("2. Task-based workflows enable structured collaboration")
    print("3. Multiple process types: sequential, hierarchical, consensus")
    print("4. Task dependencies create complex workflows")
    print("5. Agent profiles define roles and capabilities")


if __name__ == "__main__":
    asyncio.run(main())
