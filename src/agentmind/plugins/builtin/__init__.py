"""Built-in plugins for AgentMind."""

from .slack_plugin import SlackPlugin
from .discord_plugin import DiscordPlugin
from .webhook_plugin import WebhookPlugin

__all__ = [
    "SlackPlugin",
    "DiscordPlugin",
    "WebhookPlugin",
]
