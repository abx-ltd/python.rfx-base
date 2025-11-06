from fluvius.casbin import PolicyManager, PolicySchema
from .model import RFXDiscussionConnector
from . import config


class RFXDiscussionPolicy(RFXDiscussionConnector.__data_schema_base__, PolicySchema):
    __table_args__ = dict(schema=config.POLICY_SCHEMA)
    __tablename__ = config.POLICY_TABLE


class RFXDiscussionPolicyManager(PolicyManager):
    __schema__ = RFXDiscussionPolicy
