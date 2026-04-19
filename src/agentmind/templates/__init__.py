"""Template marketplace for pre-configured agent teams.

Provides 20+ built-in templates for common multi-agent scenarios.
"""

from .loader import TemplateLoader, load_template
from .registry import TemplateRegistry, get_registry

__all__ = ["TemplateLoader", "TemplateRegistry", "load_template", "get_registry"]
