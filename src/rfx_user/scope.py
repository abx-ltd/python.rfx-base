from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE

class ProfileRoleScopeSchema(BaseModel):
    profile_id: UUID_TYPE = UUIDField("Profile ID")

class SentInvitationScopeSchema(BaseModel):
    organization_id: UUID_TYPE = UUIDField("Organization ID")

class ProfileListScopeSchema(BaseModel):
    user_id: UUID_TYPE = UUIDField("User ID")

class OrgProfileListScopeSchema(BaseModel):
    organization_id: UUID_TYPE = UUIDField("Organization ID")
