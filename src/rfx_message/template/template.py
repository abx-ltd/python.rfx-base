from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import re
from jinja2 import Environment, StrictUndefined, select_autoescape
import markdown
from markupsafe import Markup

from .. import logger

class TemplateEngine(ABC):
    """Base class for template engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Engine name"""
        pass

    @abstractmethod
    def render(self, template_body: str, data: Dict[str, Any]) -> str:
        """Render the template with the provided data."""
        pass

    def validate_syntax(self, template_body: str) -> bool:
        """Validate template syntax. Returns True if valid."""
        try:
            self.render(template_body, {})
            return True
        except Exception as e:
            logger.warning(f"Template syntax error in {self.name}: {e}")
            return False

class JinjaEngine(TemplateEngine):
    """Jinja template engine for HTML/text templates."""

    def __init__(self):
        self.env = Environment(
            undefined=StrictUndefined,
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # self.env.filters['currency'] = lambda x: f"${x:,.2f}"
        # self.env.filters['datetime'] = lambda x, fmt='%Y-%m-%d %H:%M': x.strftime(fmt)

    @property
    def name(self) -> str:
        return "jinja2"
    
    def render(self, template_body: str, data: Dict[str, Any]) -> str:
        template = self.env.from_string(template_body)
        return template.render(**data)

class TextEngine(TemplateEngine):
    """Simple text template engine with basic variable substitution"""

    @property
    def name(self) -> str:
        return "txt"
    
    def render(self, template_body: str, data: Dict[str, Any]) -> str:
        """Simple variable substituion."""
        result = template_body
        for key, value in data.items():
            placeholder = f"${{{key}}}"
            result = result.replace(placeholder, str(value))
        return result

class MarkdownEngine(TemplateEngine):
    """Markdown template engine with variable substitution."""

    def __init__(self):
        self.md = markdown.Markdown(
            extensions=['extra', 'codehilite', 'toc'],
            extension_configs={
                'codehilite': {'css_class': 'highlight'}
            }
        )
    
    @property
    def name(self) -> str:
        return "markdown"
    
    def render(self, template_body: str, data: Dict[str, Any]) -> str:
        text_engine = TextEngine()
        substitude = text_engine.render(template_body, data)

        return self.md.convert(substitude)

class StaticEngine(TemplateEngine):
    """Static template engine"""

    @property
    def name(self) -> str:
        return "static"
    
    def render(self, template_body: str, data: Dict[str, Any]) -> str:
        return template_body
    
class TemplateEngineRegistry:
    """Registry for managing template engines"""

    def __init__(self):
        self._engines: Dict[str, TemplateEngine] = {}
        self._register_default_engines()

    def _register_default_engines(self):
        """Register built-in template engines"""

        engines = [
            JinjaEngine(),
            TextEngine(),
            MarkdownEngine(),
            StaticEngine()
        ]
        for engine in engines:
            self.register(engine)
    
    def register(self, engine: TemplateEngine):
        """Register a template engine."""
        self._engines[engine.name] = engine
        logger.info(f"Registered template engine: {engine.name}")
    
    def get(self, name: str) -> Optional[TemplateEngine]:
        """Get a template engine by name."""
        return self._engines.get(name)
    
    def list_engines(self) -> Dict[str, TemplateEngine]:
        """List all registered template engines."""
        return self._engines.copy()
    
    def render(self, engine_name: str, template_body: str, data: Dict[str, Any]) -> str:
        """Render template using specified engine"""
        engine = self.get(engine_name)
        if not engine:
            raise ValueError(f"Template engine '{engine_name}' not found")
        
        try:
            return engine.render(template_body, data)
        except Exception as e:
            logger.error(f"Template rendering failed with {engine_name}: {e}")

template_registry = TemplateEngineRegistry()