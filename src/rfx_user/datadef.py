# models.py
from fluvius.data import DataModel
from typing import Optional, List
from pydantic import Field
from .types import OrganizationStatus

class OrganizationPayload(DataModel):
    description: Optional[str]
    name: str = Field(max_length=255)
    tax_id: Optional[str] = Field(max_length=9)
    business_name: Optional[str]
    system_entity: Optional[bool] = False
    active: Optional[bool] = True
    system_tag: Optional[List[str]] = []
    user_tag: Optional[List[str]] = []
    status: OrganizationStatus = 'ACTIVE'
    organization_code: Optional[str] = Field(max_length=255)
    invitation_code: Optional[str] = Field(max_length=10)
    type: Optional[str]  # FK to RefOrganizationType.key

UpdateOrganizationPayload = OrganizationPayload
CreateOrganizationPayload = OrganizationPayload