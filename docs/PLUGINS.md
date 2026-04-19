# Plugin System

AgentMind provides a flexible plugin architecture that allows you to extend the framework with custom functionality, integrations, and tools.

## Overview

The plugin system supports various types of plugins:

- **Tool Plugins**: Add custom tools that agents can use
- **Integration Plugins**: Connect to external services (Slack, Discord, etc.)
- **Memory Plugins**: Custom memory backends
- **LLM Provider Plugins**: Add support for new LLM providers
- **Orchestration Plugins**: Custom collaboration strategies
- **Middleware Plugins**: Request/response processing
- **UI Plugins**: Custom web interfaces

## Installation

Plugin dependencies are optional. Install what you need:

```bash
# Slack integration
pip install slack-sdk

# Discord integration
pip install discord.py

# Webhook integration (included with AgentMind)
pip install aiohttp
```

## Quick Start

### Using Built-in Plugins

```python
from agentmind.plugins import PluginManager

# Initialize plugin manager
manager = PluginManager()

# Discover and load plugins
manager.discover_and_load()

# Load a specific plugin
await manager.load_plugin("slack", config={
    "token": "xoxb-your-token",
    "channel": "C1234567890"
})

# Use the plugin
slack = manager.get_plugin("slack")
await slack.connect()
await slack.send_message("Hello from AgentMind!")

# Unload when done
await manager.unload_plugin("slack")
```

### Creating a Custom Plugin

```python
from agentmind.plugins import Plugin, PluginMetadata, PluginType

class MyCustomPlugin(Plugin):
    """My custom plugin."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="My custom plugin",
            author="Your Name",
            plugin_type=PluginType.TOOL,
            dependencies=["requests"],
            tags=["custom", "tool"]
        )

    async def initialize(self) -> None:
        """Initialize plugin."""
        print("Plugin initialized")

    async def shutdown(self) -> None:
        """Shutdown plugin."""
        print("Plugin shutdown")
```

## Built-in Plugins

### Slack Plugin

Connect agents to Slack for team communication.

```python
from agentmind.plugins import PluginManager

manager = PluginManager()
manager.discover_and_load()

# Configure Slack
slack_config = {
    "token": "xoxb-your-slack-bot-token",
    "channel": "C1234567890"  # Default channel
}

await manager.load_plugin("slack", slack_config)
slack = manager.get_plugin("slack")
await slack.connect()

# Send message
await slack.send_message("Hello team!")

# Send rich message
blocks = [
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Status:* All systems operational"}
    }
]
await slack.send_rich_message(channel_id, blocks, text="Status Update")

# Get channel history
messages = await slack.get_channel_history(channel_id, limit=10)

# Upload file
await slack.upload_file("report.pdf", channel_id, title="Report")

# Add reaction
await slack.add_reaction(channel_id, message_ts, "thumbsup")
```

### Discord Plugin

Integrate agents with Discord servers.

```python
discord_config = {
    "token": "your-discord-bot-token",
    "guild_id": "123456789"  # Server ID
}

await manager.load_plugin("discord", discord_config)
discord = manager.get_plugin("discord")
await discord.connect()

# Send message
await discord.send_message("Hello Discord!", channel_id=channel_id)

# Send embed
await discord.send_embed(
    channel_id,
    title="Status Report",
    description="All systems operational",
    color=0x00ff00,
    fields=[
        {"name": "Agents", "value": "3", "inline": True},
        {"name": "Tasks", "value": "42", "inline": True}
    ]
)

# Get messages
messages = await discord.get_channel_messages(channel_id, limit=10)

# Add reaction
await discord.add_reaction(message_id, channel_id, "✅")

# List guilds and channels
guilds = await discord.list_guilds()
channels = await discord.list_channels(guild_id)
```

### Webhook Plugin

Send data to webhooks for integration with any service.

