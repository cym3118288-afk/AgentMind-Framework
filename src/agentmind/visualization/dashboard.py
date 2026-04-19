"""Interactive dashboard for AgentMind using Gradio."""

import asyncio
from typing import Any, Dict, List, Optional, Tuple

from ..core.agent import Agent
from ..core.mind import AgentMind
from ..core.types import Message
from .visualizer import MemoryVisualizer, MessageFlowVisualizer


class Dashboard:
    """Interactive dashboard for monitoring and debugging AgentMind.

    Provides real-time visualization of agent collaboration, memory inspection,
    and interactive task execution.

    Example:
        >>> dashboard = Dashboard(mind)
        >>> dashboard.launch()
    """

    def __init__(self, mind: Optional[AgentMind] = None):
        """Initialize the dashboard.

        Args:
            mind: Optional AgentMind instance to monitor
        """
        self.mind = mind
        self.message_visualizer = MessageFlowVisualizer()
        self.memory_visualizer = MemoryVisualizer()
        self.collaboration_history: List[Dict[str, Any]] = []

    def set_mind(self, mind: AgentMind) -> None:
        """Set the AgentMind instance to monitor.

        Args:
            mind: AgentMind instance
        """
        self.mind = mind

    async def run_collaboration(
        self,
        task: str,
        max_rounds: int = 3,
    ) -> Tuple[str, str, str]:
        """Run a collaboration task and update visualizations.

        Args:
            task: Task description
            max_rounds: Maximum collaboration rounds

        Returns:
            Tuple of (result, message_flow, memory_summary)
        """
        if not self.mind:
            return "No AgentMind instance configured", "", ""

        # Clear visualizers
        self.message_visualizer.clear()

        # Run collaboration
        result = await self.mind.collaborate(task, max_rounds=max_rounds)

        # Update visualizations
        if hasattr(self.mind, "conversation_history"):
            for msg in self.mind.conversation_history:
                self.message_visualizer.add_message(msg)

        # Update memory visualizations
        for agent in self.mind.agents:
            if hasattr(agent, "memory"):
                self.memory_visualizer.update_agent_memory(agent.name, agent.memory)

        # Store in history
        self.collaboration_history.append({
            "task": task,
            "result": result,
            "rounds": max_rounds,
        })

        # Generate visualizations
        message_flow = self.message_visualizer.get_flow_diagram()
        memory_summary = self.memory_visualizer.get_all_memories_summary()

        return result, message_flow, memory_summary

    def get_agent_info(self) -> str:
        """Get information about configured agents.

        Returns:
            String with agent information
        """
        if not self.mind or not self.mind.agents:
            return "No agents configured"

        lines = ["Configured Agents:", "=" * 60]

        for agent in self.mind.agents:
            lines.append(f"\nName: {agent.name}")
            lines.append(f"Role: {agent.role}")
            lines.append(f"Active: {agent.is_active}")
            if hasattr(agent, "memory"):
                lines.append(f"Memory size: {len(agent.memory)}")

        return "\n".join(lines)

    def get_statistics(self) -> str:
        """Get dashboard statistics.

        Returns:
            String with statistics
        """
        lines = ["Dashboard Statistics:", "=" * 60]

        lines.append(f"\nTotal collaborations: {len(self.collaboration_history)}")

        if self.mind:
            lines.append(f"Active agents: {len(self.mind.agents)}")
            lines.append(f"Strategy: {self.mind.strategy.value if hasattr(self.mind.strategy, 'value') else self.mind.strategy}")

        msg_stats = self.message_visualizer.get_statistics()
        if msg_stats:
            lines.append(f"\nTotal messages: {msg_stats.get('total_messages', 0)}")
            lines.append(f"Unique senders: {msg_stats.get('unique_senders', 0)}")

        mem_stats = self.memory_visualizer.get_memory_statistics()
        if mem_stats:
            lines.append(f"\nTotal agents with memory: {mem_stats.get('total_agents', 0)}")
            lines.append(f"Total messages in memory: {mem_stats.get('total_messages', 0)}")

        return "\n".join(lines)

    def get_collaboration_history(self) -> str:
        """Get collaboration history.

        Returns:
            String with collaboration history
        """
        if not self.collaboration_history:
            return "No collaboration history"

        lines = ["Collaboration History:", "=" * 60]

        for i, collab in enumerate(self.collaboration_history, 1):
            lines.append(f"\n{i}. Task: {collab['task'][:60]}...")
            lines.append(f"   Rounds: {collab['rounds']}")
            lines.append(f"   Result: {collab['result'][:100]}...")

        return "\n".join(lines)


