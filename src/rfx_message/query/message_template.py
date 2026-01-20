from pydantic import BaseModel
from typing import Optional
from fluvius.query import DomainQueryResource
from fluvius.query.field import (
    StringField,
    IntegerField,
    JSONField,
    EnumField,
    BooleanField,
    UUIDField,
)
from fluvius.data import UUID_TYPE
from .manager import resource
from ..types import RenderStrategyEnum


class TemplateScope(BaseModel):
    tenant_id: Optional[str] = None
    app_id: Optional[str] = None
    locale: Optional[str] = None
    channel: Optional[str] = None


@resource("message-template")
class MessageTemplateQuery(DomainQueryResource):
    """Query resource for message templates."""

    @classmethod
    def base_query(cls, context, scope):
        # Templates are typically scoped by tenant/app
        filters = {}

        if hasattr(context, "tenant_id") and context.tenant_id:
            filters["tenant_id"] = context.tenant_id

        if hasattr(context, "app_id") and context.app_id:
            filters["app_id"] = context.app_id

        return filters

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        allow_text_search = True

        backend_model = "message_template"
        resource = "message_template"
        policy_required = "id"
        scope_optional = TemplateScope

        default_order = ("key", "-version")

    # Template identity
    # id: UUID_TYPE = UUIDField("Template ID")
    key: str = StringField("Template Key")
    version: int = IntegerField("Version")
    name: str = StringField("Template Name")
    # Template content
    engine: str = StringField("Template Engine")
    body: str = StringField("Template Body")
    description: Optional[str] = StringField("Description")
    # Scoping
    locale: str = StringField("Locale")
    channel: Optional[str] = StringField("Channel")
    tenant_id: Optional[UUID_TYPE] = UUIDField("Tenant ID")
    app_id: Optional[str] = StringField("App ID")
    # Configuration
    render_strategy: Optional[RenderStrategyEnum] = EnumField(
        "Render Strategy", enum=RenderStrategyEnum
    )
    variables_schema: dict = JSONField("Variables Schema")
    sample_data: dict = JSONField("Sample Data")
    # Status
    status: str = StringField("Status")
    is_active: bool = BooleanField("Is Active")
    # Audit
    created_by: Optional[UUID_TYPE] = UUIDField("Created By")
    updated_by: Optional[UUID_TYPE] = UUIDField("Updated By")
