"""Plugin configuration management with validation and hot-reload."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Type, Callable
from pydantic import BaseModel, Field, ValidationError
from enum import Enum
import yaml

logger = logging.getLogger(__name__)


class ConfigEnvironment(str, Enum):
    """Configuration environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class PluginConfigSchema(BaseModel):
    """Base schema for plugin configuration."""

    enabled: bool = Field(default=True, description="Whether plugin is enabled")
    environment: ConfigEnvironment = Field(
        default=ConfigEnvironment.DEVELOPMENT, description="Environment"
    )
    settings: Dict[str, Any] = Field(default_factory=dict, description="Plugin-specific settings")


class ConfigValidator:
    """Validate plugin configurations."""

    def __init__(self):
        """Initialize config validator."""
        self._schemas: Dict[str, Type[BaseModel]] = {}

    def register_schema(self, plugin_name: str, schema: Type[BaseModel]) -> None:
        """Register a configuration schema for a plugin.

        Args:
            plugin_name: Plugin name
            schema: Pydantic model class for validation
        """
        self._schemas[plugin_name] = schema
        logger.info(f"Registered config schema for plugin: {plugin_name}")

    def validate(
        self, plugin_name: str, config: Dict[str, Any]
    ) -> tuple[bool, Optional[BaseModel], Optional[str]]:
        """Validate plugin configuration.

        Args:
            plugin_name: Plugin name
            config: Configuration dictionary

        Returns:
            Tuple of (valid, validated_config, error_message)
        """
        schema = self._schemas.get(plugin_name)

        if not schema:
            # No schema registered, use base schema
            schema = PluginConfigSchema

        try:
            validated = schema(**config)
            return True, validated, None
        except ValidationError as e:
            error_msg = f"Configuration validation failed: {e}"
            logger.error(f"Config validation error for {plugin_name}: {error_msg}")
            return False, None, error_msg

    def get_schema(self, plugin_name: str) -> Optional[Type[BaseModel]]:
        """Get registered schema for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Schema class or None
        """
        return self._schemas.get(plugin_name)


