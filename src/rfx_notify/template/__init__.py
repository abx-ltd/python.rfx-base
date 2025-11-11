"""
Template module for notification templates
"""
from .engine import template_registry, TemplateEngine
from .service import NotificationTemplateService

__all__ = ['template_registry', 'TemplateEngine', 'NotificationTemplateService']
