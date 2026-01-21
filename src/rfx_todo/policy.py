from fluvius.casbin import PolicyManager, PolicySchema
from rfx_schema import RFXTodoConnector
from . import config


class RFXTodoPolicy(RFXTodoConnector.__data_schema_base__, PolicySchema):
    __table_args__ = dict(schema=config.RFX_POLICY_SCHEMA)
    __tablename__ = config.POLICY_TABLE


class RFXTodoPolicyManager(PolicyManager):
    __schema__ = RFXTodoPolicy
