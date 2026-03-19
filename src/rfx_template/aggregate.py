"""
Template Aggregate
"""
from typing import Dict, Any, Optional
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import DataAccessManager, serialize_mapping
from .service import BaseTemplateService


class TemplateAggregate(Aggregate):
    """
    Aggregate for handling template commands.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._template_service = None

    @property
    def template_service(self) -> BaseTemplateService:
        """Lazy-loaded template service."""
        if self._template_service is None:
            self._template_service = BaseTemplateService(self.statemgr, table_name="template")
        return self._template_service

    @action("template_created", resources=("template", ))
    async def create_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new template."""
        # This generic create handles the logic
        # We might need to determine WHICH table to write to if we support multiple types,
        # or we enforce a single `template` table.
        # For a separate domain, it should handle its own data.
        return await self.template_service.create_template_base(
            key=data['key'],
            data=data
        )

    @action("template_updated", resources=("template", ))
    async def update_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing template."""
        template = self.get_rootobj()
        updated_template = await self.statemgr.update(template, **data)
        return serialize_mapping(updated_template)

    @action("template_rendered", resources=("template", ))
    async def render_template(self, data):
        """Resolve and render a template."""
        key = data.get('key')
        context = {
            'tenant_id': data.get('tenant_id'),
            'app_id': data.get('app_id'),
            'locale': data.get('locale'),
            'channel': data.get('channel'),
            'version': data.get('version'),
        }

        # Resolve template through service
        template_dict = await self.template_service.resolve_template(key, **context)

        if not template_dict:
            raise ValueError(f"Template not found: {key}")

        # Render main body content
        render_data = data.get('data', {})
        rendered_body = await self.template_service.render_template(template_dict, render_data, template_content_key='body')

        result = {'body': rendered_body}

        # Render meta_fields templates (e.g., subject for notifications)
        meta_fields = template_dict.get('meta_fields', {})
        if meta_fields:
            for meta_key, meta_template in meta_fields.items():
                if isinstance(meta_template, str):
                    # Render meta_fields template using the same engine
                    engine_name = template_dict.get('engine', 'jinja2')
                    from .engine import template_registry
                    engine = template_registry.get(engine_name)
                    if engine:
                        result[meta_key] = engine.render(meta_template, render_data)

        # Log rendering event
        try:
            log_record = {
                'template_key': key,
                'template_version': template_dict.get('version'),
                'tenant_id': context['tenant_id'],
                'app_id': context['app_id'],
                'locale': context['locale'],
                'channel': context['channel'],
                'parameters': render_data
            }

            record = self.init_resource("template_render_log", log_record)
            await self.statemgr.insert(record)
        except Exception as e:
            # Log error but don't fail rendering
            raise e

        return result
