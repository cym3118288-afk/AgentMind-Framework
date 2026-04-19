"""Plugin dependency resolution and version compatibility checking."""

import logging
from typing import Dict, List, Optional, Set, Tuple
from packaging import version
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PluginDependency(BaseModel):
    """Plugin dependency specification."""

    name: str = Field(..., description="Plugin name")
    version_spec: str = Field(
        default="*", description="Version specification (e.g., '>=1.0.0,<2.0.0')"
    )
    optional: bool = Field(default=False, description="Whether dependency is optional")


class DependencyNode(BaseModel):
    """Node in dependency graph."""

    name: str
    version: str
    dependencies: List[PluginDependency] = Field(default_factory=list)
    dependents: List[str] = Field(default_factory=list)


class DependencyGraph:
    """Dependency graph for plugins."""

    def __init__(self):
        """Initialize dependency graph."""
        self._nodes: Dict[str, DependencyNode] = {}

    def add_plugin(
        self, name: str, version: str, dependencies: Optional[List[PluginDependency]] = None
    ) -> None:
        """Add a plugin to the dependency graph.

        Args:
            name: Plugin name
            version: Plugin version
            dependencies: List of dependencies
        """
        if name in self._nodes:
            logger.warning(f"Plugin {name} already in graph, updating")

        self._nodes[name] = DependencyNode(
            name=name, version=version, dependencies=dependencies or []
        )

        # Update dependents
        for dep in dependencies or []:
            if dep.name in self._nodes:
                if name not in self._nodes[dep.name].dependents:
                    self._nodes[dep.name].dependents.append(name)

        logger.debug(f"Added plugin to dependency graph: {name} v{version}")

    def get_dependencies(self, plugin_name: str) -> List[PluginDependency]:
        """Get dependencies for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            List of dependencies
        """
        node = self._nodes.get(plugin_name)
        return node.dependencies if node else []

    def get_dependents(self, plugin_name: str) -> List[str]:
        """Get plugins that depend on this plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            List of dependent plugin names
        """
        node = self._nodes.get(plugin_name)
        return node.dependents if node else []

    def has_circular_dependency(self) -> Tuple[bool, Optional[List[str]]]:
        """Check for circular dependencies.

        Returns:
            Tuple of (has_circular, cycle_path)
        """
        visited = set()
        rec_stack = set()

        def visit(node_name: str, path: List[str]) -> Optional[List[str]]:
            if node_name in rec_stack:
                # Found cycle
                cycle_start = path.index(node_name)
                return path[cycle_start:] + [node_name]

            if node_name in visited:
                return None

            visited.add(node_name)
            rec_stack.add(node_name)

            node = self._nodes.get(node_name)
            if node:
                for dep in node.dependencies:
                    if not dep.optional:  # Only check required dependencies
                        cycle = visit(dep.name, path + [node_name])
                        if cycle:
                            return cycle

            rec_stack.remove(node_name)
            return None

        for node_name in self._nodes:
            if node_name not in visited:
                cycle = visit(node_name, [])
                if cycle:
                    return True, cycle

        return False, None

    def topological_sort(self) -> Optional[List[str]]:
        """Get topological sort of plugins (load order).

        Returns:
            List of plugin names in load order, or None if circular dependency
        """
        # Check for circular dependencies first
        has_circular, cycle = self.has_circular_dependency()
        if has_circular:
            logger.error(f"Circular dependency detected: {' -> '.join(cycle)}")
            return None

        visited = set()
        result = []

        def visit(node_name: str):
            if node_name in visited:
                return

            visited.add(node_name)

            node = self._nodes.get(node_name)
            if node:
                # Visit dependencies first
                for dep in node.dependencies:
                    if not dep.optional and dep.name in self._nodes:
                        visit(dep.name)

            result.append(node_name)

        for node_name in self._nodes:
            visit(node_name)

        return result

    def get_load_order(self, plugin_names: List[str]) -> Optional[List[str]]:
        """Get load order for specific plugins.

        Args:
            plugin_names: List of plugin names to load

        Returns:
            Ordered list of plugins to load, or None if error
        """
        # Build subgraph
        subgraph_nodes = set()
        to_process = list(plugin_names)

        while to_process:
            name = to_process.pop(0)
            if name in subgraph_nodes:
                continue

            subgraph_nodes.add(name)

            # Add dependencies
            node = self._nodes.get(name)
            if node:
                for dep in node.dependencies:
                    if not dep.optional and dep.name not in subgraph_nodes:
                        to_process.append(dep.name)

        # Get topological sort of subgraph
        full_order = self.topological_sort()
        if full_order is None:
            return None

        # Filter to only requested plugins and their dependencies
        return [name for name in full_order if name in subgraph_nodes]


