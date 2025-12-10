from fluvius.casbin import PolicyManager, PolicySchema
from rfx_schema import RFXPolicyConnector
from . import config
from .model import IDMConnector


class IDMPolicy(IDMConnector.__data_schema_base__, PolicySchema):
	__table_args__ = dict(schema=config.POLICY_SCHEMA)
	__tablename__ = config.POLICY_TABLE


class IDMPolicyManager(PolicyManager):
	__schema__ = IDMPolicy
