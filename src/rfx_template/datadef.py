from typing import Optional, Dict, Any
from fluvius.data import DataModel, Field

class CreateTemplatePayload(DataModel):
    key: str
    name: Optional[str] = None
    description: Optional[str] = None
    body: str  # Content for the template
    engine: str = "jinja2"
    locale: str = "en"
    channel: Optional[str] = None
    variables_schema: Dict[str, Any] = Field(default_factory=dict)
    meta_fields: Dict[str, Any] = Field(default_factory=dict)  # Domain-specific data
    tenant_id: Optional[str] = None
    app_id: Optional[str] = None

class UpdateTemplatePayload(DataModel):
    name: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    engine: Optional[str] = None
    variables_schema: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class RenderTemplatePayload(DataModel):
    key: str
    data: Dict[str, Any] = Field(default_factory=dict)

    # Context for resolution
    tenant_id: Optional[str] = None
    app_id: Optional[str] = None
    locale: Optional[str] = None
    channel: Optional[str] = None
    version: Optional[int] = None
