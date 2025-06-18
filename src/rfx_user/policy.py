from fluvius.casbin import PolicyManager, PolicySchema
from .model import IDMConnector


class UserProfilePolicy(IDMConnector.__data_schema_base__, PolicySchema):
	__table_args__ = dict(schema="rfx--policy")
	__tablename__ = "_policy--user-profile"


class UserProfilePolicyManager(PolicyManager):
	__schema__ = UserProfilePolicy
	# __model__ = "tests/_conf/model.conf"
