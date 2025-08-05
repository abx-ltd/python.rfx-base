from fluvius.casbin import PolicyManager, PolicySchema
from .model import MessageConnector
from . import config

# class MessagePolicy(MessageConnector.__data_schema_base__, PolicySchema):
#     __table_args__ = dict(schema=config.POLICY_SCHEMA)