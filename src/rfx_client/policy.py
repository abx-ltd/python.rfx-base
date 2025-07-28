from fluvius.casbin import PolicyManager, PolicySchema
from .model import CPOPortalConnector
from . import config


class CPOPortalPolicy(CPOPortalConnector.__data_schema_base__, PolicySchema):
    __table_args__ = dict(schema=config.POLICY_SCHEMA)
    __tablename__ = config.POLICY_TABLE


class CPOPortalPolicyManager(PolicyManager):
    __schema__ = CPOPortalPolicy