```python
webhook_config = {
    "url": "https://your-webhook-url.com/endpoint",
    "headers": {"Authorization": "Bearer token"},
    "method": "POST"
}

await manager.load_plugin("webhook", webhook_config)
webhook = manager.get_plugin("webhook")

# Send JSON data
await webhook.send_json({
    "event": "agent_completed",
    "data": {"task": "analysis", "result": "success"}
})

# Send form data
await webhook.send_form_data({"key": "value"})

# Upload file
await webhook.send_file("report.pdf", field_name="file")

# Get data
data = await webhook.get_data(params={"query": "status"})
```

## Creating Custom Plugins

### Tool Plugin

```python
from agentmind.plugins import ToolPlugin, PluginMetadata, PluginType

class WeatherPlugin(ToolPlugin):
    """Get weather information."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="weather",
            version="1.0.0",
            description="Get weather information",
            author="Your Name",
            plugin_type=PluginType.TOOL,
            dependencies=["requests"]
        )

    async def initialize(self) -> None:
        self.api_key = self.config.get("api_key")

    async def shutdown(self) -> None:
        pass

    async def execute(self, location: str, **kwargs) -> dict:
        """Get weather for location."""
        # Implementation here
        return {"location": location, "temp": 72, "condition": "sunny"}

    def get_tool_definition(self) -> dict:
        return {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or coordinates"
                    }
                },
                "required": ["location"]
            }
        }
```

### Integration Plugin

```python
from agentmind.plugins import IntegrationPlugin, PluginMetadata, PluginType

class TelegramPlugin(IntegrationPlugin):
    """Telegram bot integration."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="telegram",
            version="1.0.0",
            description="Telegram bot integration",
            author="Your Name",
            plugin_type=PluginType.INTEGRATION,
            dependencies=["python-telegram-bot"]
        )

    async def initialize(self) -> None:
        from telegram import Bot
        self.bot = Bot(token=self.config["token"])

    async def shutdown(self) -> None:
        pass

    async def connect(self) -> None:
        # Test connection
        await self.bot.get_me()

    async def disconnect(self) -> None:
        pass

    async def send_message(self, message: str, chat_id: str, **kwargs) -> Any:
        return await self.bot.send_message(chat_id=chat_id, text=message)
```

### Memory Plugin

```python
from agentmind.plugins import MemoryPlugin, PluginMetadata, PluginType

class RedisMemoryPlugin(MemoryPlugin):
    """Redis-backed memory storage."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="redis_memory",
            version="1.0.0",
            description="Redis memory backend",
            author="Your Name",
            plugin_type=PluginType.MEMORY,
            dependencies=["redis"]
        )

    async def initialize(self) -> None:
        import redis.asyncio as redis
        self.redis = await redis.from_url(self.config["url"])

    async def shutdown(self) -> None:
        await self.redis.close()

    async def store(self, key: str, value: Any) -> None:
        import json
        await self.redis.set(key, json.dumps(value))

    async def retrieve(self, key: str) -> Optional[Any]:
        import json
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        pattern = pattern or "*"
        keys = await self.redis.keys(pattern)
        return [k.decode() for k in keys]
```

## Plugin Discovery

### Auto-Discovery

Plugins are automatically discovered from:

1. Built-in plugins (`agentmind.plugins.builtin`)
2. `./plugins` directory in current working directory
3. `~/.agentmind/plugins` directory in user home

```python
manager = PluginManager()

# Discover from default locations
count = manager.discover_and_load()
print(f"Discovered {count} plugins")

# Discover from custom paths
from pathlib import Path
count = manager.discover_and_load(
    search_paths=[Path("/custom/plugins")]
)
```

### Manual Registration

```python
from agentmind.plugins import PluginRegistry

registry = PluginRegistry()

# Register plugin class
registry.register(MyCustomPlugin)

# List registered plugins
plugins = registry.list_plugins()

# Create instance
plugin = registry.create_instance("my_plugin", config={})
```

## Plugin Management

### Loading and Unloading

```python
manager = PluginManager()

# Load plugin
success = await manager.load_plugin("slack", config={
    "token": "xoxb-token"
})

# Get plugin instance
slack = manager.get_plugin("slack")

# Reload plugin
await manager.reload_plugin("slack", new_config={
    "token": "xoxb-new-token"
})

# Unload plugin
await manager.unload_plugin("slack")

# Load all available plugins
count = await manager.load_all_plugins(configs={
    "slack": {"token": "xoxb-token"},
    "discord": {"token": "discord-token"}
})

# Unload all plugins
await manager.unload_all_plugins()
```

