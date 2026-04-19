"""Example: Using the plugin system with Slack integration.

This example demonstrates how to use AgentMind's plugin system
to integrate with Slack for agent communication.
"""

import asyncio
import os

from agentmind import Agent, AgentMind
from agentmind.llm import LiteLLMProvider
from agentmind.plugins import PluginManager


async def example_basic_slack():
    """Basic Slack integration example."""
    print("=== Basic Slack Integration ===\n")

    # Initialize plugin manager
    manager = PluginManager()

    # Discover and register plugins
    manager.discover_and_load()

    # Load Slack plugin
    slack_config = {
        "token": os.getenv("SLACK_BOT_TOKEN"),
        "channel": os.getenv("SLACK_CHANNEL_ID")
    }

    success = await manager.load_plugin("slack", slack_config)
    if not success:
        print("Failed to load Slack plugin")
        return

    # Get plugin instance
    slack = manager.get_plugin("slack")

    # Connect to Slack
    await slack.connect()

    # Send a message
    response = await slack.send_message("Hello from AgentMind!")
    print(f"Message sent: {response['ts']}\n")

    # Unload plugin
    await manager.unload_plugin("slack")


async def example_agent_with_slack():
    """Agent that communicates via Slack."""
    print("=== Agent with Slack Integration ===\n")

    # Initialize components
    llm = LiteLLMProvider(model="gpt-4")
    mind = AgentMind(llm_provider=llm)

    # Create agent
    assistant = Agent(
        name="SlackAssistant",
        role="assistant",
        system_prompt="You are a helpful assistant that responds via Slack."
    )
    mind.add_agent(assistant)

    # Initialize plugin manager
    manager = PluginManager()
    manager.discover_and_load()

    slack_config = {
        "token": os.getenv("SLACK_BOT_TOKEN"),
        "channel": os.getenv("SLACK_CHANNEL_ID")
    }

    await manager.load_plugin("slack", slack_config)
    slack = manager.get_plugin("slack")
    await slack.connect()

    # Get recent messages from Slack
    messages = await slack.get_channel_history(slack_config["channel"], limit=10)

    # Process latest message
    if messages:
        latest = messages[0]
        user_message = latest.get("text", "")

        if user_message and not latest.get("bot_id"):
            print(f"User message: {user_message}")

            # Generate response with agent
            result = await mind.collaborate(user_message, max_rounds=1)
            response = result.final_output

            print(f"Agent response: {response}")

            # Send response to Slack
            await slack.send_message(response)

            # Add reaction to original message
            await slack.add_reaction(
                slack_config["channel"],
                latest["ts"],
                "white_check_mark"
            )

    await manager.unload_plugin("slack")


async def example_slack_bot():
    """Full Slack bot with multiple agents."""
    print("=== Slack Bot with Multiple Agents ===\n")

    # Initialize LLM and agents
    llm = LiteLLMProvider(model="gpt-4")
    mind = AgentMind(llm_provider=llm)

    # Create specialized agents
    greeter = Agent(
        name="Greeter",
        role="greeting",
        system_prompt="You greet users warmly and professionally."
    )

    helper = Agent(
        name="Helper",
        role="assistance",
        system_prompt="You provide helpful information and assistance."
    )

    mind.add_agent(greeter)
    mind.add_agent(helper)

    # Setup Slack plugin
    manager = PluginManager()
    manager.discover_and_load()

    slack_config = {
        "token": os.getenv("SLACK_BOT_TOKEN"),
        "channel": os.getenv("SLACK_CHANNEL_ID")
    }

    await manager.load_plugin("slack", slack_config)
    slack = manager.get_plugin("slack")
    await slack.connect()

    # Send greeting
    greeting_result = await mind.collaborate(
        "Generate a friendly greeting for the team",
        max_rounds=1
    )
    await slack.send_message(greeting_result.final_output)

    # List available commands
    commands_message = """
    *Available Commands:*
    • `help` - Show this help message
    • `ask <question>` - Ask the assistant a question
    • `status` - Check bot status
    """
    await slack.send_message(commands_message)

    await manager.unload_plugin("slack")


async def example_slack_rich_messages():
    """Send rich messages with Slack blocks."""
    print("=== Slack Rich Messages ===\n")

    manager = PluginManager()
    manager.discover_and_load()

    slack_config = {
        "token": os.getenv("SLACK_BOT_TOKEN"),
        "channel": os.getenv("SLACK_CHANNEL_ID")
    }

    await manager.load_plugin("slack", slack_config)
    slack = manager.get_plugin("slack")
    await slack.connect()

    # Create rich message with blocks
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "AgentMind Status Report"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Status:* All systems operational"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Active Agents:* 3"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Tasks Completed:* 42"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Need help? Type `@agentmind help`"
            }
        }
    ]

    await slack.send_rich_message(
        slack_config["channel"],
        blocks,
        text="AgentMind Status Report"
    )

    await manager.unload_plugin("slack")


async def example_slack_file_upload():
    """Upload files to Slack."""
    print("=== Slack File Upload ===\n")

    manager = PluginManager()
    manager.discover_and_load()

    slack_config = {
        "token": os.getenv("SLACK_BOT_TOKEN"),
        "channel": os.getenv("SLACK_CHANNEL_ID")
    }

    await manager.load_plugin("slack", slack_config)
    slack = manager.get_plugin("slack")
    await slack.connect()

    # Upload a file
    file_path = "report.txt"
    if os.path.exists(file_path):
        await slack.upload_file(
            file_path,
            slack_config["channel"],
            title="Agent Report",
            comment="Here's the latest report from AgentMind"
        )
        print(f"Uploaded {file_path} to Slack")
    else:
        print(f"File not found: {file_path}")

    await manager.unload_plugin("slack")


async def example_list_channels():
    """List all Slack channels."""
    print("=== List Slack Channels ===\n")

    manager = PluginManager()
    manager.discover_and_load()

    slack_config = {
        "token": os.getenv("SLACK_BOT_TOKEN")
    }

    await manager.load_plugin("slack", slack_config)
    slack = manager.get_plugin("slack")
    await slack.connect()

    # List channels
    channels = await slack.list_channels()
    print("Available channels:")
    for channel in channels:
        print(f"  - {channel['name']} (ID: {channel['id']})")

    await manager.unload_plugin("slack")


async def main():
    """Run all examples."""
    print("Slack Plugin Examples\n")
    print("=" * 50 + "\n")

    print("Note: Set SLACK_BOT_TOKEN and SLACK_CHANNEL_ID environment variables.\n")

    # Check if credentials are available
    if not os.getenv("SLACK_BOT_TOKEN"):
        print("SLACK_BOT_TOKEN not set. Skipping examples.")
        return

    # Uncomment to run examples
    # await example_basic_slack()
    # await example_agent_with_slack()
    # await example_slack_bot()
    # await example_slack_rich_messages()
    # await example_slack_file_upload()
    # await example_list_channels()


if __name__ == "__main__":
    asyncio.run(main())