class ConfigManager:
    """Manage plugin configurations."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config manager.

        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = config_dir or Path.cwd() / "config" / "plugins"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self._configs: Dict[str, Dict[str, Any]] = {}
        self._env_configs: Dict[ConfigEnvironment, Dict[str, Dict[str, Any]]] = {
            env: {} for env in ConfigEnvironment
        }
        self._validator = ConfigValidator()
        self._reload_callbacks: Dict[str, list[Callable]] = {}

    def register_schema(self, plugin_name: str, schema: Type[BaseModel]) -> None:
        """Register configuration schema for a plugin.

        Args:
            plugin_name: Plugin name
            schema: Pydantic model class
        """
        self._validator.register_schema(plugin_name, schema)

    def load_config(
        self, plugin_name: str, environment: Optional[ConfigEnvironment] = None
    ) -> Optional[Dict[str, Any]]:
        """Load configuration for a plugin.

        Args:
            plugin_name: Plugin name
            environment: Configuration environment

        Returns:
            Configuration dictionary or None
        """
        env = environment or ConfigEnvironment.DEVELOPMENT

        # Try to load from file
        config_file = self.config_dir / f"{plugin_name}.yaml"
        if not config_file.exists():
            config_file = self.config_dir / f"{plugin_name}.json"

        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    if config_file.suffix == ".yaml" or config_file.suffix == ".yml":
                        config = yaml.safe_load(f)
                    else:
                        config = json.load(f)

                # Get environment-specific config
                if isinstance(config, dict) and "environments" in config:
                    env_config = config.get("environments", {}).get(env.value, {})
                    base_config = {k: v for k, v in config.items() if k != "environments"}
                    # Merge base and environment configs
                    final_config = {**base_config, **env_config}
                else:
                    final_config = config

                # Validate
                valid, validated, error = self._validator.validate(plugin_name, final_config)
                if not valid:
                    logger.error(f"Invalid config for {plugin_name}: {error}")
                    return None

                self._configs[plugin_name] = final_config
                self._env_configs[env][plugin_name] = final_config

                logger.info(f"Loaded config for {plugin_name} (env: {env.value})")
                return final_config

            except Exception as e:
                logger.error(f"Error loading config for {plugin_name}: {e}")
                return None

        logger.warning(f"No config file found for {plugin_name}")
        return None

    def save_config(self, plugin_name: str, config: Dict[str, Any], format: str = "yaml") -> bool:
        """Save configuration for a plugin.

        Args:
            plugin_name: Plugin name
            config: Configuration dictionary
            format: File format ('yaml' or 'json')

        Returns:
            True if successful
        """
        # Validate first
        valid, validated, error = self._validator.validate(plugin_name, config)
        if not valid:
            logger.error(f"Cannot save invalid config for {plugin_name}: {error}")
            return False

        try:
            config_file = self.config_dir / f"{plugin_name}.{format}"

            with open(config_file, "w") as f:
                if format == "yaml" or format == "yml":
                    yaml.dump(config, f, default_flow_style=False)
                else:
                    json.dump(config, f, indent=2)

            self._configs[plugin_name] = config
            logger.info(f"Saved config for {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Error saving config for {plugin_name}: {e}")
            return False

    def get_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get cached configuration for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Configuration dictionary or None
        """
        return self._configs.get(plugin_name)

    def update_config(self, plugin_name: str, updates: Dict[str, Any], save: bool = True) -> bool:
        """Update configuration for a plugin.

        Args:
            plugin_name: Plugin name
            updates: Configuration updates
            save: Whether to save to file

        Returns:
            True if successful
        """
        current = self.get_config(plugin_name) or {}
        updated = {**current, **updates}

        # Validate
        valid, validated, error = self._validator.validate(plugin_name, updated)
        if not valid:
            logger.error(f"Invalid config update for {plugin_name}: {error}")
            return False

        self._configs[plugin_name] = updated

        if save:
            self.save_config(plugin_name, updated)

        # Trigger reload callbacks
        self._trigger_reload_callbacks(plugin_name, updated)

        return True

    def register_reload_callback(
        self, plugin_name: str, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Register callback for config reload.

        Args:
            plugin_name: Plugin name
            callback: Callback function
        """
        if plugin_name not in self._reload_callbacks:
            self._reload_callbacks[plugin_name] = []

        self._reload_callbacks[plugin_name].append(callback)
        logger.debug(f"Registered reload callback for {plugin_name}")

    def _trigger_reload_callbacks(self, plugin_name: str, new_config: Dict[str, Any]) -> None:
        """Trigger reload callbacks for a plugin.

        Args:
            plugin_name: Plugin name
            new_config: New configuration
        """
        callbacks = self._reload_callbacks.get(plugin_name, [])

        for callback in callbacks:
            try:
                callback(new_config)
            except Exception as e:
                logger.error(f"Error in reload callback for {plugin_name}: {e}")

    async def hot_reload(self, plugin_name: str, plugin: Any) -> bool:
        """Hot-reload configuration for a plugin.

        Args:
            plugin_name: Plugin name
            plugin: Plugin instance

        Returns:
            True if successful
        """
        try:
            # Load new config
            new_config = self.load_config(plugin_name)
            if new_config is None:
                return False

            # Call plugin's reload method if available
            if hasattr(plugin, "reload_config"):
                await plugin.reload_config(new_config)
            elif hasattr(plugin, "config"):
                plugin.config = new_config

            logger.info(f"Hot-reloaded config for {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Error hot-reloading config for {plugin_name}: {e}")
            return False

    def get_environment_config(self, environment: ConfigEnvironment) -> Dict[str, Dict[str, Any]]:
        """Get all configs for an environment.

        Args:
            environment: Configuration environment

        Returns:
            Dict of plugin configs
        """
        return self._env_configs.get(environment, {})

    def migrate_config(
        self, plugin_name: str, migration_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> bool:
        """Migrate plugin configuration.

        Args:
            plugin_name: Plugin name
            migration_func: Function to transform config

        Returns:
            True if successful
        """
        try:
            current = self.get_config(plugin_name)
            if current is None:
                logger.warning(f"No config to migrate for {plugin_name}")
                return False

            # Apply migration
            migrated = migration_func(current)

            # Validate migrated config
            valid, validated, error = self._validator.validate(plugin_name, migrated)
            if not valid:
                logger.error(f"Migrated config invalid for {plugin_name}: {error}")
                return False

            # Save migrated config
            return self.save_config(plugin_name, migrated)

        except Exception as e:
            logger.error(f"Error migrating config for {plugin_name}: {e}")
            return False

    def export_configs(self, output_file: Path) -> bool:
        """Export all configurations to a file.

        Args:
            output_file: Output file path

        Returns:
            True if successful
        """
        try:
            with open(output_file, "w") as f:
                if output_file.suffix == ".yaml" or output_file.suffix == ".yml":
                    yaml.dump(self._configs, f, default_flow_style=False)
                else:
                    json.dump(self._configs, f, indent=2)

            logger.info(f"Exported configs to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error exporting configs: {e}")
            return False

    def import_configs(self, input_file: Path) -> bool:
        """Import configurations from a file.

        Args:
            input_file: Input file path

        Returns:
            True if successful
        """
        try:
            with open(input_file, "r") as f:
                if input_file.suffix == ".yaml" or input_file.suffix == ".yml":
                    configs = yaml.safe_load(f)
                else:
                    configs = json.load(f)

            # Validate and load each config
            for plugin_name, config in configs.items():
                valid, validated, error = self._validator.validate(plugin_name, config)
                if valid:
                    self._configs[plugin_name] = config
                else:
                    logger.warning(f"Skipping invalid config for {plugin_name}: {error}")

            logger.info(f"Imported configs from {input_file}")
            return True

        except Exception as e:
            logger.error(f"Error importing configs: {e}")
            return False