class VersionChecker:
    """Check version compatibility."""

    @staticmethod
    def parse_version_spec(spec: str) -> List[Tuple[str, str]]:
        """Parse version specification.

        Args:
            spec: Version spec (e.g., '>=1.0.0,<2.0.0')

        Returns:
            List of (operator, version) tuples
        """
        if spec == "*":
            return []

        parts = [p.strip() for p in spec.split(",")]
        result = []

        for part in parts:
            # Extract operator and version
            if part.startswith(">="):
                result.append((">=", part[2:]))
            elif part.startswith("<="):
                result.append(("<=", part[2:]))
            elif part.startswith(">"):
                result.append((">", part[1:]))
            elif part.startswith("<"):
                result.append(("<", part[1:]))
            elif part.startswith("=="):
                result.append(("==", part[2:]))
            elif part.startswith("!="):
                result.append(("!=", part[2:]))
            else:
                # Assume exact match
                result.append(("==", part))

        return result

    @staticmethod
    def check_version(installed_version: str, version_spec: str) -> bool:
        """Check if installed version satisfies specification.

        Args:
            installed_version: Installed version
            version_spec: Version specification

        Returns:
            True if compatible
        """
        if version_spec == "*":
            return True

        try:
            installed = version.parse(installed_version)
            specs = VersionChecker.parse_version_spec(version_spec)

            for op, ver in specs:
                required = version.parse(ver)

                if op == ">=":
                    if not (installed >= required):
                        return False
                elif op == "<=":
                    if not (installed <= required):
                        return False
                elif op == ">":
                    if not (installed > required):
                        return False
                elif op == "<":
                    if not (installed < required):
                        return False
                elif op == "==":
                    if not (installed == required):
                        return False
                elif op == "!=":
                    if not (installed != required):
                        return False

            return True

        except Exception as e:
            logger.error(f"Error checking version compatibility: {e}")
            return False


class DependencyResolver:
    """Resolve plugin dependencies."""

    def __init__(self):
        """Initialize dependency resolver."""
        self.graph = DependencyGraph()
        self.version_checker = VersionChecker()

    def add_plugin(
        self, name: str, version: str, dependencies: Optional[List[PluginDependency]] = None
    ) -> None:
        """Add a plugin to the resolver.

        Args:
            name: Plugin name
            version: Plugin version
            dependencies: List of dependencies
        """
        self.graph.add_plugin(name, version, dependencies)

    def check_dependencies(
        self, plugin_name: str, available_plugins: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """Check if all dependencies are satisfied.

        Args:
            plugin_name: Plugin name
            available_plugins: Dict of available plugins and their versions

        Returns:
            Tuple of (satisfied, missing_dependencies)
        """
        dependencies = self.graph.get_dependencies(plugin_name)
        missing = []

        for dep in dependencies:
            if dep.optional:
                continue

            if dep.name not in available_plugins:
                missing.append(f"{dep.name} (not installed)")
                continue

            installed_version = available_plugins[dep.name]
            if not self.version_checker.check_version(installed_version, dep.version_spec):
                missing.append(
                    f"{dep.name} (requires {dep.version_spec}, found {installed_version})"
                )

        return len(missing) == 0, missing

    def resolve_load_order(
        self, plugin_names: List[str], available_plugins: Dict[str, str]
    ) -> Tuple[Optional[List[str]], List[str]]:
        """Resolve load order for plugins.

        Args:
            plugin_names: Plugins to load
            available_plugins: Available plugins and versions

        Returns:
            Tuple of (load_order, errors)
        """
        errors = []

        # Check dependencies for each plugin
        for name in plugin_names:
            satisfied, missing = self.check_dependencies(name, available_plugins)
            if not satisfied:
                errors.append(f"Plugin {name} has unsatisfied dependencies: {', '.join(missing)}")

        if errors:
            return None, errors

        # Get load order
        load_order = self.graph.get_load_order(plugin_names)
        if load_order is None:
            errors.append("Circular dependency detected")
            return None, errors

        return load_order, []

    def get_dependency_tree(self, plugin_name: str, depth: int = 0) -> str:
        """Get dependency tree as string.

        Args:
            plugin_name: Plugin name
            depth: Current depth (for indentation)

        Returns:
            Formatted dependency tree
        """
        indent = "  " * depth
        result = f"{indent}{plugin_name}\n"

        dependencies = self.graph.get_dependencies(plugin_name)
        for dep in dependencies:
            optional_marker = " (optional)" if dep.optional else ""
            result += f"{indent}  ├─ {dep.name} {dep.version_spec}{optional_marker}\n"
            if dep.name in self.graph._nodes:
                result += self.get_dependency_tree(dep.name, depth + 2)

        return result

    def validate_all(self, available_plugins: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate all plugins in the graph.

        Args:
            available_plugins: Available plugins and versions

        Returns:
            Tuple of (valid, errors)
        """
        errors = []

        # Check for circular dependencies
        has_circular, cycle = self.graph.has_circular_dependency()
        if has_circular:
            errors.append(f"Circular dependency: {' -> '.join(cycle)}")

        # Check each plugin's dependencies
        for plugin_name in self.graph._nodes:
            satisfied, missing = self.check_dependencies(plugin_name, available_plugins)
            if not satisfied:
                errors.append(f"{plugin_name}: {', '.join(missing)}")

        return len(errors) == 0, errors
