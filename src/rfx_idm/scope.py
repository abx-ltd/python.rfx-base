from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE

class UserScopeSchema(BaseModel):
    user_id: UUID_TYPE = UUIDField("User ID")

class OrganizationScopeSchema(BaseModel):
    organization_id: UUID_TYPE = UUIDField("Organization ID")

class ProfileScopeSchema(BaseModel):
    profile_id: UUID_TYPE = UUIDField("Profile ID")
