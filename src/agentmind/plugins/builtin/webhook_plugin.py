"""Webhook plugin for AgentMind."""

import asyncio
from typing import Any, Dict, Optional
import logging
import json

from ..base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class WebhookPlugin(IntegrationPlugin):
    """Plugin for webhook integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Webhook plugin.

        Args:
            config: Plugin configuration with 'url' and optional 'headers'
        """
        super().__init__(config)
        self.url = config.get("url") if config else None
        self.headers = config.get("headers", {}) if config else {}
        self.method = config.get("method", "POST") if config else "POST"
        self._session = None

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="webhook",
            version="1.0.0",
            description="Webhook integration for AgentMind agents",
            author="AgentMind Team",
            plugin_type=PluginType.INTEGRATION,
            dependencies=["aiohttp"],
            config_schema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string", "description": "Webhook URL"},
                    "headers": {"type": "object", "description": "HTTP headers"},
                    "method": {"type": "string", "description": "HTTP method (POST/PUT)"}
                }
            },
            tags=["webhook", "http", "integration"],
            homepage="https://github.com/agentmind/plugins/webhook",
            license="MIT"
        )

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        if not self.url:
            raise ValueError("Webhook URL is required")

        try:
            import aiohttp
            self._session = aiohttp.ClientSession()
            logger.info("Webhook plugin initialized")
        except ImportError:
            raise ImportError(
                "aiohttp is required for Webhook plugin. "
                "Install with: pip install aiohttp"
            )

    async def shutdown(self) -> None:
        """Shutdown HTTP session."""
        if self._session:
            await self._session.close()
        logger.info("Webhook plugin shutdown")

    async def connect(self) -> None:
        """Test webhook connection."""
        if not self._session:
            raise RuntimeError("Plugin not initialized")

        try:
            # Send test ping
            async with self._session.get(self.url, headers=self.headers) as response:
                if response.status < 400:
                    logger.info(f"Webhook connection test successful: {response.status}")
                else:
                    logger.warning(f"Webhook returned status: {response.status}")
        except Exception as e:
            logger.error(f"Failed to connect to webhook: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect (no-op for webhooks)."""
        logger.info("Webhook disconnected")

    async def send_message(
        self,
        message: str,
        **kwargs
    ) -> Any:
        """Send message to webhook.

        Args:
            message: Message text
            **kwargs: Additional data to send

        Returns:
            Response data
        """
        if not self._session:
            raise RuntimeError("Plugin not initialized")

        payload = {
            "message": message,
            **kwargs
        }

        return await self.send_json(payload)

    async def send_json(self, data: Dict[str, Any]) -> Any:
        """Send JSON data to webhook.

        Args:
            data: JSON data to send

        Returns:
            Response data
        """
        if not self._session:
            raise RuntimeError("Plugin not initialized")

        try:
            headers = {**self.headers, "Content-Type": "application/json"}

            async with self._session.request(
                self.method,
                self.url,
                json=data,
                headers=headers
            ) as response:
                response.raise_for_status()

                if response.content_type == "application/json":
                    return await response.json()
                else:
                    return await response.text()
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            raise

    async def send_form_data(self, data: Dict[str, Any]) -> Any:
        """Send form data to webhook.

        Args:
            data: Form data to send

        Returns:
            Response data
        """
        if not self._session:
            raise RuntimeError("Plugin not initialized")

        try:
            async with self._session.request(
                self.method,
                self.url,
                data=data,
                headers=self.headers
            ) as response:
                response.raise_for_status()

                if response.content_type == "application/json":
                    return await response.json()
                else:
                    return await response.text()
        except Exception as e:
            logger.error(f"Failed to send form data: {e}")
            raise

    async def send_file(
        self,
        file_path: str,
        field_name: str = "file",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Send file to webhook.

        Args:
            file_path: Path to file
            field_name: Form field name for file
            additional_data: Additional form data

        Returns:
            Response data
        """
        if not self._session:
            raise RuntimeError("Plugin not initialized")

        try:
            import aiohttp

            data = aiohttp.FormData()

            # Add file
            with open(file_path, "rb") as f:
                data.add_field(
                    field_name,
                    f,
                    filename=file_path.split("/")[-1]
                )

            # Add additional data
            if additional_data:
                for key, value in additional_data.items():
                    data.add_field(key, str(value))

            async with self._session.request(
                self.method,
                self.url,
                data=data,
                headers=self.headers
            ) as response:
                response.raise_for_status()

                if response.content_type == "application/json":
                    return await response.json()
                else:
                    return await response.text()
        except Exception as e:
            logger.error(f"Failed to send file: {e}")
            raise

    async def get_data(self, params: Optional[Dict[str, Any]] = None) -> Any:
        """Get data from webhook endpoint.

        Args:
            params: Query parameters

        Returns:
            Response data
        """
        if not self._session:
            raise RuntimeError("Plugin not initialized")

        try:
            async with self._session.get(
                self.url,
                params=params,
                headers=self.headers
            ) as response:
                response.raise_for_status()

                if response.content_type == "application/json":
                    return await response.json()
                else:
                    return await response.text()
        except Exception as e:
            logger.error(f"Failed to get data: {e}")
            raise
