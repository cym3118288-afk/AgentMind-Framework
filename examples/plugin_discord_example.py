"""Example: Using the plugin system with Discord integration.

This example demonstrates how to use AgentMind's plugin system
to integrate with Discord for agent communication.
"""

import asyncio
import os

from agentmind import Agent, AgentMind
from agentmind.llm import LiteLLMProvider
from agentmind.plugins import PluginManager


async def example_basic_discord():
    """Basic Discord integration example."""
    print("=== Basic Discord Integration ===\n")

    # Initialize plugin manager
    manager = PluginManager()
    manager.discover_and_load()

    # Load Discord plugin
    discord_config = {
        "token": os.getenv("DISCORD_BOT_TOKEN"),
        "guild_id": os.getenv("DISCORD_GUILD_ID"),
    }

    success = await manager.load_plugin("discord", discord_config)
    if not success:
        print("Failed to load Discord plugin")
        return

    # Get plugin instance
    discord = manager.get_plugin("discord")

    # Connect to Discord
    await discord.connect()

    # Send a message
    channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
    if channel_id:
        await discord.send_message("Hello from AgentMind!", channel_id=channel_id)
        print("Message sent to Discord\n")

    # Unload plugin
    await manager.unload_plugin("discord")


async def example_agent_with_discord():
    """Agent that communicates via Discord."""
    print("=== Agent with Discord Integration ===\n")

    # Initialize components
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    # Create agent
    assistant = Agent(
        name="DiscordAssistant",
        role="assistant",
        system_prompt="You are a helpful Discord bot assistant.",
    )
    mind.add_agent(assistant)

    # Initialize plugin manager
    manager = PluginManager()
    manager.discover_and_load()

    discord_config = {
        "token": os.getenv("DISCORD_BOT_TOKEN"),
        "guild_id": os.getenv("DISCORD_GUILD_ID"),
    }

    await manager.load_plugin("discord", discord_config)
    discord = manager.get_plugin("discord")
    await discord.connect()

    channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
    if channel_id:
        # Get recent messages
        messages = await discord.get_channel_messages(channel_id, limit=10)

        # Process latest message
        if messages:
            latest = messages[0]
            if not latest.author.bot:
                user_message = latest.content
                print(f"User message: {user_message}")

                # Generate response with agent
                result = await mind.collaborate(user_message, max_rounds=1)
                response = result.final_output

                print(f"Agent response: {response}")

                # Send response to Discord
                await discord.send_message(response, channel_id=channel_id)

                # Add reaction
                await discord.add_reaction(latest.id, channel_id, "✅")

    await manager.unload_plugin("discord")


async def example_discord_bot():
    """Full Discord bot with multiple agents."""
    print("=== Discord Bot with Multiple Agents ===\n")

    # Initialize LLM and agents
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    # Create specialized agents
    moderator = Agent(
        name="Moderator",
        role="moderation",
        system_prompt="You help moderate Discord servers and enforce rules.",
    )

    helper = Agent(
        name="Helper",
        role="assistance",
        system_prompt="You provide helpful information to Discord users.",
    )

    entertainer = Agent(
        name="Entertainer",
        role="entertainment",
        system_prompt="You engage users with fun facts and jokes.",
    )

    mind.add_agent(moderator)
    mind.add_agent(helper)
    mind.add_agent(entertainer)

    # Setup Discord plugin
    manager = PluginManager()
    manager.discover_and_load()

    discord_config = {
        "token": os.getenv("DISCORD_BOT_TOKEN"),
        "guild_id": os.getenv("DISCORD_GUILD_ID"),
    }

    await manager.load_plugin("discord", discord_config)
    discord = manager.get_plugin("discord")
    await discord.connect()

    channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
    if channel_id:
        # Send welcome message
        welcome_result = await mind.collaborate(
            "Generate a friendly welcome message for a Discord server", max_rounds=1
        )
        await discord.send_message(welcome_result.final_output, channel_id=channel_id)

    await manager.unload_plugin("discord")


