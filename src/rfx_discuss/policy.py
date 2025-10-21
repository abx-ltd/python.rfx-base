from fluvius.casbin import PolicyManager, PolicySchema
from .model import RFXDiscussConnector
from . import config


class RFXDiscussPolicy(RFXDiscussConnector.__data_schema_base__, PolicySchema):
    __table_args__ = dict(schema=config.POLICY_SCHEMA)
    __tablename__ = config.POLICY_TABLE


class RFXDiscussPolicyManager(PolicyManager):
    __schema__ = RFXDiscussPolicy
