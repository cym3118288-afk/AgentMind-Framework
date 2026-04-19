"""Slack integration plugin for AgentMind."""

import asyncio
from typing import Any, Dict, List, Optional
import logging

from ..base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class SlackPlugin(IntegrationPlugin):
    """Plugin for Slack integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Slack plugin.

        Args:
            config: Plugin configuration with 'token' and optional 'channel'
        """
        super().__init__(config)
        self.token = config.get("token") if config else None
        self.default_channel = config.get("channel") if config else None
        self.client = None
        self._connected = False

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="slack",
            version="1.0.0",
            description="Slack integration for AgentMind agents",
            author="AgentMind Team",
            plugin_type=PluginType.INTEGRATION,
            dependencies=["slack-sdk"],
            config_schema={
                "type": "object",
                "required": ["token"],
                "properties": {
                    "token": {"type": "string", "description": "Slack bot token"},
                    "channel": {"type": "string", "description": "Default channel ID"}
                }
            },
            tags=["slack", "messaging", "integration"],
            homepage="https://github.com/agentmind/plugins/slack",
            license="MIT"
        )

    async def initialize(self) -> None:
        """Initialize Slack client."""
        if not self.token:
            raise ValueError("Slack token is required")

        try:
            from slack_sdk.web.async_client import AsyncWebClient
            self.client = AsyncWebClient(token=self.token)
            logger.info("Slack plugin initialized")
        except ImportError:
            raise ImportError(
                "slack-sdk is required for Slack plugin. "
                "Install with: pip install slack-sdk"
            )

    async def shutdown(self) -> None:
        """Shutdown Slack client."""
        if self.client:
            await self.disconnect()
        logger.info("Slack plugin shutdown")

    async def connect(self) -> None:
        """Test connection to Slack."""
        if not self.client:
            raise RuntimeError("Plugin not initialized")

        try:
            response = await self.client.auth_test()
            if response["ok"]:
                self._connected = True
                logger.info(f"Connected to Slack as {response['user']}")
            else:
                raise RuntimeError(f"Slack auth failed: {response.get('error')}")
        except Exception as e:
            logger.error(f"Failed to connect to Slack: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Slack."""
        self._connected = False
        logger.info("Disconnected from Slack")

    async def send_message(
        self,
        message: str,
        channel: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Send message to Slack channel.

        Args:
            message: Message text
            channel: Channel ID (uses default if not provided)
            **kwargs: Additional Slack API parameters

        Returns:
            Slack API response
        """
        if not self.client:
            raise RuntimeError("Plugin not initialized")

        target_channel = channel or self.default_channel
        if not target_channel:
            raise ValueError("Channel is required")

        try:
            response = await self.client.chat_postMessage(
                channel=target_channel,
                text=message,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            raise

    async def send_rich_message(
        self,
        channel: str,
        blocks: List[Dict[str, Any]],
        text: Optional[str] = None
    ) -> Any:
        """Send rich message with blocks.

        Args:
            channel: Channel ID
            blocks: Slack block kit blocks
            text: Fallback text

        Returns:
            Slack API response
        """
        if not self.client:
            raise RuntimeError("Plugin not initialized")

        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=text or "Message"
            )
            return response
        except Exception as e:
            logger.error(f"Failed to send rich message: {e}")
            raise

    async def get_channel_history(
        self,
        channel: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get channel message history.

        Args:
            channel: Channel ID
            limit: Maximum number of messages

        Returns:
            List of messages
        """
        if not self.client:
            raise RuntimeError("Plugin not initialized")

        try:
            response = await self.client.conversations_history(
                channel=channel,
                limit=limit
            )
            return response.get("messages", [])
        except Exception as e:
            logger.error(f"Failed to get channel history: {e}")
            raise

    async def list_channels(self) -> List[Dict[str, Any]]:
        """List all channels.

        Returns:
            List of channels
        """
        if not self.client:
            raise RuntimeError("Plugin not initialized")

        try:
            response = await self.client.conversations_list()
            return response.get("channels", [])
        except Exception as e:
            logger.error(f"Failed to list channels: {e}")
            raise

    async def upload_file(
        self,
        file_path: str,
        channel: str,
        title: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Any:
        """Upload file to Slack.

        Args:
            file_path: Path to file
            channel: Channel ID
            title: File title
            comment: File comment

        Returns:
            Slack API response
        """
        if not self.client:
            raise RuntimeError("Plugin not initialized")

        try:
            response = await self.client.files_upload(
                channels=channel,
                file=file_path,
                title=title,
                initial_comment=comment
            )
            return response
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        emoji: str
    ) -> Any:
        """Add reaction to message.

        Args:
            channel: Channel ID
            timestamp: Message timestamp
            emoji: Emoji name (without colons)

        Returns:
            Slack API response
        """
        if not self.client:
            raise RuntimeError("Plugin not initialized")

        try:
            response = await self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji
            )
            return response
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            raise

    def is_connected(self) -> bool:
        """Check if connected to Slack."""
        return self._connected
