from fluvius.casbin import PolicyManager, PolicySchema
from rfx_schema.rfx_2dmessage import RFX2DMessageConnector
from . import config


class RFX2DMessagePolicy(RFX2DMessageConnector.__data_schema_base__, PolicySchema):
    __table_args__ = dict(schema=config.POLICY_SCHEMA)
    __tablename__ = config.POLICY_TABLE


class RFX2DMessagePolicyManager(PolicyManager):
    __schema__ = RFX2DMessagePolicy