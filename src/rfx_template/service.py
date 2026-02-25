"""
Base Template Service
"""
from typing import Optional, Dict, Any, List
from datetime import timedelta
import hashlib

from fluvius.data import DataAccessManager, serialize_mapping
from fluvius.data.exceptions import ItemNotFoundError

from .engine import template_registry
from . import logger


class BaseTemplateService:
    """
    Base service for template management and rendering.
    """

    def __init__(self, stm: DataAccessManager, table_name: str = "template"):
        self.stm = stm
        self.table_name = table_name
        self.cache_ttl = timedelta(hours=1)

    async def resolve_template(
        self,
        key: str,
        *,
        tenant_id: Optional[str] = None,
        app_id: Optional[str] = None,
        locale: Optional[str] = None,
        channel: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve template with fallback chain for multi-tenant, locale, channel, and product type variants.

        Fallback order:
        1. Exact match (tenant, app, locale, channel, product_type)
        2. Fallback product_type (None) if applicable
        3. Fallback channel (None) if applicable
        4. Fallback app (None)
        5. Fallback tenant (None)
        6. Fallback locale (base locale, then 'en', then None)
        """
        locales = self._get_locale_fallbacks(locale)


        # Define scopes ordered by specificity
        # Note: We iterate scopes inside the locale loop to prioritized localized version first
        scopes = []

        scopes.append({"tenant_id": tenant_id, "app_id": app_id, "channel": channel})

        # If channel is provided, we can fallback to generic channel (None)
        if channel is not None:
            scopes.append({"tenant_id": tenant_id, "app_id": app_id, "channel": None})

        # Fallback to no app
        scopes.append({"tenant_id": tenant_id, "app_id": None, "channel": channel})
        if channel is not None:
            scopes.append({"tenant_id": tenant_id, "app_id": None, "channel": None})

        # Fallback to no tenant
        scopes.append({"tenant_id": None, "app_id": None, "channel": channel})
        if channel is not None:
            scopes.append({"tenant_id": None, "app_id": None, "channel": None})

        # Remove duplicates if any (e.g. if tenant_id is None, some scopes might be identical)
        # Using a list of tuples to track uniqueness
        unique_scopes = []
        seen = set()
        for s in scopes:
            t = tuple(sorted(s.items()))
            if t not in seen:
                seen.add(t)
                unique_scopes.append(s)

        for loc in locales:
            for scope in unique_scopes:
                template = await self._find_template_for_scope(key, scope, loc, version)
                if template:
                    return template

        logger.warning(
            f"Template not found: {key} (tenant={tenant_id}, app={app_id}, locale={locale}, channel={channel})"
        )
        return None

    async def _find_template_for_scope(
        self,
        key: str,
        scope: Dict[str, Any],
        loc: Optional[str],
        version: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch template candidates using only non-None scope fields in the DB query,
        then verify in Python that fields which are None in the scope are also None
        on the returned record.

        The query builder does not translate Python None -> SQL IS NULL (it generates
        `col = NULL` which never matches). By omitting None-valued fields from the DB
        query and checking them in Python afterwards, we correctly handle NULL columns.
        """
        # Build DB query with non-None fields only; track which fields must be NULL.
        query: Dict[str, Any] = {"key": key, "is_active": True}
        none_fields: List[str] = []

        for field_name, value in scope.items():
            if value is not None:
                query[field_name] = value
            else:
                none_fields.append(field_name)

        if loc is not None:
            query["locale"] = loc
        # When loc is None: omit locale from both the DB query and none_fields.
        # This is the "any locale" last-resort fallback — accept any matching record
        # regardless of locale. (locale is NOT NULL so checking IS NULL would never match.)

        if version is not None:
            query["version"] = version

        try:
            candidates = await self.stm.find_all(self.table_name, where=query)
        except ItemNotFoundError:
            return None

        if not candidates:
            return None

        # Post-filter in Python: only accept a candidate where every field that
        # should be NULL is actually NULL on the record.
        for candidate in candidates:
            if all(getattr(candidate, f, None) is None for f in none_fields):
                logger.info(
                    f"Resolved template {key} with scope: {query}, null_fields: {none_fields}"
                )
                return serialize_mapping(candidate)

        return None

    def _get_locale_fallbacks(self, locale: Optional[str]) -> List[Optional[str]]:
        """Generate list of locales to try."""
        locales = []
        if locale:
            locales.append(locale)
            if '-' in locale:
                base_locale = locale.split('-')[0]
                if base_locale not in locales:
                    locales.append(base_locale)

        if 'en' not in locales:
            locales.append('en')

        # Add None to try getting a template with no locale specified, or fallback to any layout
        locales.append(None)

        return locales

    async def render_template(
        self,
        template: Dict[str, Any],
        data: Dict[str, Any],
        template_content_key: str = "body"
    ) -> str:
        """
        Render a specific part of the template (e.g., body, subject).

        Args:
            template: The template dictionary
            data: Data context
            template_content_key: Key in the template dict that holds the template string (e.g. 'body_template')
        """
        engine_name = template.get('engine', 'jinja2')
        template_body = template.get(template_content_key)

        if not template_body:
            return ""

        if template.get('variables_schema'):
            self._validate_template_data(data, template.get('variables_schema'))

        try:
            return template_registry.render(engine_name, template_body, data)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            logger.error(f"Template: {template.get('key')}, Engine: {engine_name}")
            raise ValueError(f"Template rendering failed: {str(e)}")

    def _validate_template_data(self, data: Dict[str, Any], schema: Dict[str, Any]):
        """Validate template data against JSON schema."""
        # TODO: Implement full JSON schema validation using jsonschema lib
        required = schema.get('required', [])
        missing = [field for field in required if field not in data]
        if missing:
             # Basic check for top-level keys
            raise ValueError(f"Missing required template variables: {missing}")

    async def create_template_base(
        self,
        key: str,
        data: Dict[str, Any],
        unique_keys: List[str] = None
    ) -> Dict[str, Any]:
        """
        Base helper for creating templates.
        Calculates version based on distinct keys.
        """
        if not unique_keys:
            unique_keys = ["key", "tenant_id", "app_id", "locale", "channel"]

        where_clause = {k: data.get(k) for k in unique_keys if k in data}

        existing = await self.stm.find_all(
            self.table_name,
            where=where_clause,
            order_by=["-version"],
            limit=1
        )

        # Handle versioning
        current_version = 0
        if existing:
            latest = existing[0]
            current_version = getattr(latest, 'version', 0)

        version = current_version + 1
        data['version'] = version

        return await self.stm.insert(self.table_name, data)
