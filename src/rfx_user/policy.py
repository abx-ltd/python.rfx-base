from fluvius.casbin import PolicyManager, PolicySchema
from .model import IDMConnector
from . import config


class UserProfilePolicy(IDMConnector.__data_schema_base__, PolicySchema):
	__table_args__ = dict(schema=config.POLICY_SCHEMA)
	__tablename__ = config.POLICY_TABLE


class UserProfilePolicyManager(PolicyManager):
	__schema__ = UserProfilePolicy
