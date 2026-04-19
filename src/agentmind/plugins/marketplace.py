"""Plugin marketplace infrastructure."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

logger = logging.getLogger(__name__)


class PluginCategory(str, Enum):
    """Plugin categories."""

    LLM_PROVIDER = "llm_provider"
    MEMORY = "memory"
    TOOLS = "tools"
    INTEGRATION = "integration"
    ORCHESTRATION = "orchestration"
    MIDDLEWARE = "middleware"
    UI = "ui"
    SECURITY = "security"
    MONITORING = "monitoring"
    OTHER = "other"


class PluginRating(BaseModel):
    """Plugin rating."""

    user_id: str = Field(..., description="User ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    review: Optional[str] = Field(None, description="Review text")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")


class PluginManifest(BaseModel):
    """Plugin manifest for marketplace."""

    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Plugin version")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    author_email: Optional[str] = Field(None, description="Author email")
    homepage: Optional[HttpUrl] = Field(None, description="Homepage URL")
    repository: Optional[HttpUrl] = Field(None, description="Repository URL")
    license: str = Field(default="MIT", description="License")
    category: PluginCategory = Field(..., description="Plugin category")
    tags: List[str] = Field(default_factory=list, description="Plugin tags")

    # Dependencies
    dependencies: List[str] = Field(default_factory=list, description="Plugin dependencies")
    python_requires: str = Field(default=">=3.8", description="Python version requirement")

    # Installation
    install_url: Optional[HttpUrl] = Field(None, description="Installation URL")
    package_name: Optional[str] = Field(None, description="PyPI package name")

    # Metadata
    downloads: int = Field(default=0, description="Download count")
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Average rating")
    rating_count: int = Field(default=0, description="Number of ratings")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    # Verification
    verified: bool = Field(default=False, description="Whether plugin is verified")
    checksum: Optional[str] = Field(None, description="Package checksum")


class PluginRegistry:
    """Plugin registry for marketplace."""

    def __init__(self, registry_file: Optional[Path] = None):
        """Initialize plugin registry.

        Args:
            registry_file: Path to registry JSON file
        """
        self.registry_file = registry_file or Path.cwd() / "plugin_registry.json"
        self._plugins: Dict[str, PluginManifest] = {}
        self._ratings: Dict[str, List[PluginRating]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load registry from file."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r") as f:
                    data = json.load(f)

                for plugin_data in data.get("plugins", []):
                    manifest = PluginManifest(**plugin_data)
                    self._plugins[manifest.name] = manifest

                for plugin_name, ratings_data in data.get("ratings", {}).items():
                    self._ratings[plugin_name] = [PluginRating(**rating) for rating in ratings_data]

                logger.info(f"Loaded {len(self._plugins)} plugins from registry")
            except Exception as e:
                logger.error(f"Error loading registry: {e}")

    def _save_registry(self) -> None:
        """Save registry to file."""
        try:
            data = {
                "plugins": [plugin.model_dump(mode="json") for plugin in self._plugins.values()],
                "ratings": {
                    name: [rating.model_dump(mode="json") for rating in ratings]
                    for name, ratings in self._ratings.items()
                },
            }

            with open(self.registry_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Saved registry with {len(self._plugins)} plugins")
        except Exception as e:
            logger.error(f"Error saving registry: {e}")

    def register_plugin(self, manifest: PluginManifest) -> bool:
        """Register a plugin in the marketplace.

        Args:
            manifest: Plugin manifest

        Returns:
            True if successful
        """
        try:
            if manifest.name in self._plugins:
                logger.warning(f"Plugin {manifest.name} already registered, updating")
                manifest.updated_at = datetime.now()
            else:
                manifest.created_at = datetime.now()
                manifest.updated_at = datetime.now()

            self._plugins[manifest.name] = manifest
            self._save_registry()

            logger.info(f"Registered plugin: {manifest.name} v{manifest.version}")
            return True

        except Exception as e:
            logger.error(f"Error registering plugin {manifest.name}: {e}")
            return False

    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister a plugin from marketplace.

        Args:
            plugin_name: Plugin name

        Returns:
            True if successful
        """
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            if plugin_name in self._ratings:
                del self._ratings[plugin_name]
            self._save_registry()
            logger.info(f"Unregistered plugin: {plugin_name}")
            return True
        return False

    def get_plugin(self, plugin_name: str) -> Optional[PluginManifest]:
        """Get plugin manifest.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin manifest or None
        """
        return self._plugins.get(plugin_name)

    def search_plugins(
        self,
        query: Optional[str] = None,
        category: Optional[PluginCategory] = None,
        tags: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        verified_only: bool = False,
    ) -> List[PluginManifest]:
        """Search for plugins.

        Args:
            query: Search query (searches name and description)
            category: Filter by category
            tags: Filter by tags
            min_rating: Minimum average rating
            verified_only: Only return verified plugins

        Returns:
            List of matching plugin manifests
        """
        results = list(self._plugins.values())

        # Filter by query
        if query:
            query_lower = query.lower()
            results = [
                p
                for p in results
                if query_lower in p.name.lower() or query_lower in p.description.lower()
            ]

        # Filter by category
        if category:
            results = [p for p in results if p.category == category]

        # Filter by tags
        if tags:
            results = [p for p in results if any(tag in p.tags for tag in tags)]

        # Filter by rating
        if min_rating is not None:
            results = [p for p in results if p.average_rating >= min_rating]

        # Filter by verification
        if verified_only:
            results = [p for p in results if p.verified]

        return results

    def add_rating(
        self, plugin_name: str, user_id: str, rating: int, review: Optional[str] = None
    ) -> bool:
        """Add a rating for a plugin.

        Args:
            plugin_name: Plugin name
            user_id: User ID
            rating: Rating (1-5)
            review: Optional review text

        Returns:
            True if successful
        """
        if plugin_name not in self._plugins:
            logger.error(f"Plugin not found: {plugin_name}")
            return False

        try:
            plugin_rating = PluginRating(user_id=user_id, rating=rating, review=review)

            if plugin_name not in self._ratings:
                self._ratings[plugin_name] = []

            # Remove existing rating from this user
            self._ratings[plugin_name] = [
                r for r in self._ratings[plugin_name] if r.user_id != user_id
            ]

            # Add new rating
            self._ratings[plugin_name].append(plugin_rating)

            # Update average rating
            self._update_plugin_rating(plugin_name)
            self._save_registry()

            logger.info(f"Added rating for {plugin_name} from user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding rating: {e}")
            return False

    def _update_plugin_rating(self, plugin_name: str) -> None:
        """Update average rating for a plugin.

        Args:
            plugin_name: Plugin name
        """
        ratings = self._ratings.get(plugin_name, [])
        if ratings:
            avg = sum(r.rating for r in ratings) / len(ratings)
            self._plugins[plugin_name].average_rating = round(avg, 2)
            self._plugins[plugin_name].rating_count = len(ratings)

    def get_ratings(self, plugin_name: str) -> List[PluginRating]:
        """Get all ratings for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            List of ratings
        """
        return self._ratings.get(plugin_name, [])

    def increment_downloads(self, plugin_name: str) -> None:
        """Increment download count for a plugin.

        Args:
            plugin_name: Plugin name
        """
        if plugin_name in self._plugins:
            self._plugins[plugin_name].downloads += 1
            self._save_registry()

    def get_popular_plugins(self, limit: int = 10) -> List[PluginManifest]:
        """Get most popular plugins by downloads.

        Args:
            limit: Maximum number of results

        Returns:
            List of plugin manifests
        """
        sorted_plugins = sorted(self._plugins.values(), key=lambda p: p.downloads, reverse=True)
        return sorted_plugins[:limit]

    def get_top_rated_plugins(self, limit: int = 10) -> List[PluginManifest]:
        """Get top-rated plugins.

        Args:
            limit: Maximum number of results

        Returns:
            List of plugin manifests
        """
        sorted_plugins = sorted(
            self._plugins.values(), key=lambda p: (p.average_rating, p.rating_count), reverse=True
        )
        return sorted_plugins[:limit]

    def get_recent_plugins(self, limit: int = 10) -> List[PluginManifest]:
        """Get recently added plugins.

        Args:
            limit: Maximum number of results

        Returns:
            List of plugin manifests
        """
        sorted_plugins = sorted(self._plugins.values(), key=lambda p: p.created_at, reverse=True)
        return sorted_plugins[:limit]

    def verify_plugin(self, plugin_name: str, verified: bool = True) -> bool:
        """Mark plugin as verified.

        Args:
            plugin_name: Plugin name
            verified: Verification status

        Returns:
            True if successful
        """
        if plugin_name in self._plugins:
            self._plugins[plugin_name].verified = verified
            self._save_registry()
            logger.info(f"Set verification status for {plugin_name}: {verified}")
            return True
        return False

    def export_manifest(self, plugin_name: str, output_file: Path) -> bool:
        """Export plugin manifest to file.

        Args:
            plugin_name: Plugin name
            output_file: Output file path

        Returns:
            True if successful
        """
        manifest = self.get_plugin(plugin_name)
        if not manifest:
            return False

        try:
            with open(output_file, "w") as f:
                json.dump(manifest.model_dump(mode="json"), f, indent=2, default=str)
            logger.info(f"Exported manifest for {plugin_name} to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting manifest: {e}")
            return False

    def import_manifest(self, manifest_file: Path) -> bool:
        """Import plugin manifest from file.

        Args:
            manifest_file: Manifest file path

        Returns:
            True if successful
        """
        try:
            with open(manifest_file, "r") as f:
                data = json.load(f)
            manifest = PluginManifest(**data)
            return self.register_plugin(manifest)
        except Exception as e:
            logger.error(f"Error importing manifest: {e}")
            return False
