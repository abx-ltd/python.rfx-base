"""
Template Service for Notification Templates
"""
from typing import Optional, Dict, Any
from fluvius.data import DataAccessManager
from fluvius.data.exceptions import ItemNotFoundError

from .engine import template_registry
from .. import logger


class NotificationTemplateService:
    """Service for notification template management and rendering"""

    def __init__(self, stm: DataAccessManager):
        self.stm = stm

    async def resolve_template(
        self,
        key: str,
        channel: str,
        *,
        tenant_id: Optional[str] = None,
        app_id: Optional[str] = None,
        locale: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve notification template with fallback chain for multi-tenant, locale variants.

        Fallback order:
        1. (tenant_id, app_id, channel, locale)
        2. (tenant_id, app_id, channel, None)
        3. (tenant_id, None, channel, None)
        4. (None, None, channel, locale)
        5. (None, None, channel, None) - base template

        Args:
            key: Template key
            channel: Notification channel (EMAIL, SMS, etc.)
            tenant_id: Optional tenant ID for multi-tenancy
            app_id: Optional app ID
            locale: Optional locale (e.g., 'en', 'en-US')
            version: Optional specific version

        Returns:
            Template dict or None if not found
        """
        locales = []
        if locale:
            locales.append(locale)
            # Add base locale (e.g., 'en' from 'en-US')
            if '-' in locale:
                base_locale = locale.split('-')[0]
                if base_locale not in locales:
                    locales.append(base_locale)

        if 'en' not in locales:
            locales.append('en')

        # Try without locale first if no locale specified
        if not locale:
            locales = [None]

        scopes = [
            {"tenant_id": tenant_id, "app_id": app_id},
            {"tenant_id": tenant_id, "app_id": None},
            {"tenant_id": None, "app_id": None},
        ]

        for loc in locales:
            for scope in scopes:
                query = {
                    **scope,
                    "key": key,
                    "channel": channel,
                    "is_active": True,
                }

                if loc:
                    query["locale"] = loc

                if version is not None:
                    query["version"] = version

                query = {k: v for k, v in query.items() if v is not None}

                try:
                    template = await self.stm.find_one("notification_template", where=query)
                    if template:
                        logger.debug(f"Resolved template {key} for {channel} with scope: {query}")
                        return template
                except ItemNotFoundError:
                    continue

        logger.warning(
            f"Template not found: {key} (channel={channel}, tenant={tenant_id}, "
            f"app={app_id}, locale={locale})"
        )
        return None

    async def render_template(
        self,
        template: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Render notification template with data using appropriate engine.

        Args:
            template: Template dict with body_template, subject_template, engine
            data: Data to render template with

        Returns:
            Dictionary with rendered 'subject' and 'body'
        """
        engine_name = template.get('engine', 'jinja2')

        # Validate data against schema if provided
        if template.get('variables_schema'):
            self._validate_template_data(data, template['variables_schema'])

        try:
            rendered = {}

            # Render body
            if template.get('body_template'):
                rendered['body'] = template_registry.render(
                    engine_name,
                    template['body_template'],
                    data
                )

            # Render subject (for email)
            if template.get('subject_template'):
                rendered['subject'] = template_registry.render(
                    engine_name,
                    template['subject_template'],
                    data
                )

            return rendered

        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            logger.error(f"Template: {template.get('key')}, Engine: {engine_name}")
            raise ValueError(f"Template rendering failed: {str(e)}")

    def _validate_template_data(self, data: Dict[str, Any], schema: Dict[str, Any]):
        """Validate template data against JSON schema."""
        # TODO: Implement full JSON schema validation
        required = schema.get('required', [])
        missing = [field for field in required if field not in data]
        if missing:
            raise ValueError(f"Missing required template variables: {missing}")

    async def create_template(
        self,
        key: str,
        channel: str,
        body_template: str,
        *,
        subject_template: Optional[str] = None,
        name: Optional[str] = None,
        engine: str = "jinja2",
        locale: str = "en",
        content_type: str = "TEXT",
        tenant_id: Optional[str] = None,
        app_id: Optional[str] = None,
        variables_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new notification template.

        Args:
            key: Template key
            channel: Notification channel
            body_template: Template body
            subject_template: Optional subject template (for email)
            name: Optional friendly name
            engine: Template engine (default: jinja2)
            locale: Locale (default: en)
            content_type: Content type (TEXT, HTML, etc.)
            tenant_id: Optional tenant ID
            app_id: Optional app ID
            variables_schema: Optional JSON schema for variables

        Returns:
            Created template dict
        """
        # Validate template syntax
        template_engine = template_registry.get(engine)
        if not template_engine:
            raise ValueError(f"Unknown template engine: {engine}")

        if not template_engine.validate_syntax(body_template):
            raise ValueError(f"Invalid template syntax for engine: {engine}")

        if subject_template and not template_engine.validate_syntax(subject_template):
            raise ValueError(f"Invalid subject template syntax for engine: {engine}")

        # Find existing versions
        existing = await self.stm.find_all(
            "notification_template",
            where={
                "key": key,
                "channel": channel,
                "tenant_id": tenant_id,
                "app_id": app_id,
                "locale": locale
            },
            order_by=["-version"],
            limit=1
        )

        version = (existing[0]['version'] + 1) if existing else 1

        template_data = {
            "key": key,
            "channel": channel,
            "body_template": body_template,
            "subject_template": subject_template,
            "name": name or key,
            "engine": engine,
            "locale": locale,
            "content_type": content_type,
            "tenant_id": tenant_id,
            "app_id": app_id,
            "variables_schema": variables_schema or {},
            "version": version,
            "is_active": True,
        }

        return await self.stm.insert("notification_template", template_data)

    async def activate_template(self, template_id: str) -> Dict[str, Any]:
        """Activate a template."""
        template = await self.stm.fetch("notification_template", template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        return await self.stm.update(template, is_active=True)

    async def deactivate_template(self, template_id: str) -> Dict[str, Any]:
        """Deactivate a template."""
        template = await self.stm.fetch("notification_template", template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        return await self.stm.update(template, is_active=False)