### Listing Plugins

```python
# List active plugins
active = manager.list_active_plugins()
print(f"Active: {active}")

# List available plugins
available = manager.list_available_plugins()
print(f"Available: {available}")

# List by type
from agentmind.plugins import PluginType
integrations = manager.list_available_plugins(PluginType.INTEGRATION)
```

### Using with Context Manager

```python
async with PluginManager() as manager:
    manager.discover_and_load()
    await manager.load_plugin("slack", config)
    
    slack = manager.get_plugin("slack")
    await slack.send_message("Hello!")
    
    # Plugins automatically unloaded on exit
```

## Plugin Configuration

### Configuration Schema

Define configuration requirements in metadata:

```python
def get_metadata(self) -> PluginMetadata:
    return PluginMetadata(
        name="my_plugin",
        version="1.0.0",
        description="My plugin",
        author="Your Name",
        plugin_type=PluginType.TOOL,
        config_schema={
            "type": "object",
            "required": ["api_key"],
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "API key for service"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 30
                }
            }
        }
    )
```

### Validation

```python
def validate_config(self, config: Dict[str, Any]) -> bool:
    """Custom validation logic."""
    if not super().validate_config(config):
        return False
    
    # Additional validation
    if config.get("timeout", 0) < 0:
        return False
    
    return True
```

## Best Practices

### Error Handling

```python
async def execute(self, **kwargs) -> Any:
    try:
        # Plugin logic
        result = await self.do_something()
        return result
    except Exception as e:
        logger.error(f"Plugin error: {e}")
        raise
```

### Resource Cleanup

```python
async def shutdown(self) -> None:
    """Always clean up resources."""
    if self.connection:
        await self.connection.close()
    if self.session:
        await self.session.close()
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

async def initialize(self) -> None:
    logger.info(f"Initializing {self.get_metadata().name}")
    # Initialization logic
    logger.info("Initialization complete")
```

### Async Operations

```python
async def execute(self, **kwargs) -> Any:
    """Use async/await for I/O operations."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

## Examples

See the `examples/` directory for complete examples:

- `plugin_slack_example.py` - Slack integration examples
- `plugin_discord_example.py` - Discord integration examples
- `plugin_custom_example.py` - Creating custom plugins

## Troubleshooting

### Plugin Not Found

```python
# Check if plugin is registered
metadata = manager.registry.get_metadata("plugin_name")
if metadata is None:
    print("Plugin not registered")
```

### Import Errors

Ensure plugin dependencies are installed:

```bash
pip install slack-sdk discord.py
```

### Connection Issues

```python
try:
    await plugin.connect()
except Exception as e:
    print(f"Connection failed: {e}")
    # Check credentials, network, etc.
```

## API Reference

### Plugin Base Classes

- `Plugin` - Base class for all plugins
- `ToolPlugin` - Base for tool plugins
- `IntegrationPlugin` - Base for integration plugins
- `MemoryPlugin` - Base for memory plugins
- `LLMProviderPlugin` - Base for LLM provider plugins
- `OrchestrationPlugin` - Base for orchestration plugins
- `MiddlewarePlugin` - Base for middleware plugins
- `UIPlugin` - Base for UI plugins

### Plugin Manager

- `load_plugin(name, config)` - Load and initialize plugin
- `unload_plugin(name)` - Unload and shutdown plugin
- `reload_plugin(name, config)` - Reload plugin
- `get_plugin(name)` - Get plugin instance
- `list_active_plugins()` - List active plugins
- `list_available_plugins(type)` - List available plugins
- `discover_and_load(paths, auto_load, configs)` - Discover plugins

### Plugin Registry

- `register(plugin_class)` - Register plugin class
- `unregister(name)` - Unregister plugin
- `get_plugin_class(name)` - Get plugin class
- `get_metadata(name)` - Get plugin metadata
- `list_plugins(type)` - List registered plugins
- `create_instance(name, config)` - Create plugin instance