async def example_discord_embeds():
    """Send rich embed messages to Discord."""
    print("=== Discord Embed Messages ===\n")

    manager = PluginManager()
    manager.discover_and_load()

    discord_config = {
        "token": os.getenv("DISCORD_BOT_TOKEN"),
        "guild_id": os.getenv("DISCORD_GUILD_ID"),
    }

    await manager.load_plugin("discord", discord_config)
    discord = manager.get_plugin("discord")
    await discord.connect()

    channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
    if channel_id:
        # Send embed
        fields = [
            {"name": "Active Agents", "value": "3", "inline": True},
            {"name": "Tasks Completed", "value": "42", "inline": True},
            {"name": "Status", "value": "All systems operational", "inline": False},
        ]

        await discord.send_embed(
            channel_id,
            title="AgentMind Status Report",
            description="Current system status and metrics",
            color=0x00FF00,
            fields=fields,
        )
        print("Embed sent to Discord")

    await manager.unload_plugin("discord")


async def example_list_guilds_and_channels():
    """List Discord guilds and channels."""
    print("=== List Discord Guilds and Channels ===\n")

    manager = PluginManager()
    manager.discover_and_load()

    discord_config = {"token": os.getenv("DISCORD_BOT_TOKEN")}

    await manager.load_plugin("discord", discord_config)
    discord = manager.get_plugin("discord")
    await discord.connect()

    # List guilds
    guilds = await discord.list_guilds()
    print("Available guilds:")
    for guild in guilds:
        print(f"  - {guild['name']} (ID: {guild['id']}, Members: {guild['member_count']})")

    # List channels in first guild
    if guilds:
        guild_id = guilds[0]["id"]
        channels = await discord.list_channels(guild_id)
        print(f"\nChannels in {guilds[0]['name']}:")
        for channel in channels:
            print(f"  - {channel['name']} (ID: {channel['id']}, Type: {channel['type']})")

    await manager.unload_plugin("discord")


async def example_discord_command_handler():
    """Discord bot with command handling."""
    print("=== Discord Command Handler ===\n")

    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    command_handler = Agent(
        name="CommandHandler",
        role="commands",
        system_prompt="You process Discord bot commands and provide appropriate responses.",
    )
    mind.add_agent(command_handler)

    manager = PluginManager()
    manager.discover_and_load()

    discord_config = {
        "token": os.getenv("DISCORD_BOT_TOKEN"),
        "guild_id": os.getenv("DISCORD_GUILD_ID"),
    }

    await manager.load_plugin("discord", discord_config)
    discord = manager.get_plugin("discord")
    await discord.connect()

    channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
    if channel_id:
        # Simulate command processing
        commands = {
            "!help": "Show available commands",
            "!status": "Check bot status",
            "!ask": "Ask the bot a question",
        }

        # Send help message
        help_text = "**Available Commands:**\n" + "\n".join(
            f"`{cmd}` - {desc}" for cmd, desc in commands.items()
        )
        await discord.send_message(help_text, channel_id=channel_id)

    await manager.unload_plugin("discord")


async def example_multi_channel_bot():
    """Bot that monitors multiple Discord channels."""
    print("=== Multi - Channel Discord Bot ===\n")

    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    monitor = Agent(
        name="ChannelMonitor",
        role="monitoring",
        system_prompt="You monitor multiple channels and provide summaries.",
    )
    mind.add_agent(monitor)

    manager = PluginManager()
    manager.discover_and_load()

    discord_config = {
        "token": os.getenv("DISCORD_BOT_TOKEN"),
        "guild_id": os.getenv("DISCORD_GUILD_ID"),
    }

    await manager.load_plugin("discord", discord_config)
    discord = manager.get_plugin("discord")
    await discord.connect()

    # Get channels
    guild_id = discord_config.get("guild_id")
    if guild_id:
        channels = await discord.list_channels(int(guild_id))

        # Monitor first few text channels
        for channel in channels[:3]:
            if "text" in channel["type"].lower():
                channel_id = channel["id"]
                messages = await discord.get_channel_messages(channel_id, limit=5)

                print(f"\nChannel: {channel['name']}")
                print(f"Recent messages: {len(messages)}")

    await manager.unload_plugin("discord")


async def main():
    """Run all examples."""
    print("Discord Plugin Examples\n")
    print("=" * 50 + "\n")

    print(
        "Note: Set DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, and DISCORD_CHANNEL_ID environment variables.\n"
    )

    # Check if credentials are available
    if not os.getenv("DISCORD_BOT_TOKEN"):
        print("DISCORD_BOT_TOKEN not set. Skipping examples.")
        return

    # Uncomment to run examples
    # await example_basic_discord()
    # await example_agent_with_discord()
    # await example_discord_bot()
    # await example_discord_embeds()
    # await example_list_guilds_and_channels()
    # await example_discord_command_handler()
    # await example_multi_channel_bot()


if __name__ == "__main__":
    asyncio.run(main())
