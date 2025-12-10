from fluvius.casbin import PolicyManager, PolicySchema
from rfx_schema.rfx_user._viewmap import PolicyUserProfileView
from . import config


class UserProfilePolicyManager(PolicyManager):
	__schema__ = PolicyUserProfileView
