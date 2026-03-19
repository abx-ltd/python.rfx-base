"""
Template Queries
"""
from typing import Optional
from pydantic import BaseModel
from fluvius.query import DomainQueryResource, DomainQueryManager
from fluvius.query.field import (
    StringField,
    IntegerField,
    JSONField,
    EnumField,
    BooleanField,
    UUIDField,
)
from fluvius.data import UUID_TYPE
from ._meta import config
from .state import TemplateStateManager
from .domain import TemplateServiceDomain

class TemplateServiceQueryManager(DomainQueryManager):
    __data_manager__ = TemplateStateManager

    class Meta(DomainQueryManager.Meta):
        prefix = TemplateServiceDomain.Meta.namespace
        tags = TemplateServiceDomain.Meta.tags

resource = TemplateServiceQueryManager.register_resource
endpoint = TemplateServiceQueryManager.register_endpoint

class TemplateScope(BaseModel):
    tenant_id: Optional[str] = None
    app_id: Optional[str] = None
    locale: Optional[str] = None
    channel: Optional[str] = None


@resource("template")
class TemplateQuery(DomainQueryResource):

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_text_search = True

        backend_model = "template"
        resource = "template"
        default_order = ("key", "-version")

    key: str = StringField("Template Key")
    version: int = IntegerField("Version")
    name: str = StringField("Template Name")
    description: Optional[str] = StringField("Description")

    locale: str = StringField("Locale")
    channel: Optional[str] = StringField("Channel")
    engine: str = StringField("Template Engine")

    variables_schema: dict = JSONField("Variables Schema")
    is_active: bool = BooleanField("Is Active")

    tenant_id: Optional[UUID_TYPE] = UUIDField("Tenant ID")
    app_id: Optional[str] = StringField("App ID")
