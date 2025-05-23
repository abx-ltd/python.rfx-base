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

class ProfilePayload(DataModel):
    access_tags: list[str] = []
    active: bool

    address__city: str
    address__country: str
    address__line1: str
    address__line2: str
    address__postal: str
    address__state: str

    picture_id: str | None
    birthdate: str | None
    expiration_date: str | None
    gender: str | None

    language: list[str] = []
    last_login: str | None

    name__family: str
    name__given: str
    name__middle: str
    name__prefix: str
    name__suffix: str

    realm: str
    svc_access: str
    svc_secret: str
    user_tag: list[str] = []

    telecom__email: str
    telecom__fax: str
    telecom__phone: str

    tfa_method: str
    tfa_token: str
    two_factor_authentication: bool

    upstream_user_id: str | None
    user_type: str
    username: str

    verified_email: str
    verified_phone: str
    primary_language: str

    last_sync: str | None
    is_super_admin: bool
    system_tag: list[str] = []
    status: str

    preferred_name: str
    default_theme: str

    user_id: str | None
    current_profile: bool
    organization_id: str | None

UpdateProfilePayload = ProfilePayload
CreateProfilePayload = ProfilePayload
