"""
RFX IDM Domain Data Definitions

Pydantic payload models for API operations and data validation.
Used by command handlers for input validation and serialization.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import Field, model_validator


from fluvius.data import DataModel, UUID_TYPE

from .types import OrganizationStatusEnum, ProfileStatusEnum, UserStatusEnum


class CreateUserPayload(DataModel):
    """Payload for creating new users."""
    # Required fields
    username: str
    email: str

    # Name fields (map to name__* in UserSchema)
    first_name: Optional[str] = None  # -> name__given
    last_name: Optional[str] = None   # -> name__family
    middle_name: Optional[str] = None # -> name__middle
    name_prefix: Optional[str] = None # -> name__prefix
    name_suffix: Optional[str] = None # -> name__suffix

    # Telecom fields
    phone: Optional[str] = None       # -> telecom__phone

    # Authentication
    password: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

    # Verification
    email_verified: Optional[bool] = True
    verified_email: Optional[str] = None
    verified_phone: Optional[str] = None

    # Access control (JSON fields)
    realm_access: Optional[dict] = None
    resource_access: Optional[dict] = None

    # Tags
    system_tag: Optional[List[str]] = []
    user_tag: Optional[List[str]] = []


class UpdateUserPayload(DataModel):
    """Payload for updating existing users."""
    username: Optional[str] = None
    email: Optional[str] = None

    # Name fields (map to name__* in UserSchema)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    name_prefix: Optional[str] = None
    name_suffix: Optional[str] = None

    # Telecom fields
    phone: Optional[str] = None

    # Authentication + status
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    status: Optional[UserStatusEnum] = None

    # Verification metadata
    email_verified: Optional[bool] = True
    verified_email: Optional[str] = None
    verified_phone: Optional[str] = None
    last_verified_request: Optional[datetime] = None

    # Access control (JSON fields)
    realm_access: Optional[dict] = None
    resource_access: Optional[dict] = None

    # Tags
    system_tag: Optional[List[str]] = None
    user_tag: Optional[List[str]] = None

    # Sync options
    sync_remote: bool = False
    force_sync: bool = False
    sync_actions: bool = True

    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        """Ensure update payload contains at least one field or an explicit sync instruction."""
        field_values = self.model_dump(
            exclude_none=True,
            exclude={"sync_remote", "force_sync", "sync_actions"}
        )
        if not field_values and not (self.sync_remote or self.force_sync):
            raise ValueError("Provide update fields or enable sync_remote/force_sync")
        return self

class CreateOrganizationPayload(DataModel):
    """Payload for creating new organizations."""
    description: Optional[str]
    name: str = Field(max_length=255)
    business_name: Optional[str]
    system_entity: Optional[bool] = False
    active: Optional[bool] = True
    system_tag: Optional[List[str]] = []
    user_tag: Optional[List[str]] = []
    organization_code: Optional[str] = Field(max_length=255, default=None)
    invitation_code: Optional[str] = Field(max_length=10, default=None)
    # type: Optional[str] = None # FK to RefOrganizationType.key


class UpdateOrganizationPayload(DataModel):
    description: Optional[str] = None
    name: Optional[str] = Field(max_length=255, default=None)
    business_name: Optional[str] = None
    system_entity: Optional[bool] = None
    active: Optional[bool] = None
    system_tag: Optional[List[str]] = None
    user_tag: Optional[List[str]] = None
    status: Optional[OrganizationStatusEnum] = None
    organization_code: Optional[str] = Field(max_length=255, default=None)
    invitation_code: Optional[str] = Field(max_length=10, default=None)
    type: Optional[str] = None # FK to RefOrganizationType.key

    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        field_values = self.model_dump(exclude_none=True)
        if not field_values:
            raise ValueError("At least one field must be provided for update")
        return self


class CreateProfilePayload(DataModel):
    """Payload for creating user profiles within organizations."""
    user_id: str = Field(default=None)
    access_tags: list[str] = []
    active: Optional[bool] = Field(default=True)

    address__city: Optional[str] = None
    address__country: Optional[str] = None
    address__line1: Optional[str] = None
    address__line2: Optional[str] = None
    address__postal: Optional[str] = None
    address__state: Optional[str] = None

    picture_id: Optional[str] = None
    birthdate: Optional[date] = None
    expiration_date: Optional[datetime] = None
    gender: Optional[str] = None

    language: list[str] = []
    last_login: Optional[datetime] = None

    name__family: str
    name__given: str
    name__middle: Optional[str] = None
    name__prefix: Optional[str] = None
    name__suffix: Optional[str] = None

    realm: Optional[str] = None
    svc_access: Optional[str] = None
    svc_secret: Optional[str] = None
    user_tag: Optional[list[str]] = None

    telecom__email: str
    telecom__fax: Optional[str] = None
    telecom__phone: str


    tfa_method: Optional[str] = None
    tfa_token: Optional[str] = None
    two_factor_authentication: Optional[bool] = Field(default=False)

    upstream_user_id: Optional[str] = None
    user_type: Optional[str] = None

    verified_email: Optional[str] = None
    verified_phone: Optional[str] = None
    primary_language: Optional[str] = Field(default="en")

    last_sync: Optional[datetime] = None
    is_super_admin: Optional[bool] = Field(default=False)
    system_tag: Optional[list[str]] = None
    status: Optional[str] = Field(default=ProfileStatusEnum.ACTIVE.value)

    preferred_name: Optional[str] = None
    default_theme: Optional[str] = None
    role_keys: list[str] = Field(default_factory=lambda: ["VIEWER"])

class CreateProfileInOrgPayload(CreateProfilePayload):
    """Payload for creating user profiles within organizations."""
    organization_id: str


class UpdateProfilePayload(DataModel):
    """Payload for updating user profiles within organizations."""
    address__city: Optional[str] = None
    address__country: Optional[str] = None
    address__line1: Optional[str] = None
    address__line2: Optional[str] = None
    address__postal: Optional[str] = None
    address__state: Optional[str] = None

    picture_id: Optional[str] = None
    birthdate: Optional[date] = None
    expiration_date: Optional[datetime] = None
    gender: Optional[str] = None

    language: list[str] = None
    last_login: Optional[datetime] = None

    name__family: Optional[str] = None
    name__given: Optional[str] = None
    name__middle: Optional[str] = None
    name__prefix: Optional[str] = None
    name__suffix: Optional[str] = None

    realm: Optional[str] = None
    svc_access: Optional[str] = None
    svc_secret: Optional[str] = None
    user_tag: list[str] = None

    telecom__email: Optional[str] = None
    telecom__fax: Optional[str] = None
    telecom__phone: Optional[str] = None

    tfa_method: Optional[str] = None
    tfa_token: Optional[str] = None
    two_factor_authentication: Optional[bool] = None

    upstream_user_id: Optional[str] = None
    user_type: Optional[str] = None
    username: Optional[str] = None

    verified_email: Optional[str] = None
    verified_phone: Optional[str] = None
    primary_language: Optional[str] = None

    last_sync: Optional[datetime] = None
    is_super_admin: Optional[bool] = None
    system_tag: Optional[list[str]] = None
    status: Optional[str] = None

    preferred_name: Optional[str] = None
    default_theme: Optional[str] = None
    role_keys: Optional[list[str]] = None


    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        """Ensure at least one field is provided for update."""
        # Get all field values, excluding None
        field_values = self.model_dump(exclude_none=True)

        if not field_values:
            raise ValueError("At least one field must be provided for update")

        return self

class SendActionPayload(DataModel):
    """Payload for sending user actions (password reset, email verification)."""
    actions: list
    required: Optional[bool] = False


class SendInvitationPayload(DataModel):
    """Payload for sending organization invitations."""
    email: str
    duration: Optional[int] = Field(default=10)
    message: str | None = None

class AssignRolePayload(DataModel):
    """Payload for assigning roles to profiles."""
    role_key: str = 'VIEWER'
    role_source: Optional[str] = 'SYSTEM'

class RevokeRolePayload(DataModel):
    """Payload for revoking roles from profiles."""
    profile_role_id: UUID_TYPE

class CreateOrgRolePayload(DataModel):
    """Payload for creating custom organization roles."""
    active: Optional[bool] = True
    description: Optional[str]
    name: str
    key: str

class CreateOrgTypePayload(DataModel):
    """Payload for creating organization types."""
    key: str
    display: Optional[str] = None

class RemoveOrgTypePayload(DataModel):
    """Payload for removing organization types."""
    key: str

class RemoveOrgRolePayload(DataModel):
    """Payload for removing organization roles."""
    key: str

class UpdateOrgRolePayload(DataModel):
    """Payload for updating organization roles."""
    role_id: UUID_TYPE
    updates: CreateOrgRolePayload

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
    force: bool = False  # Force sync even if recently synced
    sync_actions: bool = True  # Whether to sync required actions
    user_data: dict = Field(default_factory=dict)  # User data from Keycloak
    required_actions: List[str] = Field(default_factory=list)  # Required actions from Keycloak

class ChangeActionPayload(DataModel):
    action_type: str = Field(..., description="PASSWORD_CHANGE")
