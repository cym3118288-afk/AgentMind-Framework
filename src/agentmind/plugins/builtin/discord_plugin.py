"""Discord integration plugin for AgentMind."""

import asyncio
from typing import Any, Dict, List, Optional
import logging

from ..base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class DiscordPlugin(IntegrationPlugin):
    """Plugin for Discord integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Discord plugin.

        Args:
            config: Plugin configuration with 'token' and optional 'guild_id'
        """
        super().__init__(config)
        self.token = config.get("token") if config else None
        self.guild_id = config.get("guild_id") if config else None
        self.client = None
        self._connected = False

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="discord",
            version="1.0.0",
            description="Discord integration for AgentMind agents",
            author="AgentMind Team",
            plugin_type=PluginType.INTEGRATION,
            dependencies=["discord.py"],
            config_schema={
                "type": "object",
                "required": ["token"],
                "properties": {
                    "token": {"type": "string", "description": "Discord bot token"},
                    "guild_id": {"type": "string", "description": "Default guild ID"}
                }
            },
            tags=["discord", "messaging", "integration"],
            homepage="https://github.com/agentmind/plugins/discord",
            license="MIT"
        )

    async def initialize(self) -> None:
        """Initialize Discord client."""
        if not self.token:
            raise ValueError("Discord token is required")

        try:
            import discord
            intents = discord.Intents.default()
            intents.message_content = True
            self.client = discord.Client(intents=intents)
            logger.info("Discord plugin initialized")
        except ImportError:
            raise ImportError(
                "discord.py is required for Discord plugin. "
                "Install with: pip install discord.py"
            )

    async def shutdown(self) -> None:
        """Shutdown Discord client."""
        if self.client and self._connected:
            await self.disconnect()
        logger.info("Discord plugin shutdown")

    async def connect(self) -> None:
        """Connect to Discord."""
        if not self.client:
            raise RuntimeError("Plugin not initialized")

        try:
            # Start client in background
            asyncio.create_task(self.client.start(self.token))

            # Wait for ready
            await self.client.wait_until_ready()
            self._connected = True
            logger.info(f"Connected to Discord as {self.client.user}")
        except Exception as e:
            logger.error(f"Failed to connect to Discord: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Discord."""
        if self.client:
            await self.client.close()
        self._connected = False
        logger.info("Disconnected from Discord")

    async def send_message(
        self,
        message: str,
        channel_id: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Send message to Discord channel.

        Args:
            message: Message text
            channel_id: Channel ID
            **kwargs: Additional Discord API parameters

        Returns:
            Sent message object
        """
        if not self.client or not self._connected:
            raise RuntimeError("Plugin not connected")

        if not channel_id:
            raise ValueError("Channel ID is required")

        try:
            channel = self.client.get_channel(channel_id)
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")

            sent_message = await channel.send(message, **kwargs)
            return sent_message
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            raise

    async def send_embed(
        self,
        channel_id: int,
        title: str,
        description: str,
        color: Optional[int] = None,
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """Send embed message to Discord channel.

        Args:
            channel_id: Channel ID
            title: Embed title
            description: Embed description
            color: Embed color (hex)
            fields: List of embed fields

        Returns:
            Sent message object
        """
        if not self.client or not self._connected:
            raise RuntimeError("Plugin not connected")

        try:
            import discord

            channel = self.client.get_channel(channel_id)
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")

            embed = discord.Embed(
                title=title,
                description=description,
                color=color or 0x00ff00
            )

            if fields:
                for field in fields:
                    embed.add_field(
                        name=field.get("name", ""),
                        value=field.get("value", ""),
                        inline=field.get("inline", False)
                    )

            sent_message = await channel.send(embed=embed)
            return sent_message
        except Exception as e:
            logger.error(f"Failed to send embed: {e}")
            raise

    async def get_channel_messages(
        self,
        channel_id: int,
        limit: int = 100
    ) -> List[Any]:
        """Get channel message history.

        Args:
            channel_id: Channel ID
            limit: Maximum number of messages

        Returns:
            List of messages
        """
        if not self.client or not self._connected:
            raise RuntimeError("Plugin not connected")

        try:
            channel = self.client.get_channel(channel_id)
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")

            messages = []
            async for message in channel.history(limit=limit):
                messages.append(message)
            return messages
        except Exception as e:
            logger.error(f"Failed to get channel messages: {e}")
            raise

    async def add_reaction(
        self,
        message_id: int,
        channel_id: int,
        emoji: str
    ) -> None:
        """Add reaction to message.

        Args:
            message_id: Message ID
            channel_id: Channel ID
            emoji: Emoji (unicode or custom emoji name)
        """
        if not self.client or not self._connected:
            raise RuntimeError("Plugin not connected")

        try:
            channel = self.client.get_channel(channel_id)
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")

            message = await channel.fetch_message(message_id)
            await message.add_reaction(emoji)
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            raise

    async def delete_message(
        self,
        message_id: int,
        channel_id: int
    ) -> None:
        """Delete a message.

        Args:
            message_id: Message ID
            channel_id: Channel ID
        """
        if not self.client or not self._connected:
            raise RuntimeError("Plugin not connected")

        try:
            channel = self.client.get_channel(channel_id)
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")

            message = await channel.fetch_message(message_id)
            await message.delete()
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            raise

    async def list_guilds(self) -> List[Dict[str, Any]]:
        """List all guilds (servers) the bot is in.

        Returns:
            List of guild information
        """
        if not self.client or not self._connected:
            raise RuntimeError("Plugin not connected")

        guilds = []
        for guild in self.client.guilds:
            guilds.append({
                "id": guild.id,
                "name": guild.name,
                "member_count": guild.member_count
            })
        return guilds

    async def list_channels(self, guild_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all channels in a guild.

        Args:
            guild_id: Guild ID (uses default if not provided)

        Returns:
            List of channel information
        """
        if not self.client or not self._connected:
            raise RuntimeError("Plugin not connected")

        target_guild_id = guild_id or self.guild_id
        if not target_guild_id:
            raise ValueError("Guild ID is required")

        guild = self.client.get_guild(int(target_guild_id))
        if not guild:
            raise ValueError(f"Guild {target_guild_id} not found")

        channels = []
        for channel in guild.channels:
            channels.append({
                "id": channel.id,
                "name": channel.name,
                "type": str(channel.type)
            })
        return channels

    def is_connected(self) -> bool:
        """Check if connected to Discord."""
        return self._connected

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get bot user information.

        Returns:
            Bot user info or None
        """
        if not self.client or not self._connected:
            return None

        user = self.client.user
        if user:
            return {
                "id": user.id,
                "name": user.name,
                "discriminator": user.discriminator,
                "bot": user.bot
            }
        return None
