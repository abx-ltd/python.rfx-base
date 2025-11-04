from fluvius.casbin import PolicyManager, PolicySchema
from .model import RFXClientConnector
from . import config


class RFXClientPolicy(RFXClientConnector.__data_schema_base__, PolicySchema):
    __table_args__ = dict(schema=config.RFX_POLICY_SCHEMA)
    __tablename__ = config.POLICY_TABLE


class RFXClientPolicyManager(PolicyManager):
    __schema__ = RFXClientPolicy
