"""
RFX User Domain Data Definitions

Pydantic payload models for API operations and data validation.
Used by command handlers for input validation and serialization.
"""

from typing import Optional, List
from pydantic import Field

from fluvius.data import DataModel, UUID_TYPE

from .types import OrganizationStatusEnum

class CreateOrganizationPayload(DataModel):
    """Payload for creating new organizations."""
    description: Optional[str]
    name: str = Field(max_length=255)
    tax_id: Optional[str] = Field(max_length=9)
    business_name: Optional[str]
    system_entity: Optional[bool] = False
    active: Optional[bool] = True
    system_tag: Optional[List[str]] = []
    user_tag: Optional[List[str]] = []
    status: OrganizationStatusEnum = 'ACTIVE'
    organization_code: Optional[str] = Field(max_length=255, default=None)
    invitation_code: Optional[str] = Field(max_length=10, default=None)
    type: Optional[str] = None # FK to RefOrganizationType.key

UpdateOrganizationPayload = CreateOrganizationPayload

class CreateProfilePayload(DataModel):
    """Payload for creating user profiles within organizations."""
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

UpdateProfilePayload = CreateProfilePayload

class SendActionPayload(DataModel):
    """Payload for sending user actions (password reset, email verification)."""
    actions: list
    required: Optional[bool] = False

class SendInvitationPayload(DataModel):
    """Payload for sending organization invitations."""
    email: str
    duration: int
    message: str | None = None

class AssignRolePayload(DataModel):
    """Payload for assigning roles to profiles."""
    role_id: UUID_TYPE
    role_source: str = 'SYSTEM'

class RevokeRolePayload(DataModel):
    """Payload for revoking roles from profiles."""
    profile_role_id: UUID_TYPE

class CreateOrgRolePayload(DataModel):
    """Payload for creating custom organization roles."""
    active: Optional[bool] = True
    description: Optional[str]
    name: str
    key: str

class UpdateOrgRolePayload(DataModel):
    """Payload for updating organization roles."""
    role_id: UUID_TYPE
    updates: CreateOrgRolePayload

class RemoveOrgRolePayload(DataModel):
    """Payload for removing organization roles."""
    role_id: UUID_TYPE

class AddGroupToProfilePayload(DataModel):
    """Payload for adding profiles to security groups."""
    group_id: UUID_TYPE
    profile_id: Optional[UUID_TYPE] = None

class RemoveGroupFromProfilePayload(DataModel):
    """Payload for removing profiles from security groups."""
    profile_group_id: UUID_TYPE

class CreateGroupPayload(DataModel):
    """Payload for creating security groups."""
    active: Optional[bool] = True
    description: Optional[str] = Field(max_length=1024)
    name: str = Field(max_length=1024)
    resource: Optional[str] = None
    resource_id: Optional[UUID_TYPE] = None

class UpdateGroupPayload(DataModel):
    """Payload for updating security groups."""
    description: Optional[str] = Field(max_length=1024)
    name: Optional[str] = Field(max_length=1024)
    resource: Optional[str] = None
    resource_id: Optional[UUID_TYPE] = None
    active: Optional[bool] = None

class SyncUserPayload(DataModel):
    """Payload for synchronizing user data with Keycloak."""
    force: Optional[bool] = False  # Force sync even if recently synced
    sync_actions: Optional[bool] = True  # Whether to sync required actions
    user_data: dict  # User data from Keycloak
    required_actions: Optional[list[str]] = []  # Required actions from Keycloak
