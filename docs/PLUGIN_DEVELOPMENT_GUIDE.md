# Plugin System Development Guide

## Overview

AgentMind's production-grade plugin system provides comprehensive features for building, managing, and deploying plugins safely and efficiently.

## Features

### 1. Lifecycle Management
- **State Tracking**: Plugins transition through defined states (uninitialized, initializing, active, inactive, error, suspended)
- **Lifecycle Hooks**: Pre/post hooks for initialization, activation, deactivation, and cleanup
- **Health Monitoring**: Automatic health checks with uptime tracking and error counting

### 2. Dependency Resolution
- **Version Checking**: Semantic versioning support with complex version specifications
- **Dependency Graphs**: Automatic dependency resolution and load order calculation
- **Circular Detection**: Detects and prevents circular dependencies
- **Optional Dependencies**: Support for optional plugin dependencies

### 3. Security Features
- **Sandboxed Execution**: Resource-limited execution with timeout protection
- **Permission System**: Fine-grained permissions for network, filesystem, and API access
- **Signature Verification**: Plugin integrity verification with checksums and digital signatures
- **Audit Logging**: Comprehensive audit trail of all plugin operations

### 4. Configuration Management
- **Schema Validation**: Pydantic-based configuration validation
- **Hot-Reload**: Change configuration without restarting plugins
- **Environment Support**: Separate configs for dev/staging/production
- **Migration Helpers**: Tools for migrating configurations between versions

### 5. Plugin Marketplace
- **Registry Format**: JSON-based plugin manifests with rich metadata
- **Search & Filter**: Search by category, tags, ratings, and verification status
- **Ratings & Reviews**: User ratings and review system
- **Download Tracking**: Track plugin popularity

### 6. Developer Tools
- **Plugin Scaffolding**: CLI command to generate plugin templates
- **Testing Utilities**: Mock plugins, test harnesses, and performance testers
- **Debugging Tools**: Comprehensive logging and error tracking

## Quick Start

### Creating a Plugin

```bash
# Generate plugin scaffold
agentmind plugin create my-plugin --type tool --author "Your Name"

# Navigate to plugin directory
cd agentmind-plugin-my-plugin

# Install in development mode
pip install -e .
```

### Basic Plugin Structure

```python
from typing import Any, Dict, Optional
from agentmind.plugins import ToolPlugin, PluginMetadata, PluginType

class MyPlugin(ToolPlugin):
    """My custom plugin."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            description="My custom plugin",
            author="Your Name",
            plugin_type=PluginType.TOOL,
            dependencies=["other-plugin>=1.0.0"],
        )
    
    async def initialize(self) -> None:
        """Initialize plugin resources."""
        # Setup code here
        pass
    
    async def shutdown(self) -> None:
        """Cleanup plugin resources."""
        # Cleanup code here
        pass
    
    async def execute(self, **kwargs) -> Any:
        """Execute plugin functionality."""
        # Implementation here
        return {"status": "success"}
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM function calling."""
        return {
            "name": "my-plugin",
            "description": "My custom plugin",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Parameter 1"}
                },
                "required": ["param1"]
            }
        }
```

### Using Plugins

```python
from agentmind.plugins import PluginManager

# Initialize manager with all features
manager = PluginManager(
    enable_security=True,
    enable_audit=True
)

# Discover and load plugins
manager.discover_and_load(auto_load=False)

# Load specific plugin
await manager.load_plugin("my-plugin", config={
    "enabled": True,
    "setting1": "value1"
})

# Execute plugin
result = await manager.execute_plugin(
    "my-plugin",
    sandboxed=True,
    timeout=30.0,
    param1="test"
)

# Check health
health = await manager.check_plugin_health("my-plugin")
print(f"Plugin healthy: {health['healthy']}")

# Unload plugin
await manager.unload_plugin("my-plugin")
```

## Advanced Features

### Lifecycle Hooks

```python
from agentmind.plugins import PluginManager

manager = PluginManager()

# Register lifecycle hooks
def pre_init_hook(plugin):
    print(f"About to initialize {plugin.get_metadata().name}")

async def post_init_hook(plugin):
    print(f"Initialized {plugin.get_metadata().name}")

manager.register_lifecycle_hook("my-plugin", "pre_initialize", pre_init_hook)
manager.register_lifecycle_hook("my-plugin", "post_initialize", post_init_hook)
```

### Permission Management