def launch_dashboard(mind: Optional[AgentMind] = None, share: bool = False) -> None:
    """Launch the Gradio dashboard.

    Args:
        mind: Optional AgentMind instance to monitor
        share: Whether to create a public link

    Note:
        Requires gradio to be installed: pip install gradio
    """
    try:
        import gradio as gr
    except ImportError:
        print("Gradio not installed. Install with: pip install gradio")
        return

    dashboard = Dashboard(mind)

    def run_task(task: str, max_rounds: int) -> Tuple[str, str, str, str]:
        """Wrapper for running tasks in Gradio."""
        if not task:
            return "Please enter a task", "", "", ""

        result, flow, memory = asyncio.run(
            dashboard.run_collaboration(task, max_rounds)
        )
        stats = dashboard.get_statistics()
        return result, flow, memory, stats

    def get_info() -> Tuple[str, str]:
        """Get dashboard info."""
        agent_info = dashboard.get_agent_info()
        history = dashboard.get_collaboration_history()
        return agent_info, history

    # Create Gradio interface
    with gr.Blocks(title="AgentMind Dashboard") as demo:
        gr.Markdown("# AgentMind Dashboard")
        gr.Markdown("Monitor and interact with your multi-agent system")

        with gr.Tab("Collaboration"):
            with gr.Row():
                with gr.Column():
                    task_input = gr.Textbox(
                        label="Task",
                        placeholder="Enter a task for the agents...",
                        lines=3,
                    )
                    rounds_input = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=3,
                        step=1,
                        label="Max Rounds",
                    )
                    run_button = gr.Button("Run Collaboration", variant="primary")

                with gr.Column():
                    result_output = gr.Textbox(
                        label="Result",
                        lines=10,
                        interactive=False,
                    )

            with gr.Row():
                with gr.Column():
                    flow_output = gr.Textbox(
                        label="Message Flow",
                        lines=10,
                        interactive=False,
                    )
                with gr.Column():
                    memory_output = gr.Textbox(
                        label="Memory Summary",
                        lines=10,
                        interactive=False,
                    )

            stats_output = gr.Textbox(
                label="Statistics",
                lines=5,
                interactive=False,
            )

            run_button.click(
                fn=run_task,
                inputs=[task_input, rounds_input],
                outputs=[result_output, flow_output, memory_output, stats_output],
            )

        with gr.Tab("Agents"):
            agent_info_output = gr.Textbox(
                label="Agent Information",
                lines=15,
                interactive=False,
            )
            refresh_agents_button = gr.Button("Refresh")
            refresh_agents_button.click(
                fn=lambda: dashboard.get_agent_info(),
                outputs=agent_info_output,
            )

        with gr.Tab("History"):
            history_output = gr.Textbox(
                label="Collaboration History",
                lines=20,
                interactive=False,
            )
            refresh_history_button = gr.Button("Refresh")
            refresh_history_button.click(
                fn=lambda: dashboard.get_collaboration_history(),
                outputs=history_output,
            )

        with gr.Tab("Statistics"):
            stats_detail_output = gr.Textbox(
                label="Detailed Statistics",
                lines=20,
                interactive=False,
            )
            refresh_stats_button = gr.Button("Refresh")
            refresh_stats_button.click(
                fn=lambda: dashboard.get_statistics(),
                outputs=stats_detail_output,
            )

    demo.launch(share=share)
