from typing import Optional, Dict, Any, List, Tuple
from functools import lru_cache
import hashlib
import pickle
from datetime import datetime, timedelta

from fluvius.data import DataAccessManager
from .template import template_registry
from .helper import get_render_strategy
from .types import MessageType, RenderStatus, RenderStrategy
from . import logger

class TemplateService:
    """Service for template management and rendering"""

    def __init__(self, stm: DataAccessManager):
        self.stm = stm
        self.cache_ttl = timedelta(hours=1)
    
    async def resolve_template(
        self,
        key: str,
        *,
        tenant_id: Optional[str] = None,
        app_id: Optional[str] = None,
        locale: Optional[str] = None,
        channel: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve template with fallback chain for multi-tenant, locale, and channel variant

        Fallback order:
        1. (tenant_id, app_id, locale, channel)
        2. (tenant_id, app_id, locale, None)
        3. (tenant_id, None, local, None)
        4. (None, None, locale, None)
        5. Repeat with base locale (e.g., 'en' from 'en-US')
        6. Repeat with default locale 'en'
        """
        locales = []
        if locale:
            locales.append(locale)
            # Add base locale (e.g., 'en' from 'en-US)
            if '-' in locale:
                base_locale = locale.split('-')[0]
                if base_locale not in locales:
                    locales.append(base_locale)
            
        if 'en' not in locales:
            locales.append('en')
        
        scopes = [
            {"tenant_id": tenant_id, "app_id": app_id, "channel": channel},
            {"tenant_id": tenant_id, "app_id": app_id, "channel": None},
            {"tenant_id": tenant_id, "app_id": None, "channel": None},
            {"tenant_id": None, "app_id": None, "channel": None},
        ]

        for loc in locales:
            for scope in scopes:
                query = {**scope, "key": key, "locale": loc, "status": "PUBLISHED", "is_active": True}
            
            if version is not None:
                query["version"] = version
            
            #remove None values for cleaner query
            query = {k: v for k, v in query.items() if v is not None}

            template = await self.stm.find_one("message-template", where=query, order_by=["-version"])
            if template:
                logger.debug(f"Resolved template {key} with scope: {query}")
                return template

            logger.warning(f"Template not found: {key} (tenant={tenant_id}, app={app_id}, locale={locale}, channel={channel})")
            return None
        
    async def resolve_render_strategy(
        self,
        message_type: MessageType,
        message_strategy: Optional[RenderStrategy] = None,
        template_strategy: Optional[RenderStrategy] = None
    ):
        """
        Resolve rendering strategy with precedence:
        message.render_strategy > template.render_strategy > type default > SERVER
        """
        return (
            message_strategy 
            or template_strategy
            or get_render_strategy(message_type)
            or RenderStrategy.SERVER
        )

    async def render_template(self, template: Dict[str, Any], data: Dict[str, Any], *, use_cache: bool=True):
        """
            Rendering template with data using appropriate engine.
        """
        engine_name = template.get('engine', 'jinja2')
        template_body = template['body']

        if template.get('variables_schema'):
            self._validate_template_data(data, template['variables_schema'])
        
        # Use cache for CACHED strategy
        if use_cache and template.get('render_strategy') == RenderStrategy.CACHED.value:
            cache_key = self._generate_cache_key(template, data)
            cached_result = await self._get_cached_Render(cache_key)
            if cached_result:
                return cached_result
        
        try:
            rendered = template_registry.render(engine_name, template_body, data)

            # Cache result if using CACHED strategy
            if use_cache and template.get('render_strategy') == RenderStrategy.CACHED.value:
                await self._cache_render_result(cache_key, rendered)
            
            return rendered
        
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            logger.error(f"Template: {template['key']}, Engine: {engine_name}")
            raise ValueError(f"Template rendering failed: {str(e)}")
    
    def _validate_template_data(self, data: Dict[str, Any], schema: Dict[str, Any]):
        """Validate template data against JSON schema."""
        # TODO: Implement JSON schema validation

        required = schema.get('required', [])
        missing = [field for field in required if field not in data]
        if missing:
            raise ValueError(f"Missing required template variables: {missing}")
    
    def _generate_cache_key(self, template: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Generate cache key for template + data combination."""
        key_parts = [
            template['key'],
            str(template['version']),
            template.get('locale', 'en'),
            template.get('channel', ''),
            hashlib.md5(str(sorted(data.items())).encode()).hexdigest()
        ]
        return ":".join(key_parts)
    
    async def _get_cached_render(self, cache_key: str) -> Optional[str]:
        """Get cached render result."""
        #TODO: Implement with Redis or in-memory cache
        return None
    
    async def _cache_render_result(self, cache_key: str, result: str):
        """Cache render result"""
        #TODO: Implement with Redis or in-memory cache
        pass
    
    async def invalidate_template_cache(self, template_key: str, version: Optional[int]=None):
        """Invalidate cached templates for a specific template."""
        #TODO: Implement cache invalidation
        logger.info(f"Template cache invalidated: {template_key} v{version}")
    
    async def create_template(
        self,
        key: str,
        body: str,
        *,
        name: Optional[str] = None,
        engine: str = "jinja2",
        locale: str = "en",
        channel: Optional[str] = None,
        tenant_id: Optional[str] = None,
        app_id: Optional[str] = None,
        variables_schema: Optional[Dict[str, Any]] = None,
        sample_data: Optional[Dict[str, Any]] = None,
        render_strategy: Optional[RenderStrategy] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new template."""
        if not template_registry.get(engine).validate_syntax(body):
            raise ValueError(f"Invalid template syntax for engine: {engine}")
        
        existing = await self.stm.find_many(
            "message-template",
            where={"key": key, "tenant_id": tenant_id, "app_id": app_id, "locale": locale, "channel": channel},
            order_by=["-version"],
            limit=1
        )

        version = (existing[0]['version'] + 1) if existing else 1

        template_data = {
            "key": key,
            "body": body,
            "name": name,
            "engine": engine,
            "locale": locale,
            "channel": channel,
            "tenant_id": tenant_id,
            "app_id": app_id,
            "variables_schema": variables_schema or {},
            "sample_data": sample_data or {},
            "render_strategy": render_strategy.value if render_strategy else None,
            "status": RenderStatus.DRAFT.value,
            "created_by": created_by
        }

        return await self.stm.insert("message-template", template_data)
    
    async def publish_template(self, template_id: str, published_by: Optional[str] = None) -> Dict[str, Any]:
        """Publish a template"""
        template = await self.stm.fetch("message-template", template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        updated = await self.stm.update(template, status=RenderStatus.PUBLISHED.value, _updater=published_by)

        await self.invalidate_template_cache(template['key'], template['version'])

        return updated