```python
from agentmind.plugins import PluginPermissions

# Set plugin permissions
manager.set_plugin_permissions("my-plugin", {
    "allow_network": True,
    "allow_filesystem": False,
    "allowed_apis": {"api1", "api2"},
    "max_memory_mb": 512,
    "max_cpu_percent": 50.0
})
```

### Configuration with Validation

```python
from pydantic import BaseModel, Field
from agentmind.plugins import ConfigManager

class MyPluginConfig(BaseModel):
    api_key: str = Field(..., min_length=10)
    timeout: int = Field(default=30, ge=1, le=300)
    debug: bool = False

# Register schema
config_manager = ConfigManager()
config_manager.register_schema("my-plugin", MyPluginConfig)

# Load and validate config
config = config_manager.load_config("my-plugin")
```

### Hot-Reload Configuration

```python
# Update configuration
manager.config_manager.update_config("my-plugin", {
    "timeout": 60,
    "debug": True
})

# Hot-reload plugin with new config
await manager.reload_plugin("my-plugin")
```

### Dependency Management

```python
from agentmind.plugins import PluginDependency

# Define dependencies in plugin metadata
dependencies = [
    PluginDependency(name="base-plugin", version_spec=">=1.0.0,<2.0.0"),
    PluginDependency(name="optional-plugin", version_spec="*", optional=True)
]

# Manager automatically resolves load order
await manager.load_all_plugins(resolve_dependencies=True)
```

## Testing Plugins

### Using Test Harness

```python
from agentmind.plugins.testing import PluginTestHarness

# Create test harness
harness = PluginTestHarness(MyPlugin, config={"test": True})
await harness.setup()

# Run lifecycle tests
results = await harness.test_lifecycle()
assert results["initialize"]
assert results["health_check"]
assert results["shutdown"]

# Test error handling
error_results = await harness.test_error_handling()

# Generate report
report = harness.generate_test_report(results)
print(report)

await harness.teardown()
```

### Performance Testing

```python
from agentmind.plugins.testing import PluginPerformanceTester

tester = PluginPerformanceTester(my_plugin)

# Test initialization time
init_time = await tester.test_initialization_time(iterations=10)
print(f"Average init time: {init_time:.3f}s")

# Test throughput
ops_per_sec = await tester.test_execution_throughput(duration=5.0)
print(f"Throughput: {ops_per_sec:.2f} ops/sec")
```

## CLI Commands

```bash
# Create new plugin
agentmind plugin create my-plugin --type tool

# List installed plugins
agentmind plugin list

# Show plugin info
agentmind plugin info my-plugin

# Search marketplace
agentmind plugin search --query "llm" --category tools

# Test plugin
agentmind plugin test my-plugin
```

## Best Practices

1. **Always validate configuration**: Use Pydantic models for type-safe configs
2. **Implement health checks**: Return meaningful health status
3. **Handle errors gracefully**: Use try-except and log errors properly
4. **Clean up resources**: Always implement proper shutdown logic
5. **Document dependencies**: Clearly specify version requirements
6. **Write tests**: Use the testing utilities to ensure reliability
7. **Use semantic versioning**: Follow semver for version numbers
8. **Audit sensitive operations**: Log security-relevant actions

## Security Considerations

- **Sandbox untrusted plugins**: Always use sandboxed execution for third-party plugins
- **Verify signatures**: Check plugin checksums before loading
- **Limit permissions**: Grant minimal required permissions
- **Monitor resource usage**: Set appropriate resource limits
- **Audit all operations**: Enable audit logging in production
- **Validate inputs**: Sanitize all user inputs

## Troubleshooting

### Plugin won't load
- Check dependencies are satisfied
- Verify configuration is valid
- Check audit logs for errors
- Ensure plugin is properly registered

### Permission denied errors
- Review plugin permissions
- Check audit logs for denied operations
- Verify API access is granted

### Performance issues
- Use performance tester to identify bottlenecks
- Check resource limits aren't too restrictive
- Review health check results
- Monitor error counts

## API Reference

See individual module documentation:
- `agentmind.plugins.base` - Base plugin classes
- `agentmind.plugins.manager` - Plugin manager
- `agentmind.plugins.lifecycle` - Lifecycle management
- `agentmind.plugins.dependencies` - Dependency resolution
- `agentmind.plugins.security` - Security features
- `agentmind.plugins.config` - Configuration management
- `agentmind.plugins.marketplace` - Marketplace infrastructure
- `agentmind.plugins.audit` - Audit logging
- `agentmind.plugins.testing` - Testing utilities
