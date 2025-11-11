"""
Template module for notification templates
"""
from .engine import template_registry, TemplateEngine
from .service import NotificationTemplateService
from .. import logger, config

__all__ = ['template_registry', 'TemplateEngine', 'NotificationTemplateService']
