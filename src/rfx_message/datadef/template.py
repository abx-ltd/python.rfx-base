from typing import Optional, Dict, Any
from pydantic import Field
from fluvius.data import DataModel, UUID_TYPE


class CreateTemplatePayload(DataModel):
    """Payload for creating message templates."""

    key: str = Field(..., description="Template key identifier")
    name: Optional[str] = Field(None, description="Human-readable template name")
    context: str = Field(..., description="Template body/source code")

    # Template configuration
    engine: str = Field("jinja2", description="Template engine")
    locale: str = Field("en", description="Template locale")
    channel: Optional[str] = Field(None, description="Template channel")
    version: Optional[int] = Field(None, description="Template version number")

    # Multi-tenant scoping
    tenant_id: Optional[UUID_TYPE] = Field(None, description="Tenant ID")
    app_id: Optional[str] = Field(None, description="App ID")

    # Template metadata
    description: Optional[str] = Field(None, description="Template description")
    variables_schema: Optional[Dict[str, Any]] = Field(
        {}, description="JSON schema for template variables"
    )
    # sample_data: Optional[Dict[str, Any]] = Field({}, description="Sample data for testing")

    # Rendering control
    render_strategy: Optional[str] = Field(
        None, description="Default rendering strategy"
    )

